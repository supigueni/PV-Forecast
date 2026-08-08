"""
visualisation of PV power data
- loads csv files from directory "data" as Dataframes in different groups (or lists)
- groups are determined by file name (example: 20260807_open_meteo_so)
    - open_meteo_so
    - open_meteo_sw
    - open_meteo_complete
- shows plot of the data for each group (x: datetime, y: power)
"""
from pathlib import Path

import matplotlib

matplotlib.use("TkAgg", force=True)

import matplotlib.pyplot as plt
import pandas as pd

DATA_DIR = Path("../data")

# Groups are determined by the suffix of the filename
GROUPS = [
    "open_meteo_so",
    "open_meteo_sw",
    "open_meteo_complete",
]

# Dictionary: group -> list of DataFrames
data = {group: [] for group in GROUPS}

# Load all CSV files
for file in DATA_DIR.glob("*.csv"):
    for group in GROUPS:
        if file.stem.endswith(group):
            df = pd.read_csv(file)

            # Convert datetime column
            df["datetime"] = pd.to_datetime(df["datetime"])

            # Sort by datetime just in case
            df = df.sort_values("datetime")

            data[group].append(df)
            break


# Plot one figure per group

PLOT_DIR = Path("plots")
PLOT_DIR.mkdir(exist_ok=True)

for group, dfs in data.items():
    if not dfs:
        print(f"No data for {group}")
        continue

    fig, ax = plt.subplots(figsize=(14, 6))

    for i, df in enumerate(dfs):
        label = df["datetime"].dt.date.iloc[0].isoformat()
        ax.plot(
            df["datetime"],
            df["power"],
            marker="o",
            linestyle="-",
            markersize=3,
            linewidth=1,
            alpha=0.6,
            label=label,
        )

    ax.set_title(group)
    ax.set_xlabel("Datetime")
    ax.set_ylabel("Power [W]")
    ax.grid(True)
    ax.legend()

    fig.tight_layout()

    filename = PLOT_DIR / f"{group}.png"
    fig.savefig(filename, dpi=200)

    plt.close(fig)

    print(f"Saved {filename}")