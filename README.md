# 🚀 Fintech Ticker Pipeline

An automated financial data pipeline that extracts, validates, and filters stock tickers from Yahoo Finance using a **Bronze/Silver/Gold medallion architecture** — producing a daily selection of clean, dividend-free tickers ready for backtesting.

---

## 📌 What It Does

Every day at 6pm, the pipeline:

1. Extracts price history for **5,820 tickers** from Yahoo Finance (NYSE + Nasdaq)
2. Validates and cleans the data (Bronze → Silver)
3. Applies business filters — no dividends, minimum 10 years of history (Silver → Gold)
4. Randomly selects **40 tickers** from the ~965 Gold universe
5. Exports them as **CSV files** ready to drag into a backtesting engine
6. Sends a **daily email report** with pipeline statistics

---

## 🏗️ Architecture

```
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
   ✅ High >= Low (impossible values detected)
   ⚠️  Dead Letter Queue → tickers that fail rules
        ↓
🥇 Gold Layer
   Business filters:
   ✅ No dividends paid
   ✅ Minimum 10 years of price history
        ↓
📁 listos_para_hoy/
   40 random CSVs ready for backtesting
```

---

## 🔁 Dead Letter Queue

Tickers that fail validation are not discarded — they go to a **Dead Letter Queue** with intelligent retry logic:

| Reason | Retry Frequency |
|--------|----------------|
| Insufficient history | Every 6 months (auto-promoted when they qualify) |
| Temporary Yahoo Finance failure | Every 7 days |
| Delisted / no data | Never retried |

---

## 📊 Daily Stats (example)

```
🥉 Bronze:  5,659 successful | 161 failed
🥈 Silver:  2,061 valid      | 3,596 Dead Letter
🥇 Gold:      965 tickers    | 1,096 rejected (pay dividends)
📁 Output:   40 random CSVs  | ready for backtesting
⏱️  Runtime: ~35 minutes
```

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| **Python 3.13** | Core language |
| **yfinance** | Yahoo Finance API |
| **Pandas** | Data manipulation |
| **Parquet** | Efficient binary storage (Bronze/Gold) |
| **JSON** | Lightweight metadata storage (Silver/Dead Letter) |
| **Loguru** | Professional logging |
| **Schedule** | Daily automation |
| **smtplib** | Email reporting |
| **python-dotenv** | Secure credential management |

---

## 📁 Project Structure

```
fintech-ticker-pipeline/
├── pipeline.py              # Main orchestrator
├── src/
│   ├── extractor.py         # Bronze layer — Yahoo Finance download
│   ├── validador.py         # Silver layer — data validation
│   ├── transformador.py     # Gold layer — business filters
│   ├── selector.py          # Daily random selection → CSV export
│   ├── tickers_lista.py     # Universe definition (S&P 500 + Nasdaq)
│   ├── cache_dividendos.py  # Dividend cache (refreshes every 7 days)
│   └── reporte_email.py     # Daily email report
├── data/
│   ├── bronze/              # Raw historical data (Parquet)
│   ├── silver/              # Valid ticker metadata (JSON)
│   ├── silver_dead_letter/  # Failed tickers with retry logic (JSON)
│   ├── gold/                # Filtered tickers ready for selection (Parquet)
│   └── listos_para_hoy/     # Daily CSV output for backtesting
├── logs/                    # Daily pipeline logs (30-day retention)
├── tickers_sp500.csv        # S&P 500 ticker list
├── tickers_nasdaq.csv       # Nasdaq ticker list
├── .env                     # Credentials (not tracked by Git)
├── .gitignore
└── README.md
```

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/EnderA44hub/fintech-ticker-pipeline.git
cd fintech-ticker-pipeline
```

### 2. Install dependencies

```bash
pip install pandas yfinance pyarrow schedule loguru python-dotenv
```

### 3. Configure credentials

Create a `.env` file in the root directory:

```
EMAIL=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
```

> To generate a Gmail app password: Google Account → Security → Two-step verification → App passwords

### 4. Download ticker lists

Download these files and place them in the root directory:

- `tickers_sp500.csv` — [S&P 500 constituents](https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv)
- `tickers_nasdaq.csv` — [Nasdaq listings](https://raw.githubusercontent.com/datasets/nasdaq-listings/main/data/nasdaq-listed.csv)

### 5. Create data folders

```bash
mkdir -p data/bronze data/silver data/silver_dead_letter data/gold data/listos_para_hoy logs
```

---

## ▶️ Usage

### Run manually

```bash
python pipeline.py
```

### Run automatically every day at 6pm

```bash
python pipeline.py auto
```

### Schedule with Windows Task Scheduler

Set up a daily task pointing to:
- **Program:** `python.exe`
- **Arguments:** `pipeline.py`
- **Start in:** `C:\path\to\fintech-ticker-pipeline`

---

## 📧 Daily Email Report

After each run, you receive an email with:

- Pipeline duration
- Bronze / Silver / Gold statistics
- Dead Letter count
- The 40 tickers selected for today's backtesting

---

## 🔑 Key Concepts

**Medallion Architecture** — data flows through layers of increasing quality and business value, never deleting raw data.

**Incremental Loading** — after the first full historical download, only the last 5 days are fetched per ticker, reducing runtime significantly.

**Dividend Cache** — dividend status is cached locally and refreshed every 7 days, avoiding redundant API calls.

**Dead Letter Queue** — failed tickers are stored with their failure reason and retry schedule, not silently dropped.

---

## 📈 Use Case

This pipeline was built to feed a **HTML-based backtesting engine** with fresh, unbiased ticker data daily. By randomizing the selection from a clean universe of 965 qualified tickers, it avoids the bias of always testing the same well-known stocks.

The Gold universe (~965 tickers) provides enough variety for **24+ days of non-repeating backtests** with 40 tickers per day.

---

## 🗺️ Roadmap

- [ ] Two-speed pipeline (weekly universe update + daily incremental)
- [ ] DuckDB integration for instant historical queries
- [ ] Dashboard — real-time pipeline status visualization
- [ ] Cloud deployment (AWS / GCP)
- [ ] Direct integration with backtesting engine (auto-load CSVs)

---

## 👤 Author

**EnderA44hub** — combining financial markets knowledge with data engineering to build production-grade fintech infrastructure.

---

*Built from scratch in one day as a learning project. Every concept — Bronze/Silver/Gold layers, Dead Letter Queue, incremental loading, dividend caching — was derived from first principles before implementing.*