# NY Open Futures Terminal

A **production-quality local research terminal** for studying repeated New York open behavior in E-mini and Micro E-mini futures: **MNQ**, **NQ**, **MES**, **ES**. Built for serious research—correct session logic, no lookahead bias, and professional analytics—not a toy dashboard.

---

## Quick start

```bash
cd ny-open-futures-terminal
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open the URL (e.g. **http://localhost:8501**). In the sidebar: choose **Symbol**, **Interval**, and **Lookback**, set the **Opening range** (e.g. 09:30–09:35) and **Trade window end**, then click **Run analysis**.

---

## What it does

- **Data** — Load OHLCV from Yahoo Finance (or Databento when configured). Parquet cache to avoid re-downloads.
- **Sessions** — All logic in **America/New_York** with correct DST and daily grouping. Configurable opening range (OR) and trade window.
- **Opening range** — OR high, low, width, midpoint per session. Configurable OR start/end (e.g. 09:30–09:35).
- **Strategies** — **Opening range breakout (ORB)** fully implemented; Failed breakout and Sweep/reversal skeletons in place.
- **Backtest** — Bar-by-bar simulation: entry (touch / close beyond), stop (opposite OR / fixed R), target (fixed R / opposite side / session close). Slippage and fees. No lookahead.
- **Analytics** — Win rate, expectancy, profit factor, drawdown, R distribution, weekday breakdown, trade log export.
- **Charts** — Price with OR overlay, equity curve, drawdown, R histogram, OR width vs R, weekday avg R. Day explorer with session summary.
- **Diagnostics** — Row count, time range, timezone, duplicates, nulls, cache path.

---

## Supported instruments

| Symbol | Name                  |
|--------|-----------------------|
| MNQ=F  | Micro E-mini Nasdaq-100 |
| NQ=F   | E-mini Nasdaq-100     |
| MES=F  | Micro E-mini S&P 500  |
| ES=F   | E-mini S&P 500        |

Contract specs (point value, tick size, tick value) are used for dollar PnL.

---

## Data sources

### Yahoo Finance (default)

- Works out of the box; no API key.
- Intervals: 1m, 2m, 5m, 15m, 30m, 60m.
- **Limit:** 1m and 2m have ~**7 calendar days** of intraday history; use 5m or 15m for longer backtests.
- Data is cached as Parquet under `data/cache/`.

### Databento (optional)

- Skeleton in `src/data/databento.py`. Set `DATABENTO_API_KEY` and extend the adapter to fetch historical bars.
- Without a key, the app runs fully on Yahoo.

### Cache

- **On** — Same symbol/interval/range uses cache; no re-download.
- **Refresh cache** — Sidebar checkbox forces re-fetch and overwrite for that request.

---

## Research workflow

1. **Data** — Select symbol (e.g. MNQ), interval (5m recommended for 90+ days), lookback. Use “Refresh cache” only when you need fresh data.
2. **Session** — Set opening range (e.g. 09:30–09:35) and trade window end (e.g. 12:00). All times NY.
3. **Strategy** — Choose mode (ORB / failed breakout / sweep reversal), entry trigger, stop, target, direction, and costs (slippage, fee) in the expander.
4. **Run** — Click **Run analysis**. Check Overview for headline metrics, Backtest for full stats and trade log, Day Explorer to inspect specific sessions.
5. **Export** — Use “Export to CSV” in Backtest or Trade Log for further analysis.

---

## Project structure

```
ny-open-futures-terminal/
  app.py                    # Streamlit entry
  config/defaults.yaml      # Sessions, strategy, contracts
  data/cache/               # Parquet cache
  src/
    config.py               # Config loader
    models.py               # Pydantic/dataclass models
    data/                   # Yahoo, Databento, cache, loaders
    sessions/               # NY session engine, OR bounds
    strategies/             # ORB, failed breakout, sweep reversal
    backtest/               # Engine, execution, metrics
    analytics/              # Structure, time-of-day, reporting
    charts/                 # Price, performance, exploratory
    ui/                     # Sidebar, tabs
```

---

## Known limitations

- **Yahoo 1m/2m** — ~7 day lookback; use 5m or 15m for longer history.
- **Failed breakout / Sweep reversal** — Modules exist but return no trades until logic is implemented.
- **Trailing targets** — Placeholder only.
- **Single symbol per run** — Change symbol and re-run for another contract.

---

## Enabling Databento

1. Get an API key from [Databento](https://databento.com).
2. `export DATABENTO_API_KEY=your_key`
3. Select **databento** in the sidebar and extend `src/data/databento.py` to fetch and normalize bars.

---

## License

For personal research and education. Not financial advice.
