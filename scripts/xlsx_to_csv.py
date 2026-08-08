"""
Converts all FEMS exported XLSX files to CSV.

The CSV file is written next to the XLSX file using the same filename.
"""

from pathlib import Path

import pandas as pd

DIRECTORY = Path("../data-FEMS-export")

# Find all Excel files
xlsx_files = sorted(DIRECTORY.glob("*.xlsx"))

if not xlsx_files:
    print(f"No XLSX files found in {DIRECTORY.resolve()}")

for xlsx_file in xlsx_files:
    print(f"Converting {xlsx_file.name}...")

    # Read first sheet
    df = pd.read_excel(xlsx_file)

    # Output filename
    csv_file = xlsx_file.with_suffix(".csv")

    # Save as CSV
    df.to_csv(csv_file, index=False, encoding="utf-8")

    print(f" -> {csv_file.name}")

print("Done.")
