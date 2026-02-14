import argparse
import json
import sys

from react_investment_research.agent import ResearchAgent
from react_investment_research.schemas import validate_schema


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline user simulation")
    parser.add_argument("--query", default="compare AAPL vs MSFT")
    parser.add_argument("--tickers", default="AAPL,MSFT")
    parser.add_argument("--period", default="3mo")
    args = parser.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    agent = ResearchAgent(offline=True)
    output = agent.run(query=args.query, tickers=tickers, period=args.period)
    ok, error = validate_schema("final_output", output)
    if not ok:
        print(json.dumps({"error": "INVALID_OUTPUT", "reason": error}, ensure_ascii=True))
        return 1

    print(json.dumps(output, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
