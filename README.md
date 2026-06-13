# 🚀 Fintech Ticker Pipeline

An automated financial data pipeline that extracts, validates, and filters stock tickers from Yahoo Finance using a Bronze/Silver/Gold medallion architecture — producing a daily selection of clean, dividend-free tickers ready for backtesting.

## What It Does

Every day at 6pm, the pipeline:
1. Extracts price history for 5,820 tickers from Yahoo Finance (NYSE + Nasdaq)
2. Validates and cleans the data (Bronze → Silver)
3. Applies business filters — no dividends, minimum 10 years of history (Silver → Gold)
4. Randomly selects 40 tickers from the ~965 Gold universe
5. Exports them as CSV files ready for backtesting
6. Sends a daily email report with pipeline statistics

## Architecture

Yahoo Finance API (5,820 tickers)
        ↓
🥉 Bronze Layer
   Raw data as-is, never deleted
   Incremental updates (only last 5 days after first load)
        ↓
🥈 Silver Layer
   Validation rules:
   ✅ Required columns present (Open, High, Low, Close, Volume)
   ✅ No negative or zero prices
   ✅ High >= Low
   ⚠️  Dead Letter Queue → tickers that fail rules
        ↓
🥇 Gold Layer
   Business filters:
   ✅ No dividends paid
   ✅ Minimum 10 years of price history
        ↓
📁 listos_para_hoy/
   40 random CSVs ready for backtesting

## Dead Letter Queue

| Reason | Retry Frequency |
|--------|----------------|
| Insufficient history | Every 6 months |
| Temporary Yahoo Finance failure | Every 7 days |
| Delisted / no data | Never retried |

## Daily Stats (example)

🥉 Bronze:  5,659 successful | 161 failed
🥈 Silver:  2,061 valid      | 3,596 Dead Letter
🥇 Gold:      965 tickers    | 1,096 rejected (pay dividends)
📁 Output:   40 random CSVs  | ready for backtesting
⏱️  Runtime: ~35 minutes

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.13 | Core language |
| yfinance | Yahoo Finance API |
| Pandas | Data manipulation |
| Parquet | Efficient binary storage |
| Loguru | Professional logging |
| Schedule | Daily automation |
| smtplib | Email reporting |

## Project Structure

fintech-ticker-pipeline/
├── pipeline.py
├── src/
│   ├── extractor.py
│   ├── validador.py
│   ├── transformador.py
│   ├── selector.py
│   ├── tickers_lista.py
│   ├── cache_dividendos.py
│   └── reporte_email.py
├── data/
│   ├── bronze/
│   ├── silver/
│   ├── silver_dead_letter/
│   ├── gold/
│   └── listos_para_hoy/
├── logs/
├── tickers_sp500.csv
├── tickers_nasdaq.csv
└── .env

## Installation

git clone https://github.com/EnderA44hub/fintech-ticker-pipeline.git
cd fintech-ticker-pipeline
pip install pandas yfinance pyarrow schedule loguru python-dotenv

## Usage

python pipeline.py          # Run once
python pipeline.py auto     # Run daily at 6pm

## Key Concepts

Medallion Architecture — data flows through layers of increasing quality, never deleting raw data.
Incremental Loading — after first full download, only last 5 days fetched per ticker.
Dividend Cache — refreshed every 7 days to avoid redundant API calls.
Dead Letter Queue — failed tickers stored with failure reason and retry schedule.

## Use Case

Built to feed a backtesting engine with fresh, unbiased ticker data daily. By randomizing selection from 965 qualified tickers, it eliminates the bias of always testing the same well-known stocks. The Gold universe provides 24+ days of non-repeating backtests at 40 tickers per day.

## Author

EnderA44hub — combining financial markets knowledge with data engineering to build production-grade fintech infrastructure.

Built from scratch. Every concept — Bronze/Silver/Gold layers, Dead Letter Queue, incremental loading, dividend caching — derived from first principles before implementing.
