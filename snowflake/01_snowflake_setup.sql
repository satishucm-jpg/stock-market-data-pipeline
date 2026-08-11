CREATE WAREHOUSE STOCK_PIPELINE_WH
  WAREHOUSE_SIZE = 'X-SMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;


CREATE DATABASE IF NOT EXISTS STOCK_MARKET_DB;

CREATE SCHEMA IF NOT EXISTS STOCK_MARKET_DB.ANALYTICS;

USE WAREHOUSE STOCK_PIPELINE_WH;
USE DATABASE STOCK_MARKET_DB;
USE SCHEMA ANALYTICS;

USE ROLE ACCOUNTADMIN;

CREATE STORAGE INTEGRATION STOCK_MARKET_S3_INT
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = S3
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::541950550285:role/snowflake_s3_access_role'
  STORAGE_ALLOWED_LOCATIONS = (
    's3://stock-market-pipeline-mule-2026/processed/',
    's3://stock-market-pipeline-mule-2026/curated/'
  );

DESC INTEGRATION STOCK_MARKET_S3_INT;



USE ROLE ACCOUNTADMIN;
USE WAREHOUSE STOCK_PIPELINE_WH;
USE DATABASE STOCK_MARKET_DB;
USE SCHEMA ANALYTICS;

CREATE OR REPLACE STAGE CURATED_DAILY_METRICS_STAGE
  URL = 's3://stock-market-pipeline-mule-2026/curated/daily_stock_metrics/'
  STORAGE_INTEGRATION = STOCK_MARKET_S3_INT
  FILE_FORMAT = (TYPE = PARQUET);

CREATE OR REPLACE STAGE CURATED_LATEST_QUOTES_STAGE
  URL = 's3://stock-market-pipeline-mule-2026/curated/latest_stock_quotes/'
  STORAGE_INTEGRATION = STOCK_MARKET_S3_INT
  FILE_FORMAT = (TYPE = PARQUET);

LIST @CURATED_DAILY_METRICS_STAGE;




USE ROLE ACCOUNTADMIN;
USE WAREHOUSE STOCK_PIPELINE_WH;
USE DATABASE STOCK_MARKET_DB;
USE SCHEMA ANALYTICS;

CREATE OR REPLACE TABLE DAILY_STOCK_METRICS (
    ticker VARCHAR,
    trade_date DATE,
    open_price FLOAT,
    high_price FLOAT,
    low_price FLOAT,
    close_price FLOAT,
    adjusted_close_price FLOAT,
    volume NUMBER,
    source VARCHAR,
    processed_at TIMESTAMP_NTZ,
    previous_close_price FLOAT,
    daily_return_percent FLOAT,
    daily_range_percent FLOAT,
    moving_average_20 FLOAT,
    moving_average_50 FLOAT,
    volatility_20 FLOAT
);

COPY INTO DAILY_STOCK_METRICS
FROM @CURATED_DAILY_METRICS_STAGE
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
PATTERN = '.*[.]parquet';

CREATE OR REPLACE TABLE LATEST_STOCK_QUOTES (
    symbol VARCHAR,
    current_price FLOAT,
    price_change FLOAT,
    percent_change FLOAT,
    day_high FLOAT,
    day_low FLOAT,
    day_open FLOAT,
    previous_close FLOAT,
    ingestion_time TIMESTAMP_NTZ,
    market_event_time TIMESTAMP_NTZ,
    source VARCHAR,
    processed_at TIMESTAMP_NTZ
);

COPY INTO LATEST_STOCK_QUOTES
FROM @CURATED_LATEST_QUOTES_STAGE
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
PATTERN = '.*[.]parquet';





SELECT COUNT(*) AS total_daily_records
FROM DAILY_STOCK_METRICS;

SELECT *
FROM LATEST_STOCK_QUOTES;



SELECT
    COUNT(*) AS total_records,
    MIN(trade_date) AS first_date,
    MAX(trade_date) AS last_date,
    COUNT(DISTINCT ticker) AS total_stocks
FROM DAILY_STOCK_METRICS;



CREATE OR REPLACE STAGE PROCESSED_BATCH_STAGE
URL = 's3://stock-market-pipeline-mule-2026/processed/batch/stock_prices/'
STORAGE_INTEGRATION = STOCK_MARKET_S3_INT
FILE_FORMAT = (TYPE = PARQUET);





CREATE OR REPLACE TABLE PROCESSED_STOCK_PRICES (
    ticker VARCHAR,
    trade_date DATE,
    open_price FLOAT,
    high_price FLOAT,
    low_price FLOAT,
    close_price FLOAT,
    adjusted_close_price FLOAT,
    volume NUMBER,
    source VARCHAR,
    processed_at TIMESTAMP_NTZ
);

COPY INTO PROCESSED_STOCK_PRICES
FROM @PROCESSED_BATCH_STAGE
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
PATTERN = '.*[.]parquet';

SELECT COUNT(*) AS processed_batch_records
FROM PROCESSED_STOCK_PRICES;

CREATE OR REPLACE STAGE PROCESSED_STREAMING_STAGE
URL = 's3://stock-market-pipeline-mule-2026/processed/streaming/stock_quotes/'
STORAGE_INTEGRATION = STOCK_MARKET_S3_INT
FILE_FORMAT = (TYPE = PARQUET);

CREATE OR REPLACE TABLE PROCESSED_STOCK_QUOTES (
    symbol VARCHAR,
    current_price FLOAT,
    price_change FLOAT,
    percent_change FLOAT,
    day_high FLOAT,
    day_low FLOAT,
    day_open FLOAT,
    previous_close FLOAT,
    ingestion_time TIMESTAMP_NTZ,
    market_event_time TIMESTAMP_NTZ,
    source VARCHAR,
    processed_at TIMESTAMP_NTZ
);

COPY INTO PROCESSED_STOCK_QUOTES
FROM @PROCESSED_STREAMING_STAGE
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
PATTERN = '.*[.]parquet';

SELECT *
FROM PROCESSED_STOCK_QUOTES
ORDER BY market_event_time DESC
LIMIT 10;



SELECT
    trade_date,
    close_price,
    moving_average_20,
    moving_average_50
FROM DAILY_STOCK_METRICS
WHERE ticker = 'AAPL'
ORDER BY trade_date;