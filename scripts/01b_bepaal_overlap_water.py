"""Stap 01b: bepaal per scenario welk deel van de natte cellen water is (rivieren, meren, zee)."""

import sys  # Zoekpad en opdrachtregel
from pathlib import Path  # Padafhandeling

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # Zodat config.py gevonden wordt

import numpy as np  # Rekenen
import pandas as pd  # Tabeldata

import config as cfg  # Eigen configuratie


def lees_watercellen():
    """Lees de watercellen uit stap 00c; alleen cellen die (vrijwel) helemaal water zijn tellen mee."""
    bestand = cfg.WATER_MAP / "waterwegen_pdok.parquet"
    if not bestand.exists():  # Stap 00c voor heel Nederland is nog niet gedraaid
        sys.exit(f"FOUT: {bestand} bestaat niet; draai eerst stap 00c (zonder 'test')")
    water = pd.read_parquet(bestand)
    return water.loc[water["wet_pct"] >= cfg.WATER_MIN_PCT, "cell_id"].to_numpy()


def bepaal_water_overlap(cid, watercellen):
    """Percentage van de natte cellen van een scenario dat ook water is."""
    # Natte cellen van het scenario (uit stap 00b), met hun percentage nat
    cellen = pd.read_parquet(cfg.DIEPTE_MAP / f"{cid}.parquet", columns=["cell_id", "wet_pct"])
    if len(cellen) == 0:  # Een scenario zonder natte cellen: niets te berekenen
        return np.nan

    # Alleen cellen die helemaal overstroomd zijn tellen mee als overlap
    volledig_nat = cellen.loc[cellen["wet_pct"] >= cfg.NAT_MIN_PCT, "cell_id"].to_numpy()

    # Cellen die ook water zijn (zelfde celnummer = zelfde plek), gedeeld door alle natte cellen
    gedeeld = np.intersect1d(volledig_nat, watercellen, assume_unique=True)
    return len(gedeeld) / len(cellen) * 100


def main():
    # Lees de metadata van stap 01a; alle rijen en kolommen blijven behouden
    if not cfg.METADATA_01A.exists():  # Stap 01a moet eerst gedraaid zijn
        sys.exit(f"FOUT: {cfg.METADATA_01A} bestaat niet; draai eerst stap 01a")
    metadata = pd.read_parquet(cfg.METADATA_01A)

    # Alleen scenario's waarvan de natte cellen zijn gedownload (stap 00b); elke CID één keer
    unieke_cids = metadata[cfg.KOL_CID].drop_duplicates()
    unieke_cids = unieke_cids[unieke_cids.apply(lambda cid: (cfg.DIEPTE_MAP / f"{cid}.parquet").exists())]

    # Optioneel: alleen de eerste N scenario's (om te testen), bijv. "python 01b_bepaal_overlap_water.py 10"
    if len(sys.argv) > 1:
        unieke_cids = unieke_cids.head(int(sys.argv[1]))

    # Per scenario de overlap met water
    watercellen = lees_watercellen()
    water_overlap = {cid: bepaal_water_overlap(cid, watercellen) for cid in unieke_cids}

    # Voeg de overlap als nieuwe kolom toe (scenario's zonder resultaat blijven leeg) en sla op
    metadata[cfg.KOL_WATER_OVERLAP] = metadata[cfg.KOL_CID].map(water_overlap)
    metadata.to_parquet(cfg.METADATA_01A, index=False)
    print(f"{len(water_overlap)} scenario's met water-overlap -> {cfg.METADATA_01A}")


if __name__ == "__main__":  # Alleen bij direct starten
    main()  # Uitvoeren
