"""Controleplot: toon het water uit stap 00c als kaartje (opgeslagen in temp/)."""

import sys  # Zoekpad en opdrachtregel
from pathlib import Path  # Padafhandeling

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # Zodat config.py gevonden wordt

import matplotlib.pyplot as plt  # Plots maken
import numpy as np  # Rekenen met rasters
import pandas as pd  # Tabeldata

import config as cfg  # Eigen configuratie


def main():
    # Met "test" erachter ("python plot_water.py test") het testbestand tonen
    naam = "waterwegen_pdok_test.parquet" if "test" in sys.argv else "waterwegen_pdok.parquet"
    water = pd.read_parquet(cfg.WATER_MAP / naam)

    # Van celnummer terug naar rij en kolom in het grid
    rij, kolom = np.divmod(water.cell_id.to_numpy(), cfg.GRID_KOLOMMEN)

    # Leeg plaatje met precies de grootte van het gebied; cellen zonder water blijven leeg (NaN)
    plaatje = np.full((rij.max() - rij.min() + 1, kolom.max() - kolom.min() + 1), np.nan)
    plaatje[rij - rij.min(), kolom - kolom.min()] = water.wet_pct  # Percentage water per cel

    # Randen van het plaatje in RD-coördinaten (links, rechts, onder, boven)
    gebied = (cfg.GRID_X0 + kolom.min() * cfg.GRID_CEL, cfg.GRID_X0 + (kolom.max() + 1) * cfg.GRID_CEL,
              cfg.GRID_Y0 - (rij.max() + 1) * cfg.GRID_CEL, cfg.GRID_Y0 - rij.min() * cfg.GRID_CEL)

    # Teken en bewaar het kaartje
    plt.figure(figsize=(10, 8))
    plt.imshow(plaatje, extent=gebied, cmap="Blues", vmin=0, vmax=100)
    plt.colorbar(label="Water per 25 m-cel (%)")
    plt.title(f"Water uit PDOK ({len(water)} cellen)")
    plt.xlabel("X (RD)")
    plt.ylabel("Y (RD)")
    cfg.CONTROLE_MAP.mkdir(exist_ok=True)
    uitvoer = cfg.CONTROLE_MAP / "plot_water.png"
    plt.savefig(uitvoer, dpi=150, bbox_inches="tight")
    print(f"plot opgeslagen: {uitvoer}")


if __name__ == "__main__":  # Alleen bij direct starten
    main()  # Uitvoeren
