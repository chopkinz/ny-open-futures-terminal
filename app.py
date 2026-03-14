"""
NY Open Futures Terminal — Streamlit app entrypoint.

Modular layout; user-friendly errors; ready for future live execution,
broker APIs, and strategy alerts (extend data layer and execution layer).
"""
from __future__ import annotations

import pandas as pd  # pyright: ignore[reportMissingImports]
import streamlit as st  # pyright: ignore[reportMissingImports]

from src.analytics.structure import compute_opening_ranges
from src.analytics.patterns import compute_best_patterns, compute_entry_time_pattern
from src.backtest.engine import run_backtest
from src.backtest.metrics import compute_performance
from src.backtest.optimizer import optimize_r
from src.config import build_data_config, build_session_config, build_strategy_config
from src.data.loaders import load_ohlcv
from src.sessions.engine import SessionEngine
from src.ui.sidebar import render_sidebar
from src.ui.overview import render_data_and_log, render_overview
from src.ui.backtest_tab import render_backtest_tab
from src.ui.structure_tab import render_structure_tab
from src.ui.time_tab import render_time_tab
from src.ui.explorer_tab import render_explorer_tab
from src.ui.trade_log_tab import render_trade_log_tab
from src.ui.diagnostics_tab import render_diagnostics_tab
from src.utils.time import get_local_tz


def _display_tz_from_key(key: str):
    if key == "Local":
        return get_local_tz()
    import pytz  # pyright: ignore[reportMissingModuleSource]
    return pytz.timezone(key)


def _empty_perf(symbol: str):
    return compute_performance([], symbol)


def _friendly_error(e: Exception) -> str:
    """Turn exceptions into short, user-friendly messages."""
    msg = str(e).strip()
    if "yfinance" in msg.lower() or "yahoo" in msg.lower():
        return "Data fetch failed. Try a shorter lookback or 5m/15m interval (Yahoo 1m/2m have limited history)."
    if "parquet" in msg.lower() or "cache" in msg.lower():
        return "Cache read/write failed. Try refreshing cache or check disk space."
    if "timezone" in msg.lower() or "tz" in msg.lower():
        return "Timezone error in data. Check that the data source returns timezone-aware timestamps."
    if "column" in msg.lower() or "key" in msg.lower():
        return "Data format issue: required OHLCV columns missing or invalid."
    if len(msg) > 120:
        return msg[:117] + "..."
    return msg or "An unexpected error occurred."


st.set_page_config(
    page_title="NY Open Futures Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Clean light theme: white and blue
st.markdown("""
<style>
  .terminal-header {
    font-size: 1.75rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #0f172a;
    margin-bottom: 0.25rem;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 0.75rem;
  }
  .terminal-caption {
    font-size: 0.875rem;
    color: #64748b;
    margin-bottom: 1.75rem;
    line-height: 1.5;
  }
  .session-badge {
    display: inline-block;
    font-size: 0.7rem;
    color: #2563eb;
    background: #eff6ff;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    margin-top: 0.35rem;
  }
  .section-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: #1e293b;
    margin: 1.5rem 0 0.75rem 0;
    letter-spacing: 0.01em;
  }
  .section-title:first-of-type { margin-top: 0; }
  .metric-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; }
  div[data-testid="stMetric"] { background: #f8fafc; padding: 0.75rem 1rem; border-radius: 6px; border: 1px solid #e2e8f0; }
  div[data-testid="stMetric"] label { color: #64748b !important; font-size: 0.8rem !important; }
  .stTabs [data-baseweb="tab-list"] { gap: 0.5rem; }
  .stTabs [data-baseweb="tab"] { padding: 0.5rem 1rem; font-size: 0.9rem; }
  .block-container { padding-top: 1.5rem; padding-bottom: 3rem; }
  [data-testid="stSidebar"] .stMarkdown { margin-bottom: 0.25rem; }
  [data-testid="stSidebar"] hr { margin: 0.75rem 0; }
  [data-testid="stSidebar"] { background: #f8fafc; }
</style>
""", unsafe_allow_html=True)

data_config, session_config, strategy_config, run_clicked, display_tz_key, auto_optimize, optimize_metric, balance, risk_pct = render_sidebar()
display_tz = _display_tz_from_key(display_tz_key)

st.markdown('<p class="terminal-header">NY Open Futures</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="terminal-caption">Your trade plan from the data — pick symbol & days, run analysis, then follow the plan below. '
    f'<span class="session-badge">Times: {display_tz_key}</span></p>',
    unsafe_allow_html=True,
)

# Session state
if "df" not in st.session_state:
    st.session_state.df = None
if "or_map" not in st.session_state:
    st.session_state.or_map = {}
if "trades" not in st.session_state:
    st.session_state.trades = []
if "perf" not in st.session_state:
    st.session_state.perf = None
if "optimized_r" not in st.session_state:
    st.session_state.optimized_r = None
if "analysis_log" not in st.session_state:
    st.session_state.analysis_log = []

if run_clicked:
    st.session_state.analysis_log = []
    with st.spinner("Loading data…"):
        try:
            st.session_state.df = load_ohlcv(data_config)
            _df = st.session_state.df
            if _df is not None and not _df.empty:
                n_bars = len(_df)
                first_ts = _df.index.min()
                last_ts = _df.index.max()
                sym = data_config.symbol.replace("=F", "")
                st.session_state.analysis_log.append({
                    "step": "Data loaded",
                    "detail": f"{data_config.source.value} · {sym} · {data_config.interval} · {n_bars:,} bars · {first_ts} → {last_ts}",
                })
        except Exception as e:
            st.sidebar.error(_friendly_error(e))
            st.session_state.df = None
            st.session_state.analysis_log.append({"step": "Data load failed", "detail": str(e)[:200]})

    if st.session_state.df is not None and not st.session_state.df.empty:
        try:
            engine = SessionEngine(session_config)
            st.session_state.or_map = compute_opening_ranges(st.session_state.df, engine)
            n_sessions = len(st.session_state.or_map)
            st.session_state.analysis_log.append({
                "step": "Opening ranges",
                "detail": f"Computed OR for {n_sessions} session(s).",
            })
            if auto_optimize:
                with st.spinner("Optimizing SL/TP and running backtest…"):
                    opt_result = optimize_r(
                        st.session_state.df,
                        data_config,
                        session_config,
                        strategy_config,
                        r_min=0.5,
                        r_max=2.5,
                        r_step=0.25,
                        metric=optimize_metric,
                    )
                    if opt_result and opt_result.best_trades:
                        st.session_state.trades = opt_result.best_trades
                        st.session_state.perf = opt_result.best_perf
                        st.session_state.optimized_r = opt_result.best_r
                        st.session_state.analysis_log.append({
                            "step": "Backtest + optimization",
                            "detail": f"{len(opt_result.best_trades)} trades · best target {opt_result.best_r}R "
                            f"(expectancy {opt_result.best_perf.expectancy_r:.2f}R, win rate {opt_result.best_perf.win_rate*100:.0f}%).",
                        })
                        if optimize_metric == "win_rate":
                            st.sidebar.success(
                                f"Analysis complete. Best target: **{opt_result.best_r}R** "
                                f"(win rate {opt_result.best_perf.win_rate*100:.0f}%)"
                            )
                        else:
                            st.sidebar.success(
                                f"Analysis complete. Optimized for highest $ per trade: **{opt_result.best_r}R** "
                                f"(expectancy {opt_result.best_perf.expectancy_r:.2f}R)"
                            )
                    else:
                        st.session_state.trades, st.session_state.perf = run_backtest(
                            st.session_state.df, data_config, session_config, strategy_config
                        )
                        st.session_state.optimized_r = None
                        st.session_state.analysis_log.append({
                            "step": "Backtest",
                            "detail": f"{len(st.session_state.trades)} trades (optimization skipped; using your R).",
                        })
                        st.sidebar.success("Analysis complete. (Optimization had too few trades; used your R.)")
            else:
                with st.spinner("Running backtest…"):
                    st.session_state.trades, st.session_state.perf = run_backtest(
                        st.session_state.df, data_config, session_config, strategy_config
                    )
                st.session_state.optimized_r = None
                st.session_state.analysis_log.append({
                    "step": "Backtest",
                    "detail": f"{len(st.session_state.trades)} trades.",
                })
                st.sidebar.success("Analysis complete.")
        except Exception as e:
            st.sidebar.error("Backtest failed: " + _friendly_error(e))
            st.session_state.or_map = {}
            st.session_state.trades = []
            st.session_state.perf = _empty_perf(data_config.symbol)
            st.session_state.optimized_r = None
            st.session_state.analysis_log.append({"step": "Backtest failed", "detail": str(e)[:200]})
    elif st.session_state.df is not None and st.session_state.df.empty:
        st.sidebar.warning(
            "No data returned. Yahoo 1m/2m are limited to ~7 days; use 5m or 15m for longer history."
        )

df = st.session_state.df
or_map = st.session_state.or_map
trades = st.session_state.trades
perf = st.session_state.perf
optimized_r = st.session_state.get("optimized_r")

if perf is None:
    perf = _empty_perf(data_config.symbol)

entry_time_pattern = compute_entry_time_pattern(perf.trades) if perf and perf.trades else None
best_patterns = compute_best_patterns(perf.trades) if perf and perf.trades else []

# Data we analyzed + analysis log (real-time visualization)
if df is not None and not df.empty:
    render_data_and_log(
        df,
        st.session_state.get("analysis_log", []),
        data_config.symbol,
        data_config.source.value,
        data_config.interval,
        display_tz,
    )

# Single main view: your plan first, then details in an expander
render_overview(perf, strategy_config, session_config, display_tz_key, optimized_r, entry_time_pattern, best_patterns, optimize_metric, data_config.symbol, or_map=or_map, lookback_days=data_config.lookback_days, balance=balance, risk_pct=risk_pct, display_tz=display_tz)

with st.expander("More: backtest details, trade log, charts & diagnostics", expanded=False):
    tab_backtest, tab_structure, tab_time, tab_explorer, tab_log, tab_diag = st.tabs([
        "Backtest",
        "Structure",
        "Time-of-Day",
        "Day Explorer",
        "Trade Log",
        "Diagnostics",
    ])
    with tab_backtest:
        render_backtest_tab(perf, display_tz)
    with tab_structure:
        render_structure_tab(perf, or_map)
    with tab_time:
        render_time_tab(perf)
    with tab_explorer:
        engine = SessionEngine(session_config)
        render_explorer_tab(
            df if df is not None else pd.DataFrame(),
            or_map,
            trades,
            engine,
            display_tz,
        )
    with tab_log:
        render_trade_log_tab(trades, display_tz)
    with tab_diag:
        render_diagnostics_tab(
            df if df is not None and not df.empty else pd.DataFrame(),
            data_config.source.value,
            data_config.cache_dir,
            data_config.symbol,
            data_config.interval,
            display_tz,
        )
