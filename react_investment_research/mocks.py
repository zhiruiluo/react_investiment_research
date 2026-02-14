from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from importlib import resources


def _load_json(name: str) -> Dict[str, Any] | None:
    try:
        path = resources.files("react_investment_research.data.mocks").joinpath(name)
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return None


def market_snapshot(
    ticker: str,
    period: str,
    interval: str = "1d",
    benchmarks: Optional[List[str]] = None,
) -> Dict[str, Any]:
    name = f"market_snapshot_{ticker.upper()}_{period}.json"
    payload = _load_json(name)
    if payload is None:
        return {"error": "NO_DATA", "ticker": ticker, "reason": "mock not found"}
    return payload


def fundamentals_events(
    ticker: str,
    fields: Optional[List[str]] = None,
    include_calendar: bool = True,
    lookback_days: int = 90,
) -> Dict[str, Any]:
    name = f"fundamentals_events_{ticker.upper()}.json"
    payload = _load_json(name)
    if payload is None:
        return {"error": "NO_DATA", "ticker": ticker, "reason": "mock not found"}
    return payload
