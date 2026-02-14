from unittest.mock import MagicMock

from react_investment_research.llm import LLMClient


def test_llm_client_disabled_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = LLMClient()
    assert not client.enabled


def test_llm_client_fallback():
    client = LLMClient()
    result = client.generate_summary("test query", ["AAPL"], {"AAPL": {"prices": {"return_pct": 5.0}}})
    assert "thesis_bullets" in result
    assert "risks" in result


def test_llm_infer_tickers_disabled(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = LLMClient()
    result = client.infer_tickers("compare Nvidia vs AMD")
    assert "tickers" in result
    assert result.get("llm_error")
