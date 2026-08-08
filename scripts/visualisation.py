"""
Visualization of PV power data.

- Loads normalized CSV files from ../data
- Groups files by variant (so, sw, complete)
- Plots all files belonging to the same variant into one figure
"""

from pathlib import Path

import matplotlib

matplotlib.use("TkAgg", force=True)

import matplotlib.pyplot as plt
import pandas as pd

DATA_DIR = Path("../data")
PLOT_DIR = Path("plots")
PLOT_DIR.mkdir(exist_ok=True)

# Variants to compare
GROUPS = [
    "so",
    "sw",
    "complete",
]

# Dictionary: variant -> list of datasets
data = {group: [] for group in GROUPS}

# ----------------------------------------------------------------------
# Load data
# ----------------------------------------------------------------------

for file in sorted(DATA_DIR.glob("*.csv")):
    stem = file.stem

    for group in GROUPS:
        if stem.endswith(f"_{group}"):

            df = pd.read_csv(file)

            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.sort_values("datetime")

            # Expected filename:
            # YYYYMMDD_source_variant.csv
            parts = stem.split("_", 2)

            if len(parts) == 3:
                date, source, variant = parts
            else:
                date = ""
                source = ""
                variant = group

            data[group].append(
                {
                    "date": date,
                    "source": source,
                    "variant": variant,
                    "filename": stem,
                    "df": df,
                }
            )

            print(f"Loaded {stem}")
            break

# ----------------------------------------------------------------------
# Plot data
# ----------------------------------------------------------------------

for group, datasets in data.items():

    if not datasets:
        print(f"No data for '{group}'")
        continue

    fig, ax = plt.subplots(figsize=(14, 6))

    for entry in datasets:

        df = entry["df"]

        ax.plot(
            df["datetime"],
            df["power"],
            marker="o",
            linestyle="-",
            markersize=3,
            linewidth=1,
            alpha=0.7,
            label=entry["filename"],
        )

    ax.set_title(group)
    ax.set_xlabel("Datetime")
    ax.set_ylabel("Power [kW]")
    ax.grid(True)
    ax.legend(fontsize=8)

    fig.tight_layout()

    filename = PLOT_DIR / f"{group}.png"
    fig.savefig(filename, dpi=200)

    plt.close(fig)

    print(f"Saved {filename}")

print("Done.")