import pandas as pd

from react_investment_research.tools.market_snapshot import market_snapshot


def test_market_snapshot_insufficient_data():
    class FakeProvider:
        def get_ohlcv(self, ticker: str, period: str, interval: str) -> pd.DataFrame:
            return pd.DataFrame()

    result = market_snapshot("INVALID", "3mo", provider=FakeProvider())
    assert result["error"] == "NO_DATA"
    assert result["ticker"] == "INVALID"


def test_market_snapshot_with_benchmarks():
    dates = pd.date_range("2026-01-01", periods=30, freq="D")
    df = pd.DataFrame(
        {
            "Open": pd.Series(range(100, 130), index=dates, dtype=float),
            "High": pd.Series(range(101, 131), index=dates, dtype=float),
            "Low": pd.Series(range(99, 129), index=dates, dtype=float),
            "Close": pd.Series(range(100, 130), index=dates, dtype=float),
            "Volume": pd.Series(range(1000, 1030), index=dates, dtype=float),
        }
    )

    class FakeProvider:
        def get_ohlcv(self, ticker: str, period: str, interval: str) -> pd.DataFrame:
            return df

    result = market_snapshot("AAPL", "3mo", benchmarks=["SPY"], provider=FakeProvider())
    assert "error" not in result
    assert result["ticker"] == "AAPL"
    assert result["period"] == "3mo"
