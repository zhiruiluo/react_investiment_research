import argparse
import json

from .agent import ResearchAgent


def _get_tools_help_text() -> str:
    """Generate help text showing available tools with pricing info."""
    # Tool definitions with metadata
    tools = [
        {"name": "fundamentals_events", "is_paid": False, "pricing": 0.0},
        {"name": "market_snapshot", "is_paid": False, "pricing": 0.0},
        {"name": "sentiment_analysis", "is_paid": True, "pricing": 0.05},
    ]
    
    lines = ["Available tools (comma-separated):"]
    for tool in tools:
        paid_label = "[PAID]" if tool["is_paid"] else "[FREE]"
        pricing_str = f" ${tool['pricing']}/call" if tool["is_paid"] else ""
        lines.append(f"  {tool['name']} {paid_label}{pricing_str}")
    lines.append("Default: free tools only")
    return "\n".join(lines)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ReAct investment research agent")
    parser.add_argument("--query", required=True)
    parser.add_argument("--tickers", default="")
    parser.add_argument("--period", default="3mo")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM for analysis (requires OPENAI_API_KEY or ANTHROPIC_API_KEY)")
    parser.add_argument("--report-cost", action="store_true", help="Include cost analysis in output")
    parser.add_argument(
        "--tools",
        default=None,
        help=_get_tools_help_text(),
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    
    # Parse and validate tools
    available_tools = None
    if args.tools:
        available_tools = [t.strip() for t in args.tools.split(",") if t.strip()]
    
    try:
        agent = ResearchAgent(
            offline=args.offline,
            use_llm=args.use_llm,
            track_costs=args.report_cost,
            available_tools=available_tools,
        )
    except ValueError as e:
        # Tool validation error - error message already includes available tools
        print(json.dumps({
            "error": str(e),
        }, ensure_ascii=True))
        return
    
    result = agent.run(query=args.query, tickers=tickers, period=args.period)
    
    # Remove cost_analysis if not requested
    if not args.report_cost and "cost_analysis" in result:
        result["cost_analysis"] = None
    
    print(json.dumps(result, ensure_ascii=True))
