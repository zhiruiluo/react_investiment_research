import pandas as pd

from react_investment_research.tools.market_snapshot import market_snapshot


class FakeProvider:
    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df

    def get_ohlcv(self, ticker: str, period: str, interval: str) -> pd.DataFrame:
        return self._df


def test_market_snapshot_computations() -> None:
    dates = pd.date_range("2026-01-01", periods=30, freq="D")
    close = pd.Series(range(100, 130), index=dates, dtype=float)
    df = pd.DataFrame(
        {
            "Open": close,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": pd.Series(range(1000, 1030), index=dates, dtype=float),
        }
    )

    provider = FakeProvider(df)
    result = market_snapshot("AAPL", "3mo", provider=provider)

    assert result["prices"]["start"] == 100.0
    assert result["prices"]["end"] == 129.0
    assert round(result["prices"]["return_pct"], 2) == 29.0
    assert round(result["risk"]["atr_14"], 2) == 2.0
    assert result["trend"]["trend_label"] in {"bullish", "sideways", "bearish"}
