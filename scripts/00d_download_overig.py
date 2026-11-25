"""Stap 00d: download trajecten, keringen en breslocaties van LIWO en sla ze op (gpkg en parquet)."""

import io  # Download in het geheugen lezen
import sys  # Zoekpad aanpassen
from pathlib import Path  # Padafhandeling

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # Zodat config.py gevonden wordt

import geopandas as gpd  # Geodata
import pandas as pd  # Tabeldata
import requests  # Downloaden
import shapely  # Vormen bewerken

import config as cfg  # Eigen configuratie


def download_laag(laag):
    """Haal één kaartlaag op bij de WFS-server van LIWO (in RD, zonder hoogte)."""
    # Vraag de laag op als GeoJSON, in Rijksdriehoekscoördinaten
    antwoord = requests.get(cfg.WFS_BASIS, timeout=300, params={
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "typeNames": laag, "outputFormat": "application/json", "srsName": "EPSG:28992"})
    antwoord.raise_for_status()
    gdf = gpd.read_file(io.BytesIO(antwoord.content))
    gdf["geometry"] = shapely.force_2d(gdf.geometry.values)  # Alleen x en y (geen hoogte)
    return gdf.set_crs(cfg.CRS_RD, allow_override=True)


def download_kansen():
    """Download de lagen met overstromingskansen (trajecten en keringen) en sla ze op als gpkg."""
    for laag, bestand in cfg.WFS_KANSEN.items():
        try:
            gdf = download_laag(laag)
        except Exception as fout:
            if bestand.exists():
                print(f"WAARSCHUWING: {laag} niet gedownload ({fout}); het oude bestand blijft in gebruik")
                continue
            sys.exit(f"FOUT: {laag} niet gedownload ({fout}) en er is geen oud bestand")
        # Kolomnamen in HOOFDLETTERS en extra kolom 'id' weg (zoals in het oude script)
        gdf = gdf.drop(columns="id", errors="ignore")
        gdf.columns = [c if c == "geometry" else c.upper() for c in gdf.columns]
        gdf.to_file(bestand, driver="GPKG")
        print(f"{bestand.name}: {len(gdf)} lijnen")


def download_breslocaties():
    """Download de breslocaties (vijf lagen), voeg het overstromingstype toe en sla ze samen op als gpkg."""
    lagen = []
    for laag, type_overstroming in cfg.WFS_BRESLOCATIES.items():
        gdf = download_laag(laag)
        gdf["Type overstroming"] = type_overstroming  # A, B, C, D of BRS
        lagen.append(gdf)
        print(f"{laag}: {len(gdf)} breslocaties")
    breslocaties = gpd.GeoDataFrame(pd.concat(lagen, ignore_index=True), crs=cfg.CRS_RD)
    breslocaties.to_file(cfg.BRESLOCATIES_GPKG, driver="GPKG")
    return breslocaties


def maak_trajecten():
    """Lees de primaire trajecten (2019-laag van LIWO) en geef de kolommen duidelijke namen, in RD."""
    t = gpd.read_file(cfg.KANSEN_PRIMAIR_2019)
    return gpd.GeoDataFrame({
        "traject_id": t["TRAJECT_ID"], "omschrijving": t["DUIDING"],
        "klasse": t["KLASSE"], "kans": t["KANS"],
    }, geometry=t.geometry, crs=cfg.CRS_RD)


def maak_keringen():
    """Bereid de niet-primaire keringen voor: alleen de kolommen die later gebruikt worden, in RD."""
    k = gpd.read_file(cfg.KANSEN_NIET_PRIMAIR)
    return gpd.GeoDataFrame({
        "kering_id": ["KNP_" + str(i) for i in range(len(k))],  # Eigen ID: het bronbestand heeft er geen
        "naam": k["NAAM"], "beheerder": k["BEHEERDER"], "provincie": k["PROVINCIE"],
        "type": k["TYPE"], "soort": k["SOORT"], "normfrequentie": k["NORMFREQ"],
    }, geometry=k.geometry, crs=k.crs)


def main():
    # Stap 1: download alles van LIWO
    download_kansen()
    breslocaties = download_breslocaties()

    # Stap 2: bereid trajecten en keringen voor en sla alles op als parquet
    cfg.OVERIG_MAP.mkdir(parents=True, exist_ok=True)
    trajecten = maak_trajecten()
    trajecten.to_parquet(cfg.OVERIG_MAP / "trajecten_primair.parquet", index=False)
    print(f"trajecten_primair: {len(trajecten)} lijnen")

    keringen = maak_keringen()
    keringen.to_parquet(cfg.OVERIG_MAP / "keringen_niet_primair.parquet", index=False)
    print(f"keringen_niet_primair: {len(keringen)} lijnen")

    breslocaties.to_parquet(cfg.OVERIG_MAP / "breslocaties.parquet", index=False)
    print(f"breslocaties: {len(breslocaties)} punten")


if __name__ == "__main__":  # Alleen bij direct starten
    main()  # Uitvoeren
