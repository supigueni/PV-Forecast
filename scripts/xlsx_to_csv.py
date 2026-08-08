"""
Converts FEMS exported XLSX files directly to the normalized format.

Before running the script
Get data from "http://192.168.178.57/device/0/history"
Store it in data-FEMS-export

Input:
    ../data-FEMS-export/*.xlsx

Output:
    ../data/20260807_fenecon_complete.csv

Output format:
    datetime,power
    2026-08-07 00:00:00,0.0
    ...
"""

from pathlib import Path

import pandas as pd

INPUT_DIR = Path("../data-FEMS-export")
OUTPUT_DIR = Path("../data")
OUTPUT_DIR.mkdir(exist_ok=True)

for xlsx_file in sorted(INPUT_DIR.glob("*.xlsx")):

    print(f"Processing {xlsx_file.name}")

    # Read complete worksheet without interpreting headers
    df = pd.read_excel(xlsx_file, header=None)

    # ------------------------------------------------------------------
    # Find the table header ("Datum / Uhrzeit")
    # ------------------------------------------------------------------

    header_row = None

    for idx, row in df.iterrows():
        if "Datum / Uhrzeit" in row.values:
            header_row = idx
            break

    if header_row is None:
        print("  -> No data table found")
        continue

    # ------------------------------------------------------------------
    # Read worksheet again using the detected header row
    # ------------------------------------------------------------------

    df = pd.read_excel(
        xlsx_file,
        header=header_row,
    )

    # Keep only the required columns
    df = df[["Datum / Uhrzeit", "Erzeugung [W]"]]

    # Rename columns
    df = df.rename(
        columns={
            "Datum / Uhrzeit": "datetime",
            "Erzeugung [W]": "power",
        }
    )

    # Convert datetime
    df["datetime"] = pd.to_datetime(
        df["datetime"],
        format="%d.%m.%Y %H:%M:%S %z",
    ).dt.tz_localize(None)

    # Convert W -> kW
    df["power"] = df["power"] / 1000.0

    # Format datetime
    df["datetime"] = df["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # ------------------------------------------------------------------
    # Generate output filename
    # ------------------------------------------------------------------

    date = pd.to_datetime(df.iloc[0]["datetime"]).strftime("%Y%m%d")

    outfile = OUTPUT_DIR / f"{date}_fenecon_complete.csv"

    df.to_csv(outfile, index=False)

    print(f"  -> {outfile.name}")

print("Done.")