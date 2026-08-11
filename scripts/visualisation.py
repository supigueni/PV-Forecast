"""
Visualization of PV power data.

- Loads normalized CSV files from ../data
- Groups files by source variant
- Merges each source into one time series
- Saves each source series as CSV in ../plots
- Plots each source series with markers to show measured points
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
# Build one merged timeseries per source and save each source as CSV and PNG
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

if not per_source:
    print("No datasets found to merge per source")

for source, series in per_source.items():
    series = series.sort_index()
    output_csv = PLOT_DIR / f"{source}.csv"
    series.reset_index().rename(columns={"datetime": "datetime", source: "power"}).to_csv(output_csv, index=False)
    print(f"Saved {output_csv}")

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(
        series.index,
        series[source],
        marker="o",
        linestyle="-",
        markersize=4,
        linewidth=1,
        alpha=0.8,
        label=source,
    )

    ax.set_title(source)
    ax.set_xlabel("Datetime")
    ax.set_ylabel("Power [kW]")
    ax.grid(True)
    ax.legend(fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
    fig.autofmt_xdate()
    fig.tight_layout()

    output_png = PLOT_DIR / f"{source}.png"
    fig.savefig(output_png, dpi=200)
    plt.close(fig)

    print(f"Saved {output_png}")

# ----------------------------------------------------------------------
# Combined comparison plot for fenecon_complete and open_meteo_complete
if "fenecon_complete" in per_source and "open_meteo_complete" in per_source:
    fenecon = per_source["fenecon_complete"].sort_index()
    open_meteo = per_source["open_meteo_complete"].sort_index()

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(
        fenecon.index,
        fenecon,
        marker="o",
        linestyle="-",
        markersize=4,
        linewidth=1,
        alpha=0.8,
        label="fenecon_complete",
    )
    ax.plot(
        open_meteo.index,
        open_meteo,
        marker="o",
        linestyle="-",
        markersize=4,
        linewidth=1,
        alpha=0.8,
        label="open_meteo_complete",
    )

    ax.set_title("Fenecon Complete vs Open Météo Complete")
    ax.set_xlabel("Datetime")
    ax.set_ylabel("Power [kW]")
    ax.grid(True)
    ax.legend(fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
    fig.autofmt_xdate()
    fig.tight_layout()

    comparison_png = PLOT_DIR / "fenecon_vs_open_meteo_complete.png"
    fig.savefig(comparison_png, dpi=200)
    plt.close(fig)
    print(f"Saved {comparison_png}")
else:
    print("Skipping combined comparison plot: required sources missing")

