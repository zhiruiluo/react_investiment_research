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


def sentiment_analysis(
    ticker: str,
    lookback_days: int = 30,
) -> Dict[str, Any]:
    """Return mock sentiment data for offline testing.
    
    Uses the built-in MOCK_SENTIMENT_DATA from the sentiment_analysis tool.
    """
    from .tools.sentiment_analysis import MOCK_SENTIMENT_DATA
    
    ticker = ticker.upper()
    if ticker not in MOCK_SENTIMENT_DATA:
        # Return neutral sentiment for unknown tickers
        return {
            "ticker": ticker,
            "asof": "2026-02-14",
            "overall_sentiment": 0.0,
            "components": {"news_sentiment": 0.0, "analyst_sentiment": 0.0},
            "metadata": {
                "news_articles_analyzed": 0,
                "analyst_ratings": {
                    "strong_buy": 0,
                    "buy": 0,
                    "hold": 0,
                    "sell": 0,
                    "strong_sell": 0,
                },
                "consensus": "no_data",
            },
            "trend": "neutral",
            "top_headlines": [],
            "lookback_days": lookback_days,
        }
    
    # Return mock data, adding the asof field
    mock_data = MOCK_SENTIMENT_DATA[ticker].copy()
    mock_data["ticker"] = ticker
    mock_data["asof"] = "2026-02-14"
    mock_data["lookback_days"] = lookback_days
    return mock_data
