from __future__ import annotations

from typing import Any, Dict, List, Optional

from .providers import YFinanceProvider

ALLOWLIST_FIELDS = {
    "marketCap",
    "trailingPE",
    "forwardPE",
    "trailingEps",
    "forwardEps",
    "priceToBook",
    "dividendYield",
    "profitMargins",
    "beta",
    "sector",
    "industry",
}


def fundamentals_events(
    ticker: str,
    fields: Optional[List[str]] = None,
    include_calendar: bool = True,
    lookback_days: int = 90,
    provider: Optional[YFinanceProvider] = None,
) -> Dict[str, Any]:
    provider = provider or YFinanceProvider()
    flags: List[str] = []
    try:
        info = provider.get_info(ticker)
        if include_calendar:
            try:
                calendar = provider.get_calendar(ticker)
            except Exception:
                calendar = {}
                flags.append("calendar_unavailable")
        else:
            calendar = {}
    except Exception:
        return {"error": "NO_DATA", "ticker": ticker, "reason": "invalid ticker or empty history"}

    if not info:
        return {"error": "NO_DATA", "ticker": ticker, "reason": "invalid ticker or empty history"}

    selected = sorted(ALLOWLIST_FIELDS) if not fields else fields
    fundamentals = {key: info.get(key) for key in selected if key in ALLOWLIST_FIELDS}

    return {
        "ticker": ticker,
        "asof": str(info.get("regularMarketTime", "")),
        "fundamentals": fundamentals,
        "calendar": calendar,
        "flags": flags,
    }
