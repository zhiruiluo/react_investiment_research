import pandas as pd

from react_investment_research.tools.providers import YFinanceProvider


def test_provider_with_empty_data(monkeypatch):
    def mock_download(*args, **kwargs):
        return pd.DataFrame()

    monkeypatch.setattr("yfinance.download", mock_download)
    provider = YFinanceProvider()
    result = provider.get_ohlcv("INVALID", "3mo", "1d")
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_provider_get_info_empty(monkeypatch):
    def mock_ticker(*args, **kwargs):
        class MockTicker:
            info = None

        return MockTicker()

    monkeypatch.setattr("yfinance.Ticker", mock_ticker)
    provider = YFinanceProvider()
    result = provider.get_info("INVALID")
    assert result == {}
