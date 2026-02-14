from __future__ import annotations

from typing import Any, Dict, List

from .agent import ResearchAgent
from .schemas import validate_schema


def run_eval() -> Dict[str, Any]:
    agent = ResearchAgent(offline=True)
    cases = [
        {"query": "trend summary for AAPL", "tickers": ["AAPL"], "period": "3mo"},
        {"query": "compare AAPL vs MSFT", "tickers": ["AAPL", "MSFT"], "period": "6mo"},
        {"query": "risk evaluation", "tickers": ["AAPL"], "period": "1y"},
        {"query": "macro proxies", "tickers": [], "period": "3mo"},
    ]

    results: List[Dict[str, Any]] = []
    score = 0

    for case in cases:
        output = agent.run(**case)
        ok, _ = validate_schema("final_output", output)
        if ok:
            score += 2
        if output.get("tool_calls") and len(output["tool_calls"]) <= 6:
            score += 1
        if output.get("disclaimer") == "Research summary, not financial advice.":
            score += 1
        results.append(output)

    return {"score": score, "max_score": len(cases) * 4, "results": results}
