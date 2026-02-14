from __future__ import annotations

from typing import Any, Dict

import pandas as pd
import yfinance as yf


class YFinanceProvider:
    def get_ohlcv(self, ticker: str, period: str, interval: str) -> pd.DataFrame:
        data = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
        )
        if data is None:
            return pd.DataFrame()
        return data.dropna()

    def get_info(self, ticker: str) -> Dict[str, Any]:
        info = yf.Ticker(ticker).info
        return info or {}

    def get_calendar(self, ticker: str) -> Dict[str, Any]:
        calendar = yf.Ticker(ticker).calendar
        if calendar is None:
            return {}
        if isinstance(calendar, dict):
            return calendar
        if hasattr(calendar, "empty") and calendar.empty:
            return {}
        if hasattr(calendar, "to_dict"):
            return calendar.to_dict()
        return {}
