# JARVIS for Trading

High-performance **NY Open Futures** research, signal, alerting, and execution-ready platform. Markets: **MNQ**, **NQ**, **MES**, **ES**. Session logic and display: **America/New_York**; frontend shows times in the user’s local timezone.

---

## Stack

| Layer | Tech |
|-------|------|
| Web | Next.js (App Router), React, TypeScript, Tailwind, Plotly.js |
| Engine | Rust, Axum, Tokio |
| Analytics | Polars, DuckDB, Parquet |
| Automation | n8n (webhooks) |

---

## Run locally

### 1. Engine (Rust)

```bash
cd engine
cp .env.example .env   # edit and add API keys
cargo run
```

API: **http://localhost:3001** (configurable via `PORT`).  
`GET /health` → `{"status":"ok","service":"jarvis-engine"}`.

### 2. Web app (when added)

```bash
cd web
cp .env.example .env.local
npm install && npm run dev
```

---

## Environment variables

**Engine (`engine/.env`)** — never commit; use `.env.example` as template.

| Variable | Required | Description |
|----------|----------|-------------|
| `PORT` | No | Server port (default `3001`) |
| `CACHE_DIR` | No | Parquet cache directory (default `data/cache`) |
| `POLYGON_API_KEY` | For Polygon | Polygon.io API key |
| `ALPHA_VANTAGE_API_KEY` | For Alpha Vantage | Alpha Vantage API key |
| `SESSION_TIMEZONE` | No | Session timezone (default `America/New_York`) |
| `OR_START` | No | Opening range start, e.g. `09:30` |
| `OR_END` | No | Opening range end, e.g. `10:00` |
| `TRADE_WINDOW_END` | No | Trade window end, e.g. `12:00` |

---

## Repo layout

```
ny-open-futures-terminal/
  engine/           # Rust API + session/OR logic
    src/
      main.rs       # Entrypoint
      config.rs     # Env config
      session.rs    # NY session, OR bounds (chrono-tz)
      api.rs        # Axum routes, CORS, /health
      data.rs       # Data adapters (stub)
      backtest.rs   # Backtest (stub)
      setup.rs      # Setup ranking / today matcher (stub)
      alert.rs      # Alert payloads / n8n (stub)
    .env.example
  data/cache/       # Parquet (gitignored)
  README.md
```

---

## 1. Biggest improvements made

- **Timezone correctness** — All session/OR math uses **chrono-tz** `America/New_York` (DST-safe). Session date: before 04:00 NY = previous calendar day. No more mixed CST/NY or fixed-offset hacks.
- **Single codebase** — All Python/Streamlit removed. One Rust engine, one future Next.js app; no duplicate session or OR logic.
- **Clarity** — Session and OR logic live in one small `session.rs`; `parse_hhmm` → `or_bounds_utc` / `trade_window_end_utc` are obvious and testable. API is a thin health check + CORS-ready for the web app.
- **Production hygiene** — `.env`/`.env.local` and API keys in gitignore; config from env only; release build with LTO and codegen-units=1.
- **Clean pipeline** — Clear separation: `config` → `session` → (future) `data` → `backtest` → `setup` → `alert`; stubs document where live data, backtest, setup ranking, and n8n hooks will plug in.

---

## 2. What’s still weak

- **Data layer** — `data.rs` is a stub. No Polygon/Alpha Vantage/Yahoo fetch, no Parquet write, no DuckDB. No OHLCV → no backtest or setup ranking yet.
- **Backtest & setup** — `backtest.rs` and `setup.rs` are stubs. No ORB (or other) execution, no metrics, no today-matcher, no ranking.
- **Alerts** — `alert.rs` is a stub. No PREP/WATCH/READY payloads, no n8n endpoint.
- **Frontend** — No `web/` yet. No Overview, Setup Finder, Backtests, Day Explorer, or local-time display.
- **Live pipeline** — No streaming ingestion, no in-memory session state, no real-time OR/VWAP/volume. Architecture is ready; implementation is not.

---

## 3. What to test first

1. **Engine build and health**  
   `cd engine && cargo build && cargo run` then `curl http://localhost:3001/health`. Confirms Rust stack and CORS/health.
2. **Session/OR timezone**  
   Unit tests (or a small binary) for `session_date_from_utc`, `or_bounds_utc`, and `trade_window_end_utc` on a few NY dates (including DST transition). Ensures 04:00 rollover and OR windows are correct.
3. **Env and secrets**  
   Ensure `engine/.env` is not committed and keys are read from env in config. Add `.env.example` with empty keys and document in README (done above).

After that: implement `data` (fetch + cache), then ORB in `backtest`, then setup ranking and today-matcher, then alerts and n8n, then the Next.js UI.

---

*For research and education. Not financial advice.*
