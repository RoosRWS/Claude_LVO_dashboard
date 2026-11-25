"""Stap 00b: download per scenario de waterdiepte van de WCS en sla de natte cellen op als parquet."""

import re  # Zoeken in tekst
import sys  # Zoekpad en opdrachtregel
from concurrent.futures import ThreadPoolExecutor, as_completed  # Meerdere taken tegelijk uitvoeren
from pathlib import Path  # Padafhandeling

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # Zodat config.py gevonden wordt

import numpy as np  # Rekenen met rasters
import pandas as pd  # Tabeldata
import requests  # Downloaden
from rasterio.io import MemoryFile  # Raster in het geheugen openen

import config as cfg  # Eigen configuratie


def lees_resolutie(cid):
    """Vraag bij de WCS de echte resolutie (pixelgrootte in meters) van het raster van een scenario op, zonder te downloaden."""
    antwoord = requests.get(cfg.WCS_URL, timeout=60, params={
        "service": "WCS", "version": "2.0.1", "request": "DescribeCoverage", "coverageId": cid})
    antwoord.raise_for_status()
    # De eerste offsetVector (bijv. "5.0 0.0") bevat de pixelgrootte in x-richting
    vector = re.search(r"<gml:offsetVector[^>]*>([^<]+)</gml:offsetVector>", antwoord.text).group(1)
    return float(np.hypot(*map(float, vector.split())))


def download_raster(cid, scalefactor=None):
    """Download het raster van één scenario van de WCS en geef de eerste band (waterdiepte) terug."""
    # Vraag het raster op bij de WCS
    vraag = {"service": "WCS", "version": "2.0.1", "request": "GetCoverage",
             "coverageId": cid, "format": "image/tiff"}
    if scalefactor:  # Fijn raster: laat de server het verkleinen naar ongeveer 25 m
        vraag["scalefactor"] = scalefactor
    antwoord = requests.get(cfg.WCS_URL, timeout=300, params=vraag)
    antwoord.raise_for_status()  # Stop met een fout als de download mislukt

    # Lees het raster direct uit het geheugen (geen tijdelijk bestand)
    with MemoryFile(antwoord.content) as geheugenbestand:
        with geheugenbestand.open() as raster:
            diepte = raster.read(1).astype("float32")  # Band 1 = waterdiepte
            return diepte, raster.transform, raster.res[0], raster.nodata


def raster_naar_cellen(diepte, transform, bron_resolutie, nodata):
    """Zet een raster om naar natte cellen op het vaste 25 m-grid (cell_id, wet_pct, max_depth_cm)."""
    # Natte pixels zijn geldig en dieper dan 0
    geldig = np.isfinite(diepte)
    if nodata is not None:
        geldig &= diepte != nodata
    rijen, kolommen = np.nonzero(geldig & (diepte > 0))
    waterdiepte = diepte[rijen, kolommen]

    # Middelpunt van elke natte pixel (c/f = hoek linksboven, a = x-resolutie, e = y-resolutie (negatief))
    x = transform.c + (kolommen + 0.5) * transform.a
    y = transform.f + (rijen + 0.5) * transform.e

    # Pixel groter dan een 25 m-cel? Maak dan van elke natte pixel meerdere punten, één per 25 m-cel erin
    if bron_resolutie > cfg.GRID_CEL:
        aantal = round(bron_resolutie / cfg.GRID_CEL)  # Cellen per zijde, bijv. 100 m -> 4
        afstand = (np.arange(aantal) + 0.5) * cfg.GRID_CEL - bron_resolutie / 2  # Van pixelmidden naar celmiddens
        dx, dy = np.meshgrid(afstand, afstand)  # Alle combinaties (bijv. 4 x 4 = 16)
        x = (x[:, None] + dx.ravel()).ravel()  # Elk puntje van elke pixel
        y = (y[:, None] + dy.ravel()).ravel()
        waterdiepte = np.repeat(waterdiepte, aantal ** 2)  # Elk puntje krijgt de diepte van zijn pixel

    # Celnummer op het vaste grid: rij * aantal kolommen + kolom
    cell_id = ((cfg.GRID_Y0 - y) // cfg.GRID_CEL).astype("int64") * cfg.GRID_KOLOMMEN + ((x - cfg.GRID_X0) // cfg.GRID_CEL).astype("int64")

    # Punten in dezelfde 25 m-cel samenvoegen: aantal natte punten en maximale diepte
    punten = pd.DataFrame({"cell_id": cell_id, "depth": waterdiepte})
    cellen = punten.groupby("cell_id").agg(n_wet=("depth", "size"), max_depth=("depth", "max")).reset_index()

    # Percentage nat: natte punten gedeeld door het aantal punten dat een volle cel zou hebben
    pixels_per_cel = max(1.0, (cfg.GRID_CEL / bron_resolutie) ** 2)
    cellen["wet_pct"] = np.minimum(100, cellen.n_wet / pixels_per_cel * 100).round().astype("uint8")
    cellen["max_depth_cm"] = (cellen.max_depth * 100).clip(0, 65535).astype("uint16")
    cellen["cell_id"] = cellen.cell_id.astype("int32")

    # Alleen cellen die voor meer dan MIN_NAT_PCT nat zijn
    cellen = cellen[cellen["wet_pct"] > cfg.MIN_NAT_PCT]
    return cellen[["cell_id", "wet_pct", "max_depth_cm"]].sort_values("cell_id")


def verwerk_scenario(cid):
    """Download één scenario, zet het om naar natte cellen en sla het op; geeft een melding terug (leeg als het al bestond)."""
    bestand = cfg.DIEPTE_MAP / f"{cid}.parquet"  # Waar de natte cellen van dit scenario komen
    if bestand.exists():  # Al gedownload: overslaan
        return None
    try:  # Eén mislukte download mag de rest niet stoppen
        # Stap 1: vraag de echte resolutie op; is het raster fijner dan 25 m, laat de server het dan verkleinen
        resolutie = lees_resolutie(cid)
        scalefactor = resolutie / cfg.GRID_CEL if resolutie < min(cfg.VERKLEIN_ALS_FIJNER_DAN, cfg.GRID_CEL) else None
        # Stap 2: download het raster van dit scenario
        diepte, transform, bron_resolutie, nodata = download_raster(cid, scalefactor)
        # Stap 3: zet het raster om naar natte cellen op het 25 m-grid
        cellen = raster_naar_cellen(diepte, transform, bron_resolutie, nodata)
        # Stap 4: sla op onder een tijdelijke naam en hernoem daarna (zo blijft er nooit een half bestand staan)
        tijdelijk = bestand.with_suffix(".tmp")
        cellen.to_parquet(tijdelijk, compression="zstd", index=False)
        tijdelijk.replace(bestand)
        return f"{cid}: {len(cellen)} natte cellen"
    except Exception as fout:
        return f"{cid}: MISLUKT ({fout})"


def main():
    # Lees de metadata uit stap 00a: elke CID één keer (er staan dubbele scenario's in)
    metadata = pd.read_parquet(cfg.METADATA_00A).dropna(subset=[cfg.KOL_CID]).drop_duplicates(cfg.KOL_CID)

    # Optioneel: alleen de eerste N scenario's (om te testen), bijv. "python 00b_download_overstroming.py 3"
    if len(sys.argv) > 1:
        metadata = metadata.head(int(sys.argv[1]))

    cfg.DIEPTE_MAP.mkdir(parents=True, exist_ok=True)  # Uitvoermap aanmaken

    # Alle scenario's door een groep threads laten verwerken; melding zodra een scenario klaar is
    with ThreadPoolExecutor(max_workers=cfg.AANTAL_PARALLEL) as uitvoerder:
        taken = [uitvoerder.submit(verwerk_scenario, cid) for cid in metadata[cfg.KOL_CID]]
        for nummer, taak in enumerate(as_completed(taken), start=1):
            melding = taak.result()
            if melding:
                print(f"{nummer}/{len(taken)} {melding}")


if __name__ == "__main__":  # Alleen bij direct starten
    main()  # Uitvoeren
