# NY Open Futures Terminal

A **local research terminal** for opening-range breakout (ORB) backtests on E-mini and Micro E-mini futures: **MNQ**, **NQ**, **MES**, **ES**. Uses **Yahoo Finance (free)** by default—no API key or paid data required. Built for serious research: correct session logic, no lookahead bias, and full breakdowns (trades/PnL per day, week, month).

---

## Quick start

```bash
cd ny-open-futures-terminal
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open **http://localhost:8501**. In the sidebar: choose **Symbol**, **Days of data**, and **Opening range** (default 8:00–9:15 AM CST). Click **Run analysis**. Your trade plan, evidence table, breakdown by period, and charts appear on the main page.

---

## What it does

- **Data** — OHLCV from **Yahoo Finance (free)** by default. Optional Databento (paid). Parquet cache to avoid re-downloads.
- **Sessions** — America/Chicago (CST) for opening range; configurable OR (e.g. 8:00–9:15 AM) and trade window end.
- **Opening range breakout** — First break after OR close (morning breakout); entry on close beyond OR high/low, stop at opposite OR side, target at configurable R multiple.
- **Backtest** — Bar-by-bar simulation, no lookahead. Slippage and fees. Auto-optimize for **highest $ per trade** or highest win rate.
- **Trade plan** — One-line plan, your numbers (risk per trade, expected $ per trade, confidence), exact evidence table (timestamps, entry/stop/target/exit, PnL, volume when available), suggested order forms (long/short), example in ticks.
- **Breakdown by period** — Trades and profit **per day**, **per week**, **per month**; avg trades/PnL per day/week/month; best and worst day.
- **Data we analyzed** — Expandable section: source, symbol, interval, bar count, date range; **price chart** of the data used; **analysis log** (data loaded → OR computed → backtest/optimization). **Export ticker data (CSV)** for the analyzed timeframe and symbol.
- **Charts** — Equity curve, drawdown, R histogram, OR width vs R, weekday breakdown. Day Explorer for any session with OR levels and trade.
- **Diagnostics** — Data quality, time range, cache path (under More → Diagnostics).

---

## Supported instruments

| Symbol | Name                    |
|--------|-------------------------|
| MNQ=F  | Micro E-mini Nasdaq-100 |
| NQ=F   | E-mini Nasdaq-100       |
| MES=F  | Micro E-mini S&P 500    |
| ES=F   | E-mini S&P 500          |

Contract specs (tick size, point value) are used for dollar PnL.

---

## Data sources

### Yahoo Finance (default, free)

- **No API key.** Select **Yahoo (free)** in the sidebar (Advanced settings → Data → Source).
- Intervals: 1m, 2m, 5m, 15m, 30m, 60m.
- **Limit:** 1m and 2m have ~**7 calendar days** of intraday history; use **5m** or **15m** for longer backtests.
- Data is cached as Parquet under `data/cache/`.

### Databento (optional, paid)

- Select **Databento (paid)** only if you have a Databento subscription. The app runs fully on Yahoo otherwise.

### Cache

- Cache is used by default. Use **Refresh cache** in the sidebar to force re-fetch.

---

## Research workflow

1. **Sidebar** — Symbol (e.g. MNQ), days of data, opening range (default 8:00–9:15 AM CST). Optionally enable **Auto-optimize target** and choose **Expectancy (highest $ per trade)** or **Win rate**.
2. **Run analysis** — Click **Run analysis**. Main page shows: data we analyzed (with chart + log + export CSV), your trade plan, evidence table, breakdown by day/week/month, equity and drawdown.
3. **More** — Expand “More” for Backtest details, Structure, Time-of-Day, Day Explorer, Trade Log, Diagnostics. Export trade log or ticker data as CSV.

---

## Project structure

```
ny-open-futures-terminal/
  app.py                    # Streamlit entry
  config/defaults.yaml      # Sessions, strategy, contracts
  data/cache/               # Parquet cache (gitignored)
  src/
    config.py               # Config loader
    models.py               # DataConfig, TradeRecord, PerformanceSummary, etc.
    data/                   # Yahoo, Databento, cache, loaders
    sessions/               # Session engine, OR bounds (CST)
    strategies/             # ORB, failed breakout, sweep reversal
    backtest/               # Engine, execution, metrics, optimizer
    analytics/              # Structure, patterns, time-of-day
    charts/                 # Price, performance, exploratory
    ui/                     # Sidebar, overview, tabs
```

---

## Known limitations

- **Yahoo 1m/2m** — ~7 day lookback; use 5m or 15m for longer history.
- **Failed breakout / Sweep reversal** — Modules exist but return no trades until logic is implemented.
- **Single symbol per run** — Change symbol and re-run for another contract.

---

## License

For personal research and education. Not financial advice.
