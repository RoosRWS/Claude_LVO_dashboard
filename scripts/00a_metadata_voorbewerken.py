"""Stap 00a: zet complete_scenariolist.csv om naar een parquet-bestand met een CID-kolom."""

import sys  # Zoekpad aanpassen
from pathlib import Path  # Padafhandeling

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # Zodat config.py gevonden wordt

import pandas as pd  # Tabeldata

import config as cfg  # Eigen configuratie


def main():
    # Lees de metadata van alle scenario's
    metadata = pd.read_csv(cfg.CSV_METADATA)

    # Voeg de CID toe: begin op basis van overstromingstype + scenarionummer
    metadata["CID"] = metadata["Type overstroming"].map(cfg.CID_BEGIN_PER_TYPE) + metadata["Scenario ID"].astype(str)

    # Waarschuw als een scenario een onbekend overstromingstype heeft (dan is de CID leeg)
    zonder_cid = metadata["CID"].isna().sum()
    if zonder_cid > 0:
        print(f"LET OP: {zonder_cid} scenario's hebben een onbekend overstromingstype, dus geen CID")

    # Waarschuw voor dubbele CID's (hetzelfde scenario staat dan meer dan één keer in de lijst)
    dubbel = metadata["CID"].duplicated().sum()
    if dubbel > 0:
        print(f"LET OP: {dubbel} dubbele CID's (zelfde scenario meerdere keren in de lijst)")

    # Tekstkolommen expliciet als tekst opslaan (anders geeft parquet fouten bij gemengde kolommen)
    tekstkolommen = metadata.select_dtypes(include=["object", "string"]).columns
    metadata[tekstkolommen] = metadata[tekstkolommen].astype("string")

    # Opslaan als parquet
    cfg.METADATA_00A.parent.mkdir(parents=True, exist_ok=True)
    metadata.to_parquet(cfg.METADATA_00A, index=False)
    print(f"{len(metadata)} scenario's, {len(metadata.columns)} kolommen -> {cfg.METADATA_00A}")


if __name__ == "__main__":  # Alleen bij direct starten
    main()  # Uitvoeren
