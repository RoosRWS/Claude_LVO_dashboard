"""Stap 01c: bepaal per scenario de kwaliteitsindicatoren (KI's) voor leeftijd en software."""

import sys  # Zoekpad aanpassen
from datetime import date, datetime  # Datums
from pathlib import Path  # Padafhandeling

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # Zodat config.py gevonden wordt

import numpy as np  # Rekenen
import pandas as pd  # Tabeldata

import config as cfg  # Eigen configuratie

vandaag = date.today()  # Peildatum voor de leeftijd (let op: de uitkomst hangt af van de dag waarop je draait)


def bepaal_leeftijd(scenario_datum):
    """Bepaalt hoe oud het scenario is in hele jaren; leeg als de datum onbekend of ongeldig is."""
    scenario_datum = str(scenario_datum)  # Altijd als tekst behandelen

    try:  # Eerst ISO-formaat proberen (2019-06-06)
        datum = datetime.fromisoformat(scenario_datum).date()
    except ValueError:  # Geen ISO-formaat: dan dag-maand-jaar proberen
        try:
            dag, maand, jaar = map(int, scenario_datum.split("-"))
            datum = date(jaar, maand, dag)
        except ValueError:  # Ook dat lukt niet
            return np.nan

    return int((vandaag - datum).days / 365)  # Aantal dagen omrekenen naar hele jaren


def geef_klasse(waarde, grenzen):
    """Klasse op basis van twee grenzen: hoe lager de waarde, hoe beter (3 = goed, 2 = gemiddeld, 1 = matig, 0 = onbekend)."""
    if pd.isna(waarde):  # Geen waarde bekend
        return 0
    if waarde > grenzen.grens2:  # Boven de hoogste grens
        return 1
    if waarde > grenzen.grens1:  # Tussen de twee grenzen
        return 2
    return 3  # Op of onder de laagste grens


def geef_klasse_berekeningsmethode(methode):
    """Klasse voor de berekeningsmethode (3 = goed, 2 = gemiddeld, 1 = matig, 0 = onbekend)."""
    if methode == "2d model":
        return 3
    if methode in ("bakjesmodel", "integraal model", "koppelingsmodel"):
        return 2
    if methode == "waterstand gelijk aan waterstand systeem":
        return 1
    return 0  # Onbekend


def main():
    # Lees de metadata van stap 01a (met de overlap) en de klassegrenzen
    metadata = pd.read_parquet(cfg.METADATA_01A)
    grenzen = pd.read_csv(cfg.CSV_GRENZEN, sep=";", index_col=0)

    # KI leeftijd: bepaal de leeftijd en deel in op de grenzen uit Grenzen_3.csv
    metadata[cfg.KOL_LEEFTIJD] = metadata[cfg.KOL_DATUM].apply(bepaal_leeftijd)
    metadata[cfg.KOL_KI_LEEFTIJD] = metadata[cfg.KOL_LEEFTIJD].apply(geef_klasse, grenzen=grenzen.loc["Leeftijd"])

    # KI software: klasse op basis van de berekeningsmethode
    metadata[cfg.KOL_KI_SOFTWARE] = metadata[cfg.KOL_METHODE].apply(geef_klasse_berekeningsmethode)

    # Opslaan als parquet
    metadata.to_parquet(cfg.METADATA_KWALITEIT, index=False)

    # Samenvatting: verdeling van de klassen
    print(f"{len(metadata)} scenario's -> {cfg.METADATA_KWALITEIT}")
    for kolom in [cfg.KOL_KI_LEEFTIJD, cfg.KOL_KI_SOFTWARE]:
        print(f"  {kolom}: {metadata[kolom].value_counts().sort_index().to_dict()}")


if __name__ == "__main__":  # Alleen bij direct starten
    main()  # Uitvoeren
