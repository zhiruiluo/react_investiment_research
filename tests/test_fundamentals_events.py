from react_investment_research.tools.fundamentals_events import fundamentals_events


class FakeProvider:
    def get_info(self, ticker: str):
        return {
            "marketCap": 10,
            "trailingPE": 20,
            "unknownField": 999,
            "regularMarketTime": "2026-01-31",
        }

    def get_calendar(self, ticker: str):
        return {"Earnings Date": {"2026-02-10": "2026-02-10"}}


def test_fundamentals_allowlist() -> None:
    result = fundamentals_events("AAPL", fields=["marketCap", "unknownField"], provider=FakeProvider())
    assert "marketCap" in result["fundamentals"]
    assert "unknownField" not in result["fundamentals"]
