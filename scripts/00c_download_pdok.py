"""Stap 00c: haal water (meer/plas, zee en waterlopen van 50 m of breder) op uit PDOK en zet het op het 25 m-grid."""

import sys  # Zoekpad en opdrachtregel
from pathlib import Path  # Padafhandeling

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # Zodat config.py gevonden wordt

import numpy as np  # Rekenen met rasters
import pandas as pd  # Tabeldata
import requests  # Downloaden
from affine import Affine  # Plaats van het raster
from rasterio.features import rasterize  # Polygonen omzetten naar een raster
from shapely.geometry import shape  # GeoJSON omzetten naar een vorm

import config as cfg  # Eigen configuratie

RD = "http://www.opengis.net/def/crs/EPSG/0/28992"  # Coördinatenstelsel (RD New) voor PDOK
BLOKKEN_PER_CEL = cfg.GRID_CEL // cfg.WATER_BLOK  # 5 blokjes breed (en 5 hoog) per 25 m-cel


def is_gewenst_water(eigenschappen):
    """Meer/plas en zee altijd; van de waterlopen alleen de brede (50 m of breder)."""
    if eigenschappen["typewater"] in cfg.WATER_TYPEN:  # Meer, plas of zee
        return True
    return eigenschappen["typewater"] == "waterloop" and eigenschappen["breedteklasse"] in cfg.RIVIER_BREEDTES  # Brede waterloop


def haal_waterpolygonen(xmin, ymin, xmax, ymax):
    """Vraag PDOK om alle waterpolygonen in het gebied (in pagina's van 1000)."""
    vragen = {"f": "json", "limit": 1000, "bbox": f"{xmin},{ymin},{xmax},{ymax}", "bbox-crs": RD, "crs": RD}
    url, polygonen = cfg.PDOK_WATER_URL, []
    while url:
        antwoord = requests.get(url, params=vragen if url == cfg.PDOK_WATER_URL else None, timeout=120)
        antwoord.raise_for_status()
        data = antwoord.json()
        # Bewaar alleen de vorm van de gewenste watertypes
        polygonen += [shape(w["geometry"]) for w in data["features"] if is_gewenst_water(w["properties"])]
        # Link naar de volgende pagina (is leeg na de laatste pagina)
        url = next((l["href"] for l in data["links"] if l["rel"] == "next"), None)
    return polygonen


def polygonen_naar_cellen(polygonen, xmin, ymin, xmax, ymax):
    """Zet waterpolygonen om naar 25 m-cellen met het percentage water per cel (cell_id, wet_pct)."""
    # Rond het gebied af naar hele 25 m-cellen
    kolom_start = int(np.floor((xmin - cfg.GRID_X0) / cfg.GRID_CEL))
    kolom_eind = int(np.ceil((xmax - cfg.GRID_X0) / cfg.GRID_CEL))
    rij_start = int(np.floor((cfg.GRID_Y0 - ymax) / cfg.GRID_CEL))
    rij_eind = int(np.ceil((cfg.GRID_Y0 - ymin) / cfg.GRID_CEL))
    aantal_kolommen, aantal_rijen = kolom_eind - kolom_start, rij_eind - rij_start

    # Teken het water op 5 m-blokjes: 1 = water, 0 = geen water
    links = cfg.GRID_X0 + kolom_start * cfg.GRID_CEL
    boven = cfg.GRID_Y0 - rij_start * cfg.GRID_CEL
    blokjes = rasterize(((p, 1) for p in polygonen),
                        out_shape=(aantal_rijen * BLOKKEN_PER_CEL, aantal_kolommen * BLOKKEN_PER_CEL),
                        transform=Affine(cfg.WATER_BLOK, 0, links, 0, -cfg.WATER_BLOK, boven), fill=0, dtype="uint8")

    # Tel per 25 m-cel de natte blokjes (elke cel bestaat uit 5 x 5 blokjes)
    per_cel = blokjes.reshape(aantal_rijen, BLOKKEN_PER_CEL, aantal_kolommen, BLOKKEN_PER_CEL)
    water_pct = per_cel.sum(axis=(1, 3)) / BLOKKEN_PER_CEL ** 2 * 100

    # Bewaar alle cellen met water (dus meer dan 0%); stap 01b bepaalt later hoeveel % nodig is
    rij, kolom = np.nonzero(water_pct > 0)
    cel_nummer = (rij_start + rij) * cfg.GRID_KOLOMMEN + (kolom_start + kolom)
    return pd.DataFrame({"cell_id": cel_nummer.astype("int32"),
                         "wet_pct": water_pct[rij, kolom].round().astype("uint8")})


def maak_tegels(gebied):
    """Knip het gebied in tegels die precies op het 25 m-grid aansluiten."""
    xmin, ymin, xmax, ymax = gebied
    x_start = cfg.GRID_X0 + np.floor((xmin - cfg.GRID_X0) / cfg.WATER_TEGEL) * cfg.WATER_TEGEL
    y_start = cfg.GRID_Y0 - np.ceil((cfg.GRID_Y0 - ymin) / cfg.WATER_TEGEL) * cfg.WATER_TEGEL
    return [(x, y, x + cfg.WATER_TEGEL, y + cfg.WATER_TEGEL)
            for x in np.arange(x_start, xmax, cfg.WATER_TEGEL)
            for y in np.arange(y_start, ymax, cfg.WATER_TEGEL)]


def main():
    # Met "test" erachter ("python 00c_download_pdok.py test") alleen het kleine testgebied
    test = "test" in sys.argv
    tegels = maak_tegels(cfg.TESTGEBIED if test else cfg.NL_GRENZEN)

    cellen_per_tegel = []  # Resultaat per tegel
    for nummer, tegel in enumerate(tegels, start=1):
        polygonen = haal_waterpolygonen(*tegel)  # Waterpolygonen in deze tegel
        if polygonen:  # Lege tegels (bijv. geen water) overslaan
            cellen_per_tegel.append(polygonen_naar_cellen(polygonen, *tegel))
        print(f"tegel {nummer}/{len(tegels)}: {len(polygonen)} waterpolygonen")

    # Alle tegels samenvoegen en opslaan
    water = pd.concat(cellen_per_tegel).sort_values("cell_id")
    cfg.WATER_MAP.mkdir(parents=True, exist_ok=True)
    bestand = cfg.WATER_MAP / ("waterwegen_pdok_test.parquet" if test else "waterwegen_pdok.parquet")
    water.to_parquet(bestand, compression="zstd", index=False)
    print(f"{len(water)} cellen met water -> {bestand}")


if __name__ == "__main__":  # Alleen bij direct starten
    main()  # Uitvoeren
