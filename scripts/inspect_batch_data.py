import csv
from pathlib import Path


project_folder = Path(__file__).resolve().parents[1]
csv_file = (
    project_folder
    / "data"
    / "raw"
    / "batch"
    / "SP500_Historical_Data.csv"
)

if not csv_file.exists():
    raise FileNotFoundError(f"CSV file not found: {csv_file}")

row_count = 0
sample_rows = []
missing_values = {}

with csv_file.open("r", encoding="utf-8-sig", newline="") as file:
    reader = csv.DictReader(file)

    if reader.fieldnames is None:
        raise ValueError("The CSV does not contain column names")

    missing_values = {column: 0 for column in reader.fieldnames}

    for row in reader:
        row_count += 1

        if len(sample_rows) < 5:
            sample_rows.append(row)

        for column, value in row.items():
            if value is None or not value.strip():
                missing_values[column] += 1

print("\nCSV file:")
print(csv_file)

print("\nColumns:")
for column in reader.fieldnames:
    print(f"- {column}")

print(f"\nTotal rows: {row_count:,}")

print("\nFirst five records:")
for number, row in enumerate(sample_rows, start=1):
    print(f"\nRecord {number}:")
    print(row)

print("\nMissing values:")
for column, count in missing_values.items():
    print(f"- {column}: {count:,}")