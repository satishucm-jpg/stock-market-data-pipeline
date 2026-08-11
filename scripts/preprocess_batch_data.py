import csv
import json
from datetime import datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


project_folder = Path(__file__).resolve().parents[1]

input_file = (
    project_folder
    / "data"
    / "raw"
    / "batch"
    / "SP500_Historical_Data.csv"
)

output_folder = project_folder / "data" / "processed" / "batch"
output_file = output_folder / "stock_prices.parquet"

quarantine_folder = project_folder / "data" / "quarantine"
quarantine_file = quarantine_folder / "invalid_stock_prices.jsonl"

batch_size = 100_000

schema = pa.schema(
    [
        ("ticker", pa.string()),
        ("date", pa.date32()),
        ("open", pa.float64()),
        ("high", pa.float64()),
        ("low", pa.float64()),
        ("close", pa.float64()),
        ("adjusted_close", pa.float64()),
        ("volume", pa.int64()),
        ("source", pa.string()),
    ]
)


def process_row(row):
    errors = []

    required_columns = [
        "Ticker",
        "Date",
        "Open",
        "High",
        "Low",
        "Close",
        "Adj Close",
        "Volume",
    ]

    for column in required_columns:
        value = row.get(column)

        if value is None or not value.strip():
            errors.append("missing_value")
            return None, errors

    try:
        trade_date = datetime.strptime(
            row["Date"], "%Y-%m-%d"
        ).date()
    except ValueError:
        errors.append("invalid_date")
        return None, errors

    try:
        open_price = float(row["Open"])
        high_price = float(row["High"])
        low_price = float(row["Low"])
        close_price = float(row["Close"])
        adjusted_close = float(row["Adj Close"])
        volume = int(row["Volume"])
    except ValueError:
        errors.append("invalid_number")
        return None, errors

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

    if errors:
        return None, errors

    cleaned_row = {
        "ticker": row["Ticker"].strip().upper(),
        "date": trade_date,
        "open": open_price,
        "high": high_price,
        "low": low_price,
        "close": close_price,
        "adjusted_close": adjusted_close,
        "volume": volume,
        "source": "kaggle",
    }

    return cleaned_row, []


if not input_file.exists():
    raise FileNotFoundError(f"Input file not found: {input_file}")

output_folder.mkdir(parents=True, exist_ok=True)
quarantine_folder.mkdir(parents=True, exist_ok=True)

valid_count = 0
invalid_count = 0
rows_checked = 0
clean_batch = []

writer = pq.ParquetWriter(
    output_file,
    schema,
    compression="snappy",
)

try:
    with (
        input_file.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as input_stream,
        quarantine_file.open(
            "w",
            encoding="utf-8",
        ) as quarantine_stream,
    ):
        reader = csv.DictReader(input_stream)

        for row_number, row in enumerate(reader, start=2):
            rows_checked += 1
            cleaned_row, errors = process_row(row)

            if errors:
                invalid_count += 1

                quarantine_record = {
                    "row_number": row_number,
                    "errors": errors,
                    "record": row,
                }

                quarantine_stream.write(
                    json.dumps(quarantine_record) + "\n"
                )
            else:
                valid_count += 1
                clean_batch.append(cleaned_row)

            if len(clean_batch) >= batch_size:
                table = pa.Table.from_pylist(
                    clean_batch,
                    schema=schema,
                )
                writer.write_table(table)
                clean_batch.clear()

            if rows_checked % 500_000 == 0:
                print(f"Processed {rows_checked:,} records...")

        if clean_batch:
            table = pa.Table.from_pylist(
                clean_batch,
                schema=schema,
            )
            writer.write_table(table)

finally:
    writer.close()

print("\nPreprocessing complete")
print(f"Records checked: {rows_checked:,}")
print(f"Valid records:   {valid_count:,}")
print(f"Invalid records: {invalid_count:,}")
print(f"Parquet output:  {output_file}")
print(f"Quarantine:      {quarantine_file}")