import csv
import json
from datetime import datetime, timezone
from pathlib import Path


project_folder = Path(__file__).resolve().parents[1]

input_file = (
    project_folder
    / "data"
    / "raw"
    / "batch"
    / "SP500_Historical_Data.csv"
)

report_folder = project_folder / "data" / "processed"
report_file = report_folder / "batch_validation_report.json"

required_columns = {
    "Ticker",
    "Date",
    "Open",
    "High",
    "Low",
    "Close",
    "Adj Close",
    "Volume",
}

error_counts = {
    "missing_value": 0,
    "invalid_date": 0,
    "invalid_number": 0,
    "non_positive_price": 0,
    "negative_volume": 0,
    "invalid_high_price": 0,
    "invalid_low_price": 0,
}

total_rows = 0
valid_rows = 0
invalid_rows = 0
invalid_samples = []


def validate_row(row):
    errors = []

    # Check for missing values.
    for column in required_columns:
        value = row.get(column)

        if value is None or not value.strip():
            errors.append("missing_value")
            break

    if errors:
        return errors

    # Check the date.
    try:
        datetime.strptime(row["Date"], "%Y-%m-%d")
    except ValueError:
        errors.append("invalid_date")

    # Convert price and volume fields.
    try:
        open_price = float(row["Open"])
        high_price = float(row["High"])
        low_price = float(row["Low"])
        close_price = float(row["Close"])
        adjusted_close = float(row["Adj Close"])
        volume = int(row["Volume"])
    except ValueError:
        errors.append("invalid_number")
        return errors

    prices = [
        open_price,
        high_price,
        low_price,
        close_price,
        adjusted_close,
    ]

    if any(price <= 0 for price in prices):
        errors.append("non_positive_price")

    if volume < 0:
        errors.append("negative_volume")

    if high_price < max(open_price, low_price, close_price):
        errors.append("invalid_high_price")

    if low_price > min(open_price, high_price, close_price):
        errors.append("invalid_low_price")

    return errors


if not input_file.exists():
    raise FileNotFoundError(f"Input file not found: {input_file}")

with input_file.open("r", encoding="utf-8-sig", newline="") as file:
    reader = csv.DictReader(file)

    actual_columns = set(reader.fieldnames or [])
    missing_columns = required_columns - actual_columns

    if missing_columns:
        raise ValueError(
            f"Required columns are missing: {sorted(missing_columns)}"
        )

    for row_number, row in enumerate(reader, start=2):
        total_rows += 1
        errors = validate_row(row)

        if errors:
            invalid_rows += 1

            for error in set(errors):
                error_counts[error] += 1

            if len(invalid_samples) < 10:
                invalid_samples.append(
                    {
                        "row_number": row_number,
                        "ticker": row.get("Ticker"),
                        "date": row.get("Date"),
                        "errors": errors,
                    }
                )
        else:
            valid_rows += 1

        if total_rows % 500_000 == 0:
            print(f"Checked {total_rows:,} records...")

report = {
    "input_file": str(input_file),
    "validation_time_utc": datetime.now(timezone.utc).isoformat(),
    "total_rows": total_rows,
    "valid_rows": valid_rows,
    "invalid_rows": invalid_rows,
    "error_counts": error_counts,
    "invalid_samples": invalid_samples,
}

report_folder.mkdir(parents=True, exist_ok=True)

with report_file.open("w", encoding="utf-8") as file:
    json.dump(report, file, indent=2)

print("\nValidation complete")
print(f"Total records:   {total_rows:,}")
print(f"Valid records:   {valid_rows:,}")
print(f"Invalid records: {invalid_rows:,}")

print("\nErrors:")
for error, count in error_counts.items():
    print(f"- {error}: {count:,}")

print(f"\nReport saved to: {report_file}")