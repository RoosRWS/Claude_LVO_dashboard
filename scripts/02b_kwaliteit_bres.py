"""Stap 02b: bepaal per breslocatie de kwaliteit: spreiding van de herhalingstijd en een samenvatting van de KI's van de scenario's."""

import sys  # Zoekpad aanpassen
from pathlib import Path  # Padafhandeling

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # Zodat config.py gevonden wordt

import geopandas as gpd  # Geodata
import numpy as np  # Rekenen
import pandas as pd  # Tabeldata

import config as cfg  # Eigen configuratie


def factor_herhalingstijd(frequenties):
    """Hoogste herhalingstijd gedeeld door de laagste; leeg als er geen geldige waarde is of maar één herhalingstijd."""
    geldig = frequenties[frequenties > 0]  # Lege en ongeldige waarden tellen niet mee
    if len(geldig) == 0:
        return np.nan
    factor = geldig.max() / geldig.min()
    return factor if factor > 1 else np.nan  # Factor 1 betekent: geen spreiding te bepalen


def geef_klasse_hoog(waarde, grenzen):
    """Klasse op basis van twee grenzen: hoe hoger de waarde, hoe beter (3 = goed, 2 = gemiddeld, 1 = matig, 0 = onbekend)."""
    if pd.isna(waarde):  # Geen waarde bekend
        return 0
    if waarde >= grenzen.grens1:  # Op of boven de hoogste grens
        return 3
    if waarde >= grenzen.grens2:  # Tussen de twee grenzen
        return 2
    return 1


def vat_scenarios_samen(scenarios):
    """Per breslocatie: aantal scenario's, spreiding van de herhalingstijd en de KI's (laagste, gemiddelde, hoogste)."""
    groep = scenarios.groupby(cfg.KOL_BRES_ID)
    samenvatting = pd.DataFrame({
        cfg.KOL_N_SCENARIOS: groep[cfg.KOL_CID].nunique(),
        cfg.KOL_FACTOR: groep[cfg.KOL_FREQUENTIE].apply(factor_herhalingstijd),
    })

    # Per KI de laagste, gemiddelde en hoogste score; onbekend (0) telt niet mee
    for kolom in [cfg.KOL_KI_LEEFTIJD, cfg.KOL_KI_SOFTWARE]:
        bekend = scenarios[kolom].where(scenarios[kolom] > 0)
        per_bres = bekend.groupby(scenarios[cfg.KOL_BRES_ID]).agg(["min", "mean", "max"])
        for statistiek in ["min", "mean", "max"]:
            samenvatting[f"{kolom}_{statistiek}"] = per_bres[statistiek]
    return samenvatting


def main():
    # Lees de scenario's met hun breslocatie (stap 02a): elke CID één keer, alleen gekoppelde scenario's
    scenarios = pd.read_parquet(cfg.METADATA_02A).drop_duplicates(cfg.KOL_CID).dropna(subset=[cfg.KOL_BRES_ID])

    # Lees de breslocaties van LIWO en geef ze dezelfde ID als in stap 02a
    breslocaties = gpd.read_parquet(cfg.BRESLOCATIES_PARQUET)
    breslocaties[cfg.KOL_BRES_ID] = breslocaties[cfg.KOL_TYPE] + "_" + breslocaties["id"].astype(str)

    # Samenvatting per breslocatie en KI voor de spreiding van de herhalingstijd (grenzen uit Grenzen_3.csv)
    grenzen = pd.read_csv(cfg.CSV_GRENZEN, sep=";", index_col=0)
    samenvatting = vat_scenarios_samen(scenarios)
    samenvatting[cfg.KOL_KI_FREQUENTIE] = samenvatting[cfg.KOL_FACTOR].apply(geef_klasse_hoog, grenzen=grenzen.loc["Frequentie"])

    # Alle breslocaties blijven staan, ook zonder scenario's (die krijgen 0 scenario's en onbekende KI's)
    resultaat = breslocaties[[cfg.KOL_BRES_ID, cfg.KOL_TYPE, "name", "geometry"]].merge(
        samenvatting, left_on=cfg.KOL_BRES_ID, right_index=True, how="left")
    resultaat[cfg.KOL_N_SCENARIOS] = resultaat[cfg.KOL_N_SCENARIOS].fillna(0).astype(int)
    resultaat[cfg.KOL_KI_FREQUENTIE] = resultaat[cfg.KOL_KI_FREQUENTIE].fillna(0).astype(int)

    # Opslaan als gpkg
    resultaat.to_file(cfg.KWALITEIT_BRES_GPKG, driver="GPKG")

    # Samenvatting
    print(f"{len(resultaat)} breslocaties, waarvan {(resultaat[cfg.KOL_N_SCENARIOS] == 0).sum()} zonder scenario's -> {cfg.KWALITEIT_BRES_GPKG}")
    print(f"  {cfg.KOL_KI_FREQUENTIE}: {resultaat[cfg.KOL_KI_FREQUENTIE].value_counts().sort_index().to_dict()}")


if __name__ == "__main__":  # Alleen bij direct starten
    main()  # Uitvoeren
