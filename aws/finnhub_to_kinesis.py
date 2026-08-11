import json
import os
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import urlopen

import boto3


kinesis = boto3.client("kinesis")


def lambda_handler(event, context):
    api_key = os.environ["FINNHUB_API_KEY"]
    stream_name = os.environ["KINESIS_STREAM_NAME"]
    symbol = "AAPL"

    query = urlencode({
        "symbol": symbol,
        "token": api_key,
    })

    url = f"https://finnhub.io/api/v1/quote?{query}"

    with urlopen(url, timeout=20) as response:
        quote = json.loads(response.read().decode("utf-8"))

    if "error" in quote:
        raise RuntimeError(f"Finnhub error: {quote['error']}")

    stock_event = {
        "event_type": "stock_quote",
        "source": "finnhub",
        "symbol": symbol,
        "ingestion_time": datetime.now(timezone.utc).isoformat(),
        "data": quote,
    }

    result = kinesis.put_record(
        StreamName=stream_name,
        Data=json.dumps(stock_event).encode("utf-8"),
        PartitionKey=symbol,
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Stock quote sent to Kinesis",
            "symbol": symbol,
            "sequence_number": result["SequenceNumber"],
        }),
    }