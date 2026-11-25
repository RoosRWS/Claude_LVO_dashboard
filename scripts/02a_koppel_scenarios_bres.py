"""Stap 02a: koppel elk scenario aan de breslocatie (van LIWO) waar het scenario op ligt."""

import sys  # Zoekpad aanpassen
from pathlib import Path  # Padafhandeling

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # Zodat config.py gevonden wordt

import geopandas as gpd  # Geodata
import pandas as pd  # Tabeldata

import config as cfg  # Eigen configuratie


def koppel_op_coordinaten(scenarios, breslocaties):
    """Koppel elk scenario aan de dichtstbijzijnde breslocatie van hetzelfde type, binnen KOPPEL_AFSTAND_BRES_M meter."""
    # Punten maken van de coördinaten van de scenario's (RD)
    punten = gpd.GeoDataFrame(scenarios[[cfg.KOL_CID, cfg.KOL_TYPE]], crs=cfg.CRS_RD,
                              geometry=gpd.points_from_xy(scenarios[cfg.KOL_X], scenarios[cfg.KOL_Y]))

    # Per overstromingstype zoeken, zodat een scenario alleen bij een breslocatie van zijn eigen type hoort
    gekoppeld = []
    for type_overstroming, groep in punten.groupby(cfg.KOL_TYPE):
        bres_van_type = breslocaties[breslocaties[cfg.KOL_TYPE] == type_overstroming][[cfg.KOL_BRES_ID, "geometry"]]
        gekoppeld.append(gpd.sjoin_nearest(groep, bres_van_type, how="left",
                                           max_distance=cfg.KOPPEL_AFSTAND_BRES_M, distance_col=cfg.KOL_BRES_AFSTAND))
    gekoppeld = pd.concat(gekoppeld).drop_duplicates(cfg.KOL_CID)  # Bij gelijke afstand: de eerste

    # Noteer hoe gekoppeld is (alleen waar een breslocatie gevonden is)
    gekoppeld[cfg.KOL_BRES_KOPPELING] = gekoppeld[cfg.KOL_BRES_ID].notna().map({True: "coördinaten", False: None})
    return gekoppeld[[cfg.KOL_CID, cfg.KOL_BRES_ID, cfg.KOL_BRES_AFSTAND, cfg.KOL_BRES_KOPPELING]]


def koppel_op_naam(scenarios, breslocaties):
    """Koppel scenario's via type + naam van de doorbraaklocatie, alleen als die naam bij dat type maar één keer voorkomt."""
    # Namen vergelijkbaar maken: kleine letters en zonder spaties eromheen
    bres = breslocaties[[cfg.KOL_BRES_ID, cfg.KOL_TYPE, "name"]].dropna(subset=["name"]).copy()
    bres["sleutel"] = bres["name"].str.strip().str.lower()
    bres = bres[~bres.duplicated([cfg.KOL_TYPE, "sleutel"], keep=False)]  # Alleen namen die bij één breslocatie horen

    scenarios = scenarios[[cfg.KOL_CID, cfg.KOL_TYPE, cfg.KOL_NAAM_BRES]].dropna(subset=[cfg.KOL_NAAM_BRES]).copy()
    scenarios["sleutel"] = scenarios[cfg.KOL_NAAM_BRES].str.strip().str.lower()
    return scenarios.merge(bres[[cfg.KOL_BRES_ID, cfg.KOL_TYPE, "sleutel"]], on=[cfg.KOL_TYPE, "sleutel"])[[cfg.KOL_CID, cfg.KOL_BRES_ID]]


def main():
    # Lees de metadata van stap 01c (met de KI's) en de breslocaties van LIWO (stap 00d)
    metadata = pd.read_parquet(cfg.METADATA_KWALITEIT)
    breslocaties = gpd.read_parquet(cfg.BRESLOCATIES_PARQUET)

    # Geef elke breslocatie een unieke ID: type + id van LIWO (het id alleen is niet uniek tussen de types)
    breslocaties[cfg.KOL_BRES_ID] = breslocaties[cfg.KOL_TYPE] + "_" + breslocaties["id"].astype(str)

    # Stap 1: koppel elke unieke CID op coördinaten
    unieke = metadata.drop_duplicates(cfg.KOL_CID)
    koppeling = koppel_op_coordinaten(unieke, breslocaties)

    # Stap 2: scenario's zonder koppeling proberen we nog via type + naam
    zonder = koppeling.loc[koppeling[cfg.KOL_BRES_ID].isna(), cfg.KOL_CID]
    op_naam = koppel_op_naam(unieke[unieke[cfg.KOL_CID].isin(zonder)], breslocaties)
    bres_per_cid = dict(zip(op_naam[cfg.KOL_CID], op_naam[cfg.KOL_BRES_ID]))
    via_naam = koppeling[cfg.KOL_CID].isin(bres_per_cid) & koppeling[cfg.KOL_BRES_ID].isna()
    koppeling.loc[via_naam, cfg.KOL_BRES_ID] = koppeling.loc[via_naam, cfg.KOL_CID].map(bres_per_cid)
    koppeling.loc[via_naam, cfg.KOL_BRES_KOPPELING] = "naam"

    # Voeg de koppeling toe aan alle rijen van de metadata en sla op
    aantal_rijen = len(metadata)
    metadata = metadata.merge(koppeling, on=cfg.KOL_CID, how="left")
    assert len(metadata) == aantal_rijen, "het aantal rijen is veranderd door het samenvoegen"
    metadata.to_parquet(cfg.METADATA_02A, index=False)

    # Samenvatting
    unieke = metadata.drop_duplicates(cfg.KOL_CID)
    print(f"gekoppeld: {unieke[cfg.KOL_BRES_KOPPELING].value_counts().to_dict()} | zonder breslocatie: {unieke[cfg.KOL_BRES_ID].isna().sum()} van {len(unieke)}")
    print(f"{unieke[cfg.KOL_BRES_ID].nunique()} van {len(breslocaties)} breslocaties hebben minstens één scenario -> {cfg.METADATA_02A}")


if __name__ == "__main__":  # Alleen bij direct starten
    main()  # Uitvoeren
