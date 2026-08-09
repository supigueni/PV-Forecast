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
import matplotlib.dates as mdates
import pandas as pd
from datetime import datetime as dt

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PLOT_DIR = BASE_DIR / "plots"
PLOT_DIR.mkdir(exist_ok=True)

# We'll group by full source name (e.g. open_meteo_so, fenecon)
data = {}

# ----------------------------------------------------------------------
# Load files into `data` keyed by combined source (e.g. open_meteo_so)
# ----------------------------------------------------------------------
for file in sorted(DATA_DIR.glob("*.csv")):
    stem = file.stem

    # Expected filename: YYYYMMDD_source_variant.csv
    parts = stem.split("_", 2)

    if len(parts) == 3:
        date, source_base, variant = parts
        source_full = f"{source_base}_{variant}"
    elif len(parts) == 2:
        date, source_base = parts
        source_full = source_base
        variant = ""
    else:
        date = ""
        source_full = stem
        variant = ""

    df = pd.read_csv(file)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime")

    entry = {
        "date": date,
        "source": source_full,
        "variant": variant,
        "filename": stem,
        "df": df,
    }

    data.setdefault(source_full, []).append(entry)
    print(f"Loaded {stem} as source {source_full}")

# ----------------------------------------------------------------------
# Build one timeseries per source, then merge into a wide table (one column per source)
per_source = {}

for source, entries in data.items():
    src_frames = []
    for entry in entries:
        df = entry["df"].copy()

        # If we have a date in the filename and the source is not 'fenecon',
        # trim the forecast to that single day (cut off following days).
        date_str = entry.get("date", "")
        if date_str and entry.get("source", "").lower() != "fenecon":
            try:
                file_date = dt.strptime(date_str, "%Y%m%d").date()
                df = df[df["datetime"].dt.date == file_date]
            except Exception:
                pass

        df = df.set_index("datetime")[ ["power"] ].rename(columns={"power": source})
        src_frames.append(df)

    if src_frames:
        # concatenate and average duplicate timestamps
        src_series = pd.concat(src_frames).groupby(level=0).mean()
        per_source[source] = src_series

if per_source:
    # union all timestamps
    all_index = None
    for s, ser in per_source.items():
        if all_index is None:
            all_index = ser.index
        else:
            all_index = all_index.union(ser.index)
    all_index = all_index.sort_values()

    # determine a reasonable frequency (use minimum delta)
    if len(all_index) >= 2:
        diffs = all_index.to_series().diff().dropna()
        min_diff = diffs.min()
        if pd.isna(min_diff) or min_diff == pd.Timedelta(0):
            min_diff = pd.Timedelta(minutes=1)
    else:
        min_diff = pd.Timedelta(minutes=1)

    full_index = pd.date_range(start=all_index.min(), end=all_index.max(), freq=min_diff)

    wide = pd.DataFrame(index=full_index)
    for source, ser in per_source.items():
        wide[source] = ser.reindex(full_index)

    wide = wide.sort_index()
    wide = wide.interpolate(method="time", limit_direction="both")

    combined_file = PLOT_DIR / "combined_wide.csv"
    wide.reset_index().rename(columns={"index": "datetime"}).to_csv(combined_file, index=False)
    print(f"Saved combined wide dataset to {combined_file}")
    # Plot wide combined dataset: one color/label per source
    fig, ax = plt.subplots(figsize=(14, 6))
    cmap = plt.get_cmap("tab10")
    colors = cmap.colors if hasattr(cmap, "colors") else [cmap(i) for i in range(10)]

    for i, col in enumerate(wide.columns):
        ax.plot(
            wide.index,
            wide[col],
            label=col,
            color=colors[i % len(colors)],
            linewidth=1,
            marker="",
            alpha=0.9,
        )

    ax.set_title("Combined PV Power by Source")
    ax.set_xlabel("Datetime")
    ax.set_ylabel("Power [kW]")
    ax.grid(True)
    ax.legend(fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
    fig.autofmt_xdate()
    fig.tight_layout()
    combined_png = PLOT_DIR / "combined_datasets.png"
    fig.savefig(combined_png, dpi=200)
    plt.close(fig)
    print(f"Saved combined dataset plot to {combined_png}")
else:
    print("No datasets found to combine")

# ----------------------------------------------------------------------
# Plot data
# ----------------------------------------------------------------------

for source, datasets in data.items():

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

    ax.set_title(source)
    ax.set_xlabel("Datetime")
    ax.set_ylabel("Power [kW]")
    ax.grid(True)
    ax.legend(fontsize=8)

    fig.tight_layout()

    filename = PLOT_DIR / f"{source}.png"
    fig.savefig(filename, dpi=200)

    plt.close(fig)

    print(f"Saved {filename}")



# Additional grouping/plotting was consolidated earlier; nothing to do here.