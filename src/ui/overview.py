"""Overview tab: headline metrics, trade plan from patterns, equity curve, drawdown."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import pandas as pd  # pyright: ignore[reportMissingImports]
import streamlit as st  # pyright: ignore[reportMissingImports]

from src.charts.performance import plot_drawdown, plot_equity_curve
from src.charts.price import plot_data_preview
from src.models import PerformanceSummary
from src.utils.format import format_currency, format_pct, format_r
from src.utils.time import format_time_12h

if TYPE_CHECKING:
    from src.analytics.patterns import BestPattern, EntryTimePattern
    from src.models import SessionConfig, StrategyConfig


def render_data_and_log(
    df: pd.DataFrame,
    analysis_log: list[dict[str, Any]],
    symbol: str,
    source: str,
    interval: str,
    display_tz: Optional[object] = None,
) -> None:
    """Show the actual data we analyzed (Yahoo etc.) and the analysis pipeline log."""
    if df is None or df.empty:
        return
    sym = symbol.replace("=F", "")
    n_bars = len(df)
    first_ts = df.index.min()
    last_ts = df.index.max()
    try:
        first_str = first_ts.strftime("%b %d, %Y %I:%M %p") if hasattr(first_ts, "strftime") else str(first_ts)
        last_str = last_ts.strftime("%b %d, %Y %I:%M %p") if hasattr(last_ts, "strftime") else str(last_ts)
    except Exception:
        first_str = str(first_ts)
        last_str = str(last_ts)
    source_label = "Yahoo" if (source or "").lower() == "yahoo" else (source or "").replace("_", " ").title()
    with st.expander("Data we analyzed · real-time log", expanded=True):
        st.markdown(f"**{source_label}** · **{sym}** · **{interval}** · **{n_bars:,}** bars · {first_str} → {last_str}")
        # Export ticker data for this timeframe/symbol
        export_df = df.copy()
        export_df.index.name = "timestamp"
        export_df = export_df.reset_index()
        try:
            date_start = pd.Timestamp(first_ts).strftime("%Y-%m-%d")
            date_end = pd.Timestamp(last_ts).strftime("%Y-%m-%d")
        except Exception:
            date_start = "start"
            date_end = "end"
        csv_filename = f"{sym}_{interval}_{date_start}_to_{date_end}.csv"
        csv_bytes = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Export ticker data (CSV)",
            data=csv_bytes,
            file_name=csv_filename,
            mime="text/csv",
            key="export_ticker_data",
        )
        st.plotly_chart(
            plot_data_preview(df, "Price (close) — data used for this run"),
            use_container_width=True,
        )
        st.markdown("**Analysis log**")
        for i, entry in enumerate(analysis_log):
            step = entry.get("step", "")
            detail = entry.get("detail", "")
            st.markdown(f"`{i + 1}. {step}` — {detail}")
    st.markdown("")


def render_overview(
    perf: PerformanceSummary,
    strategy_config: "StrategyConfig",
    session_config: "SessionConfig",
    display_tz_key: str,
    optimized_r: Optional[float],
    entry_time_pattern: Optional["EntryTimePattern"],
    best_patterns: list["BestPattern"],
    optimize_metric: str = "win_rate",
    symbol: str = "MNQ=F",
    or_map: Optional[dict] = None,
    lookback_days: int = 90,
    balance: float = 50000.0,
    risk_pct: float = 1.0,
    display_tz: Optional[object] = None,
) -> None:
    if perf.total_trades == 0:
        st.info("**Get started:** Choose symbol and lookback in the sidebar → click **Run analysis**. Your trade plan and stats will appear here.")
        return

    # Plan first — answer "what do I do?"
    _render_trade_plan(perf, strategy_config, session_config, display_tz_key, optimized_r, entry_time_pattern, best_patterns, optimize_metric, symbol, or_map=or_map, lookback_days=lookback_days, balance=balance, risk_pct=risk_pct, display_tz=display_tz)
    st.markdown("---")
    st.markdown("#### How this plan has performed")
    st.markdown("")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Trades", f"{perf.total_trades:,}")
    with c2:
        st.metric("Win rate", format_pct(perf.win_rate))
    with c3:
        st.metric("Expectancy", format_r(perf.expectancy_r))
    with c4:
        pf = perf.profit_factor
        st.metric("Profit factor", f"{pf:.2f}" if pf != float("inf") else "∞")
    with c5:
        net_pnl = perf.gross_profit - perf.gross_loss
        st.metric("Net PnL", format_currency(net_pnl, 0))
    st.markdown("")
    _render_period_breakdown(perf.trades, symbol)
    st.markdown("")
    st.markdown("#### Equity & drawdown")
    st.markdown("")
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(plot_equity_curve(perf.trades, "Equity curve"), use_container_width=True)
    with col_b:
        st.plotly_chart(plot_drawdown(perf.trades, "Drawdown"), use_container_width=True)


def _get_tick_size(symbol: str) -> float:
    """Tick size for symbol (e.g. MNQ=F -> 0.25)."""
    from src.config import get_contract_specs
    root = symbol.replace("=F", "").strip()
    specs = get_contract_specs()
    if root in specs:
        return float(specs[root].get("tick_size", 0.25))
    for key, spec in specs.items():
        if key in symbol or symbol.startswith(key):
            return float(spec.get("tick_size", 0.25))
    return 0.25


def _confidence(perf: PerformanceSummary) -> tuple[str, str]:
    """Return (level, reason) e.g. ('High', '72% win rate, 45 trades')."""
    n = perf.total_trades
    wr = perf.win_rate
    if n >= 20 and wr >= 0.55:
        return "High", f"{wr*100:.0f}% win rate, {n} trades in sample"
    if n >= 10 or (n >= 5 and wr >= 0.45):
        return "Medium", f"{wr*100:.0f}% win rate, {n} trades — run more data for higher confidence"
    if n >= 1:
        return "Low", f"Only {n} trade(s) — add more days of data for reliable estimates"
    return "—", "No trades yet"


def _render_period_breakdown(trades: list, symbol: str) -> None:
    """Render trades per day / week / month and profit per day / week / month."""
    from src.backtest.metrics import compute_period_breakdown
    breakdown = compute_period_breakdown(trades, symbol)
    daily = breakdown["daily"]
    weekly = breakdown["weekly"]
    monthly = breakdown["monthly"]
    summary = breakdown.get("summary") or {}
    if not daily and not weekly and not monthly:
        return
    st.markdown("#### Breakdown by period")
    st.markdown("")
    # Summary row: avg per day, per week, per month; best/worst day
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown("**Per day**")
        if "avg_trades_per_day" in summary:
            st.metric("Avg trades/day", f"{summary['avg_trades_per_day']:.2f}")
        if "avg_pnl_per_day" in summary:
            st.metric("Avg PnL/day", format_currency(summary["avg_pnl_per_day"], 0))
        if "total_days_with_trades" in summary:
            st.caption(f"{summary['total_days_with_trades']} days with trades")
    with s2:
        st.markdown("**Per week**")
        if "avg_trades_per_week" in summary:
            st.metric("Avg trades/week", f"{summary['avg_trades_per_week']:.2f}")
        if "avg_pnl_per_week" in summary:
            st.metric("Avg PnL/week", format_currency(summary["avg_pnl_per_week"], 0))
        if "total_weeks_with_trades" in summary:
            st.caption(f"{summary['total_weeks_with_trades']} weeks with trades")
    with s3:
        st.markdown("**Per month**")
        if "avg_trades_per_month" in summary:
            st.metric("Avg trades/month", f"{summary['avg_trades_per_month']:.2f}")
        if "avg_pnl_per_month" in summary:
            st.metric("Avg PnL/month", format_currency(summary["avg_pnl_per_month"], 0))
        if "total_months_with_trades" in summary:
            st.caption(f"{summary['total_months_with_trades']} months with trades")
    with s4:
        st.markdown("**Best / worst day**")
        if "best_day" in summary:
            d, pnl = summary["best_day"]
            st.metric("Best day", format_currency(pnl, 0))
            st.caption(d)
        if "worst_day" in summary:
            d, pnl = summary["worst_day"]
            st.metric("Worst day", format_currency(pnl, 0))
            st.caption(d)
    st.markdown("")
    # Tables: daily, weekly, monthly
    def _table(rows: list) -> None:
        if not rows:
            return
        df = pd.DataFrame(rows)
        df = df.rename(columns={
            "period_label": "Period",
            "trades": "Trades",
            "pnl": "PnL",
            "wins": "Wins",
            "losses": "Losses",
            "win_rate": "Win %",
        })
        df["PnL"] = df["PnL"].apply(lambda x: format_currency(x, 0))
        df["Win %"] = df["Win %"].apply(lambda x: format_pct(x))
        cols = ["Period", "Trades", "PnL", "Wins", "Losses", "Win %"]
        df = df[[c for c in cols if c in df.columns]]
        st.dataframe(df, use_container_width=True, height=min(220, 60 + len(df) * 38))

    st.markdown("**Per day**")
    _table(daily)
    st.markdown("")
    st.markdown("**Per week**")
    _table(weekly)
    st.markdown("")
    st.markdown("**Per month**")
    _table(monthly)
    st.markdown("")


def _render_trade_plan(
    perf: PerformanceSummary,
    strategy_config: "StrategyConfig",
    session_config: "SessionConfig",
    display_tz_key: str,
    optimized_r: Optional[float],
    entry_time_pattern: Optional["EntryTimePattern"],
    best_patterns: list["BestPattern"],
    optimize_metric: str,
    symbol: str = "MNQ=F",
    or_map: Optional[dict] = None,
    lookback_days: int = 90,
    balance: float = 50000.0,
    risk_pct: float = 1.0,
    display_tz: Optional[object] = None,
) -> None:
    """Exact trade plan from pattern: entry time, SL, target, next session."""
    from src.analytics.patterns import format_entry_window
    from src.backtest.metrics import pnl_dollars
    from src.utils.time import format_timestamp_12h as fmt_ts

    st.markdown("#### Your trade plan")
    st.markdown("")
    target_r = optimized_r if optimized_r is not None else strategy_config.r_multiple
    st.markdown("**In one line:** Wait for the opening range → take the **first break** after OR close (morning breakout, when volume is typically highest) → long on close above OR high, short on close below OR low → SL at opposite OR side, target " + f"{target_r}R → one trade per day.")
    if optimized_r is not None:
        if optimize_metric == "win_rate":
            st.caption("Optimized for **highest win rate** the data allows (closest to 100%).")
        else:
            st.caption("Optimized for **highest $ per trade** (best target R from your data).")
    st.markdown("")

    # Your numbers: risk, expected profit, confidence
    risk_per_trade = balance * (risk_pct / 100.0)
    expected_profit_per_trade = perf.expectancy_r * risk_per_trade
    months_of_data = lookback_days / 30.0 if lookback_days else 1.0
    trades_per_month = perf.total_trades / months_of_data if months_of_data else 0
    expected_profit_30d = expected_profit_per_trade * trades_per_month
    conf_level, conf_reason = _confidence(perf)
    st.markdown("**Your numbers** (from your balance and this plan)")
    st.caption("Backtest includes *all* trades (wins and losses) so you see true risk. With **Auto-optimize** on we pick the target R that maximizes profit per trade when there’s enough data.")
    st.markdown("")
    r1, r2, r3, r4, r5 = st.columns(5)
    with r1:
        st.metric("Risk per trade", format_currency(risk_per_trade, 0))
    with r2:
        st.metric("Expected $ per trade", format_currency(expected_profit_per_trade, 0))
    with r3:
        st.metric("Trades/month (est.)", f"{trades_per_month:.1f}")
    with r4:
        st.metric("Expected profit (30d)", format_currency(expected_profit_30d, 0))
    with r5:
        st.metric("Confidence", conf_level)
    st.caption(conf_reason)
    st.markdown("")

    # Evidence of analysis: timestamps and exact prices (not vague)
    sessions_with_or = len(or_map) if or_map else 0
    unique_days = sorted(set(t.trade_date for t in perf.trades if t.trade_date))
    long_count = sum(1 for t in perf.trades if t.direction == "long")
    short_count = sum(1 for t in perf.trades if t.direction == "short")
    st.markdown("**Evidence of analysis**")
    st.markdown("")
    st.markdown(f"Sessions with OR data: **{sessions_with_or:,}** (last {lookback_days} days). Setup triggered **{perf.total_trades:,}** times on **{len(unique_days):,}** days (Long: {long_count}, Short: {short_count}). All entries are on the **morning breakout** (first break after OR), when volume is typically highest.")
    st.markdown("")
    st.markdown("**Exact trades — timestamps and prices:**")
    st.markdown("")
    tz = display_tz
    rows = []
    has_volume = any(getattr(t, "volume_at_entry", None) is not None for t in perf.trades)
    for t in perf.trades:
        entry_ts_str = fmt_ts(t.entry_ts, tz) if t.entry_ts else "—"
        exit_ts_str = fmt_ts(t.exit_ts, tz) if t.exit_ts else "—"
        entry_p = f"{t.entry_price:,.2f}" if t.entry_price is not None else "—"
        stop_p = f"{t.stop_price:,.2f}" if t.stop_price is not None else "—"
        target_p = f"{t.target_price:,.2f}" if t.target_price is not None else "—"
        exit_p = f"{t.exit_price:,.2f}" if t.exit_price is not None else "—"
        r_str = f"{t.r_multiple:,.2f}R" if t.r_multiple is not None else "—"
        pnl_d = pnl_dollars(t)
        pnl_str = format_currency(pnl_d, 0) if pnl_d is not None else "—"
        vol_at_entry = getattr(t, "volume_at_entry", None)
        vol_str = f"{int(vol_at_entry):,}" if vol_at_entry is not None and vol_at_entry else "—"
        row = {
            "Date": t.trade_date or "—",
            "Entry time": entry_ts_str,
            "Direction": t.direction.upper(),
            "Entry": entry_p,
            "Stop": stop_p,
            "Target": target_p,
            "Exit time": exit_ts_str,
            "Exit": exit_p,
            "R": r_str,
            "PnL": pnl_str,
        }
        if has_volume:
            row["Volume"] = vol_str
        rows.append(row)
    import pandas as pd
    evidence_df = pd.DataFrame(rows)
    st.dataframe(evidence_df, use_container_width=True, height=min(400, 60 + len(rows) * 38))
    st.markdown("")

    # Best patterns: highest win rate & profit potential
    if best_patterns:
        st.markdown("**Patterns with the most profit potential (highest win rate)**")
        st.markdown("")
        # Show top 3–4: direction + time window when available, win rate, avg R
        from src.utils.format import format_pct, format_r
        for p in best_patterns[:4]:
            dir_label = p.direction.capitalize()
            if p.time_start_minutes is not None and p.time_end_minutes is not None:
                window = f" {format_entry_window(p.time_start_minutes)}–{format_entry_window(p.time_end_minutes)}"
            else:
                window = ""
            st.markdown(f"- **{dir_label}{window}:** {format_pct(p.win_rate)} win rate, {format_r(p.avg_r)} avg · {p.count} trades")
        st.markdown("")
    or_start_12 = format_time_12h(session_config.or_start)
    or_end_12 = format_time_12h(session_config.or_end)
    trade_end_12 = format_time_12h(session_config.trade_window_end)
    session_tz_label = "CST" if "Chicago" in session_config.timezone else ("NY" if "New_York" in session_config.timezone else session_config.timezone.split("/")[-1][:3].upper())

    st.markdown("**What the data says** — From **price data analysis** and **historical market structure**: use the opening range (OR) and the **morning breakout** (first break after OR), when volume is typically highest:")
    st.markdown("")
    plan = [
        f"**OR window:** {or_start_12} – {or_end_12} ({session_tz_label}). Don’t trade during this; let the range form.",
        f"**Entry:** First *close* beyond OR high (long) or OR low (short) after {or_end_12} — the **morning breakout**, when volume is usually highest. Trade the first break only.",
        "**Stop loss:** Opposite OR side — long SL at OR low, short SL at OR high. (Auto from the range.)",
        f"**Target:** {target_r}R (risk multiple). "
        + ("Optimized for highest $ per trade." if optimize_metric == "expectancy_r" and optimized_r is not None else "Optimized for highest win rate." if optimize_metric == "win_rate" and optimized_r is not None else "Optimized from backtest." if optimized_r is not None else "From your setting."),
        f"**Trade window:** After {or_end_12} until {trade_end_12} (morning breakout period).",
    ]
    for line in plan:
        st.markdown(f"- {line}")
    st.markdown("")

    if entry_time_pattern and entry_time_pattern.trade_count >= 5:
        start_str = format_entry_window(entry_time_pattern.typical_start_minutes)
        end_str = format_entry_window(entry_time_pattern.typical_end_minutes)
        typical_window = f"**{start_str}** – **{end_str}** ({session_tz_label})"
    else:
        typical_window = f"Shortly after **{or_end_12}**"

    st.markdown("**Suggested trades** — During the **morning breakout** (first break after OR, when volume is typically highest). Based on **price data analysis** and **historical market structure**. Use these as literal order form entries (one trade per day; place both, first to trigger fills):")
    st.markdown("")
    tick_size = _get_tick_size(symbol)
    sym_display = symbol.replace("=F", "")
    col_long, col_short = st.columns(2)
    with col_long:
        st.markdown("##### Order form — LONG")
        st.markdown(
            "| Field | Entry |\n"
            "|-------|-------|\n"
            "| **Order type** | Buy stop |\n"
            f"| **Symbol** | {sym_display} |\n"
            "| **Quantity** | 1 |\n"
            f"| **Trigger price** | OR high + {tick_size} (1 tick above OR high) |\n"
            "| **Stop loss order** | Sell stop @ OR low |\n"
            f"| **Target order** | Sell limit @ entry + (risk × {target_r}R) |\n"
            f"| **Typical time** | {typical_window} (morning breakout, highest volume) |"
        )
    with col_short:
        st.markdown("##### Order form — SHORT")
        st.markdown(
            "| Field | Entry |\n"
            "|-------|-------|\n"
            "| **Order type** | Sell stop |\n"
            f"| **Symbol** | {sym_display} |\n"
            "| **Quantity** | 1 |\n"
            f"| **Trigger price** | OR low − {tick_size} (1 tick below OR low) |\n"
            "| **Stop loss order** | Buy stop @ OR high |\n"
            f"| **Target order** | Buy limit @ entry − (risk × {target_r}R) |\n"
            f"| **Typical time** | {typical_window} (morning breakout, highest volume) |"
        )
    st.markdown("")
    st.markdown("**Example in ticks** (" + f"{symbol.replace('=F', '')}, tick = {tick_size}):")
    st.markdown("")
    example_or_high = 21250.0
    example_or_low = 21245.0
    example_buy_stop = example_or_high + tick_size
    example_sell_stop_short = example_or_low - tick_size
    risk_pts = example_buy_stop - example_or_low
    target_pts = risk_pts * target_r
    example_sell_limit = example_buy_stop + target_pts
    example_buy_limit = example_sell_stop_short - target_pts
    st.markdown(f"- **Long:** Buy stop @ **{example_buy_stop:,.2f}** (OR high {example_or_high:,.2f} + 1 tick). Sell stop @ **{example_or_low:,.2f}** (OR low). Risk = {risk_pts:.2f} pts. Sell limit @ **{example_sell_limit:,.2f}** (entry + {target_r}R).")
    st.markdown(f"- **Short:** Sell stop @ **{example_sell_stop_short:,.2f}** (OR low {example_or_low:,.2f} − 1 tick). Buy stop @ **{example_or_high:,.2f}** (OR high). Risk = {risk_pts:.2f} pts. Buy limit @ **{example_buy_limit:,.2f}** (entry − {target_r}R).")
    st.markdown("")
    st.caption("See **Day Explorer** (under More) for a chart with OR levels, entry, stop, and target for any session.")
    st.markdown("")

    st.markdown("**Runner & follow-up**")
    st.markdown("- Let the trade run to target or stop; no add-ons in this system.")
    st.markdown("- If stopped out, do not reverse into the other break same day (one trade per day).")
    st.markdown("- Optional: trail stop to breakeven after 1R in profit (not in backtest).")
    st.markdown("")

    st.markdown("**Next session** — Wait for OR to print (" + f"{or_start_12}–{or_end_12} {session_tz_label}). Take the **first break** (morning breakout, when volume is highest) — long or short — with SL opposite OR side, target {target_r}R. One trade per day.")
