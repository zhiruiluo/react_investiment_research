import argparse
import json

from .agent import ResearchAgent


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ReAct investment research agent")
    parser.add_argument("--query", required=True)
    parser.add_argument("--tickers", default="")
    parser.add_argument("--period", default="3mo")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM for analysis (requires OPENAI_API_KEY or ANTHROPIC_API_KEY)")
    parser.add_argument("--report-cost", action="store_true", help="Include cost analysis in output")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    agent = ResearchAgent(offline=args.offline, use_llm=args.use_llm, track_costs=args.report_cost)
    result = agent.run(query=args.query, tickers=tickers, period=args.period)
    
    # Remove cost_analysis if not requested
    if not args.report_cost and "cost_analysis" in result:
        result["cost_analysis"] = None
    
    print(json.dumps(result, ensure_ascii=True))
