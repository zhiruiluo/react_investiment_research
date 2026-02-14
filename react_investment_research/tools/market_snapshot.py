from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .providers import YFinanceProvider


def _trend_label(sma_20: float, sma_50: float) -> str:
    if sma_20 > sma_50 * 1.01:
        return "bullish"
    if sma_20 < sma_50 * 0.99:
        return "bearish"
    return "sideways"


def _compute_return_pct(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    start = float(series.iloc[0])
    end = float(series.iloc[-1])
    if start == 0:
        return 0.0
    return (end / start - 1.0) * 100.0


def market_snapshot(
    ticker: str,
    period: str,
    interval: str = "1d",
    benchmarks: Optional[List[str]] = None,
    provider: Optional[YFinanceProvider] = None,
) -> Dict[str, Any]:
    provider = provider or YFinanceProvider()
    try:
        df = provider.get_ohlcv(ticker, period, interval)
    except Exception:
        df = pd.DataFrame()

    if df is None or df.empty:
        return {"error": "NO_DATA", "ticker": ticker, "reason": "invalid ticker or empty history"}

    try:
        close = pd.to_numeric(df["Close"].squeeze(), errors="coerce").dropna()
        high = pd.to_numeric(df["High"].squeeze(), errors="coerce").dropna()
        low = pd.to_numeric(df["Low"].squeeze(), errors="coerce").dropna()
        volume = pd.to_numeric(df["Volume"].squeeze(), errors="coerce").dropna()
    except Exception:
        return {"error": "NO_DATA", "ticker": ticker, "reason": "data parsing failed"}

    if close.empty or high.empty or low.empty or volume.empty:
        return {"error": "NO_DATA", "ticker": ticker, "reason": "insufficient data after parsing"}

    start = float(close.iloc[0])
    end = float(close.iloc[-1])
    return_pct = _compute_return_pct(close)

    cummax = close.cummax()
    drawdowns = (close / cummax - 1.0) * 100.0
    max_drawdown_pct = float(drawdowns.min())

    returns = close.pct_change().dropna()
    volatility_ann_pct = float(returns.std() * np.sqrt(252) * 100.0) if not returns.empty else 0.0

    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr_14 = float(tr.rolling(14).mean().iloc[-1]) if len(tr) >= 14 else float(tr.mean())

    sma_20 = float(close.rolling(20).mean().iloc[-1]) if len(close) >= 20 else float(close.mean())
    sma_50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else float(close.mean())
    trend_label = _trend_label(sma_20, sma_50)

    avg_20d = float(volume.rolling(20).mean().iloc[-1]) if len(volume) >= 20 else float(volume.mean())
    latest_vol = float(volume.iloc[-1])
    vol_window = volume.tail(20)
    vol_std = float(vol_window.std()) if len(vol_window) >= 2 else 0.0
    zscore_latest = float((latest_vol - vol_window.mean()) / vol_std) if vol_std else 0.0

    relative: List[Dict[str, Any]] = []
    if benchmarks:
        for bench in benchmarks:
            try:
                bench_df = provider.get_ohlcv(bench, period, interval)
                if bench_df is None or bench_df.empty:
                    continue
                bench_return = _compute_return_pct(bench_df["Close"].astype(float))
                relative.append({"ticker": bench, "return_pct": bench_return})
            except Exception:
                continue

    asof = df.index[-1].date().isoformat() if hasattr(df.index[-1], "date") else str(df.index[-1])

    return {
        "ticker": ticker,
        "asof": asof,
        "period": period,
        "interval": interval,
        "prices": {
            "start": start,
            "end": end,
            "return_pct": return_pct,
            "max_drawdown_pct": max_drawdown_pct,
        },
        "risk": {"volatility_ann_pct": volatility_ann_pct, "atr_14": atr_14},
        "trend": {"sma_20": sma_20, "sma_50": sma_50, "trend_label": trend_label},
        "volume": {"avg_20d": avg_20d, "latest": latest_vol, "zscore_latest": zscore_latest},
        "relative": relative,
        "notes": [],
    }
