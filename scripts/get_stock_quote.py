import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests


# Read the private API key from the computer's environment.
api_key = os.environ.get("FINNHUB_API_KEY")

if not api_key:
    raise RuntimeError("FINNHUB_API_KEY is not set")

# Stock we want to request.
symbol = "AAPL"

response = requests.get(
    "https://finnhub.io/api/v1/quote",
    params={
        "symbol": symbol,
        "token": api_key,
    },
    timeout=30,
)

# Stop the program if the API request failed.
response.raise_for_status()

stock_data = response.json()

# Add information that will help us track the data later.
raw_record = {
    "source": "finnhub",
    "symbol": symbol,
    "ingestion_time": datetime.now(timezone.utc).isoformat(),
    "data": stock_data,
}

# Find the project folder and its raw API directory.
project_folder = Path(__file__).resolve().parents[1]
output_folder = project_folder / "data" / "raw" / "api"
output_folder.mkdir(parents=True, exist_ok=True)

# Give every response a unique filename.
timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
output_file = output_folder / f"{symbol}_{timestamp}.json"

with output_file.open("w", encoding="utf-8") as file:
    json.dump(raw_record, file, indent=2)

print("Stock data received:")
print(json.dumps(stock_data, indent=2))
print(f"Saved to: {output_file}")