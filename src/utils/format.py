"""
Consistent number formatting for UI: currency, percentages, R multiples, integers.
"""
from __future__ import annotations


def format_currency(value: float | None, decimals: int = 2) -> str:
    """Format as dollar amount: $1,234.56 or $0.00."""
    if value is None:
        return "$0.00"
    return f"${value:,.{decimals}f}"


def format_pct(value: float | None, decimals: int = 1) -> str:
    """Format as percentage: 45.2%."""
    if value is None:
        return "—"
    return f"{value * 100:,.{decimals}f}%"


def format_r(value: float | None, decimals: int = 2) -> str:
    """Format as R multiple: 1.25R."""
    if value is None:
        return "—"
    return f"{value:,.{decimals}f}R"


def format_int(value: int | None) -> str:
    """Format integer with thousands commas: 1,234."""
    if value is None:
        return "—"
    return f"{value:,}"


def format_float(value: float | None, decimals: int = 2) -> str:
    """Format float with fixed decimals (no currency/unit)."""
    if value is None:
        return "—"
    return f"{value:,.{decimals}f}"
