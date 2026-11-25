"""Stap 01a: bepaal per scenario het scenario met de meeste overlap, en het verschil in schade en slachtoffers."""

import sys  # Zoekpad en opdrachtregel
from pathlib import Path  # Padafhandeling

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # Zodat config.py gevonden wordt

import numpy as np  # Rekenen
import pandas as pd  # Tabeldata

import config as cfg  # Eigen configuratie


def vind_dichtstbijzijnde_scenarios(kandidaten, scenario_id, n=cfg.AANTAL_BUREN):
    """Geef de n dichtstbijzijnde scenario's met dezelfde herhalingstijd en hetzelfde type overstroming."""
    # Het scenario waarvoor we zoeken
    scenario = kandidaten[kandidaten[cfg.KOL_ID] == scenario_id].iloc[0]

    # Alle andere scenario's met dezelfde frequentie en hetzelfde type
    overige = kandidaten[(kandidaten[cfg.KOL_ID] != scenario_id)
                         & (kandidaten[cfg.KOL_FREQUENTIE] == scenario[cfg.KOL_FREQUENTIE])
                         & (kandidaten[cfg.KOL_TYPE] == scenario[cfg.KOL_TYPE])].copy()

    # Afstand tot het scenario (in meters, RD-coördinaten) en de n dichtstbijzijnde kiezen
    overige["afstand"] = np.hypot(overige[cfg.KOL_X] - scenario[cfg.KOL_X], overige[cfg.KOL_Y] - scenario[cfg.KOL_Y])
    return overige.nsmallest(n, "afstand")[cfg.KOL_ID].tolist()


def lees_cellen(cid):
    """Lees de natte cellen van een scenario (uit stap 00b); alleen de celnummers zijn nodig."""
    bestand = cfg.DIEPTE_MAP / f"{cid}.parquet"
    return pd.read_parquet(bestand, columns=["cell_id"])["cell_id"].to_numpy()


def bepaal_overlap(cellen1, cellen2):
    """Overlap in procenten: aantal gedeelde cellen gedeeld door het aantal cellen van het grootste scenario."""
    # Het grootste scenario bepaalt het totaal (zoals in het oude script)
    totaal_cellen = max(len(cellen1), len(cellen2))
    if totaal_cellen == 0:  # Een scenario zonder natte cellen: geen overlap te berekenen
        return np.nan

    # Cellen die in beide scenario's voorkomen (zelfde celnummer = zelfde plek)
    gedeelde_cellen = np.intersect1d(cellen1, cellen2, assume_unique=True)
    return len(gedeelde_cellen) / totaal_cellen * 100


def vind_meeste_overlap(kandidaten, scenario_id, cid_per_id):
    """Vergelijk een scenario met zijn dichtstbijzijnde buren; geef het buur-scenario met de meeste overlap en die overlap."""
    # Natte cellen van het scenario zelf
    cellen = lees_cellen(cid_per_id[scenario_id])

    max_overlap, max_scenario = np.nan, None  # Nog niets gevonden
    for buur_id in vind_dichtstbijzijnde_scenarios(kandidaten, scenario_id):
        # Overlap met deze buur
        overlap = bepaal_overlap(cellen, lees_cellen(cid_per_id[buur_id]))
        # Onthoud de buur met de hoogste overlap
        if not np.isnan(overlap) and (max_scenario is None or overlap > max_overlap):
            max_overlap, max_scenario = overlap, buur_id
    return max_scenario, max_overlap


def bepaal_verschil(waarde, waarde_buur):
    """Verschil in procenten van de buur ten opzichte van het scenario (voor schade of slachtoffers)."""
    # Ontbrekende waarden: geen verschil te berekenen
    if pd.isna(waarde) or pd.isna(waarde_buur):
        return np.nan
    # Delen door 0 kan niet: twee keer 0 is geen verschil, anders is het verschil niet te geven
    if waarde == 0:
        return 0.0 if waarde_buur == 0 else np.nan
    return (waarde_buur - waarde) / waarde * 100


def main():
    # Lees de metadata van stap 00a; alle rijen blijven behouden (ook de dubbele)
    metadata = pd.read_parquet(cfg.METADATA_00A)

    # Voor de berekening elke CID één keer (zo worden dubbele scenario's niet dubbel vergeleken)
    unieke_scenarios = metadata.drop_duplicates(cfg.KOL_CID)

    # Alleen scenario's waarvan de natte cellen zijn gedownload (stap 00b) doen mee
    heeft_cellen = unieke_scenarios[cfg.KOL_CID].apply(lambda cid: (cfg.DIEPTE_MAP / f"{cid}.parquet").exists())
    kandidaten = unieke_scenarios[heeft_cellen]
    print(f"{len(kandidaten)} van {len(unieke_scenarios)} unieke scenario's hebben natte cellen")

    # Woordenboeken om snel waarden op te zoeken per scenarionummer
    cid_per_id = dict(zip(kandidaten[cfg.KOL_ID], kandidaten[cfg.KOL_CID]))
    schade_per_id = dict(zip(kandidaten[cfg.KOL_ID], kandidaten[cfg.KOL_SCHADE]))
    slachtoffers_per_id = dict(zip(kandidaten[cfg.KOL_ID], kandidaten[cfg.KOL_SLACHTOFFERS]))

    # Optioneel: alleen de eerste N scenario's verwerken (om te testen), bijv. "python 01a_bepaal_overlap.py 10"
    te_verwerken = kandidaten[cfg.KOL_ID].tolist()
    if len(sys.argv) > 1:
        te_verwerken = te_verwerken[:int(sys.argv[1])]

    # Per scenario: de buur met de meeste overlap, de overlap, en het verschil in schade en slachtoffers
    resultaten = []
    for nummer, scenario_id in enumerate(te_verwerken, start=1):
        buur_id, overlap = vind_meeste_overlap(kandidaten, scenario_id, cid_per_id)
        resultaten.append({
            cfg.KOL_ID: scenario_id,
            cfg.KOL_MEESTE_OVERLAP_SCENARIO: buur_id,
            cfg.KOL_OVERLAP: overlap,
            cfg.KOL_VERSCHIL_SCHADE: bepaal_verschil(schade_per_id[scenario_id], schade_per_id.get(buur_id)),
            cfg.KOL_VERSCHIL_SLACHTOFFERS: bepaal_verschil(slachtoffers_per_id[scenario_id], slachtoffers_per_id.get(buur_id)),
        })
        if nummer % 100 == 0:  # Voortgang tonen
            print(f"{nummer}/{len(te_verwerken)} scenario's verwerkt")

    # Voeg de resultaten toe aan de metadata en sla op; alle rijen blijven behouden
    resultaten = pd.DataFrame(resultaten)
    resultaten[cfg.KOL_MEESTE_OVERLAP_SCENARIO] = pd.array(resultaten[cfg.KOL_MEESTE_OVERLAP_SCENARIO], dtype="Int64")
    aantal_rijen = len(metadata)
    metadata = metadata.merge(resultaten, on=cfg.KOL_ID, how="left")
    assert len(metadata) == aantal_rijen, "het aantal rijen is veranderd door het samenvoegen"
    metadata.to_parquet(cfg.METADATA_01A, index=False)
    print(f"{resultaten[cfg.KOL_OVERLAP].notna().sum()} scenario's met een buur -> {cfg.METADATA_01A}")


if __name__ == "__main__":  # Alleen bij direct starten
    main()  # Uitvoeren
