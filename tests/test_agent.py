from react_investment_research.agent import ResearchAgent
from react_investment_research.schemas import validate_schema


def test_agent_offline_schema() -> None:
    agent = ResearchAgent(offline=True)
    output = agent.run(query="compare AAPL vs MSFT", tickers=["AAPL", "MSFT"], period="3mo")
    ok, error = validate_schema("final_output", output)
    assert ok, error
    assert output["disclaimer"] == "Research summary, not financial advice."


def test_agent_proxy_tickers() -> None:
    agent = ResearchAgent(offline=True)
    output = agent.run(query="macro proxies", tickers=[], period="3mo")
    assert output["tickers"] == ["SPY", "QQQ", "TLT", "GLD"]


def test_tool_budget_guardrail() -> None:
    agent = ResearchAgent(offline=True)
    output = agent.run(query="too many", tickers=["A", "B", "C", "D"], period="3mo")
    assert len(output["tool_calls"]) <= 6
    assert output["limitations"]
