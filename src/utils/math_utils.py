"""Math and rounding helpers."""
from __future__ import annotations


def round_to_tick(price: float, tick_size: float) -> float:
    """Round price to nearest tick."""
    if tick_size <= 0:
        return price
    return round(price / tick_size) * tick_size


def r_multiple(entry: float, exit_price: float, stop: float, direction: str) -> float | None:
    """
    Compute R multiple: (exit - entry) / (entry - stop) for long,
    (entry - exit) / (stop - entry) for short. Returns None if risk is zero.
    """
    if direction == "long":
        risk = entry - stop
        pnl = exit_price - entry
    else:
        risk = stop - entry
        pnl = entry - exit_price
    if risk <= 0:
        return None
    return pnl / risk


def mae_mfe(entry: float, stop: float, target: float, highs: list[float], lows: list[float], direction: str) -> tuple[float, float]:
    """
    Given entry, stop, target and series of high/low after entry,
    return (MAE, MFE) in points. MAE = max adverse excursion, MFE = max favorable.
    """
    mae = 0.0
    mfe = 0.0
    for h, l in zip(highs, lows):
        if direction == "long":
            adverse = min(l) - entry if isinstance(l, (list, tuple)) else l - entry
            favorable = (max(h) if isinstance(h, (list, tuple)) else h) - entry
        else:
            adverse = entry - (max(h) if isinstance(h, (list, tuple)) else h)
            favorable = entry - (min(l) if isinstance(l, (list, tuple)) else l)
        mae = min(mae, adverse)
        mfe = max(mfe, favorable)
    return mae, mfe
