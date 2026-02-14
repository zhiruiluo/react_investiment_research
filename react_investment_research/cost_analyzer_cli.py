"""CLI for cost and token analysis of research agent."""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from .cost_analyzer import batch_analyze, get_global_analyzer


def analyze_session() -> None:
    """Print session cost summary."""
    analyzer = get_global_analyzer()
    summary = analyzer.get_session_summary()
    
    if not summary['total_queries']:
        print("No queries tracked in session.")
        return
    
    print(f"Session Summary")
    print(f"  Total queries: {summary['total_queries']}")
    print(f"  Total tokens: {summary['total_tokens']}")
    print(f"  Total cost: ${summary['total_cost_usd']:.6f}")
    print(f"  Avg cost/query: ${summary['avg_cost_per_query']:.6f}")
    print(f"  Avg tokens/query: {summary['avg_tokens_per_query']}")
    
    print("\nProvider Breakdown")
    providers = analyzer.get_provider_breakdown()
    for provider, data in providers.items():
        print(f"  {provider}:")
        print(f"    Queries: {data['queries']}")
        print(f"    Total tokens: {data['total_tokens']}")
        print(f"    Total cost: ${data['total_cost_usd']:.6f}")


def compare_providers() -> None:
    """Compare costs between OpenAI and Anthropic."""
    analyzer = get_global_analyzer()
    comparison = analyzer.get_cost_comparison()
    
    print("Cost Comparison: OpenAI vs Anthropic")
    print("(for typical investment research queries)\n")
    
    for query_type, data in comparison.items():
        tokens = data['tokens']
        openai_cost = data['openai_cost_usd']
        anthropic_cost = data['anthropic_cost_usd']
        ratio = data['cost_ratio']
        
        print(f"{query_type}:")
        print(f"  Tokens: {tokens['input']} input + {tokens['output']} output")
        print(f"  OpenAI:    ${openai_cost:.6f}")
        print(f"  Anthropic: ${anthropic_cost:.6f}")
        if data['anthropic_more_expensive']:
            print(f"  ⚠️  Anthropic is {(ratio-1)*100:.1f}% MORE expensive")
        else:
            print(f"  ✓ Anthropic is {(1-ratio)*100:.1f}% CHEAPER")
        print()


def batch_cost_estimation(num_queries: int, provider: str, num_tickers: int) -> None:
    """Estimate cost for a batch of queries."""
    print(f"Batch Cost Estimation")
    print(f"  Queries: {num_queries}")
    print(f"  Provider: {provider}")
    print(f"  Tickers per query: {num_tickers}")
    print()
    
    # Generate sample queries
    queries = []
    for i in range(num_queries):
        tickers = [f"TICK{j}" for j in range(num_tickers)]
        queries.append((f"Query {i+1}", tickers, "3mo"))
    
    result = batch_analyze(queries, provider=provider)
    
    print(f"Results:")
    print(f"  Model: {result['model']}")
    print(f"  Total tokens: {result['total_tokens']}")
    print(f"  Total cost: ${result['total_cost_usd']:.6f}")
    print(f"  Cost per query: ${result['avg_cost_per_query']:.6f}")
    print(f"  Cost per ticker: ${result['avg_cost_per_query'] / num_tickers:.6f}")


def estimate_monthly_cost(queries_per_day: int, provider: str) -> None:
    """Estimate monthly cost based on usage pattern."""
    print(f"Monthly Cost Estimation")
    print(f"  Queries per day: {queries_per_day}")
    print(f"  Provider: {provider}")
    print()
    
    # Typical single-ticker query
    queries = [(f"Daily query {i}", ["STOCK"], "3mo") for i in range(queries_per_day)]
    result = batch_analyze(queries, provider=provider)
    
    daily_cost = result['total_cost_usd']
    monthly_cost = daily_cost * 30
    yearly_cost = daily_cost * 365
    
    print(f"Results (per single-ticker query):")
    print(f"  Cost per query: ${result['avg_cost_per_query']:.6f}")
    print(f"  Daily cost: ${daily_cost:.6f}")
    print(f"  Monthly cost: ${monthly_cost:.2f}")
    print(f"  Yearly cost: ${yearly_cost:.2f}")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Cost and token analysis for research agent"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Session command
    subparsers.add_parser(
        "session",
        help="Print current session cost summary"
    )
    
    # Compare providers command
    subparsers.add_parser(
        "compare",
        help="Compare costs between OpenAI and Anthropic"
    )
    
    # Batch estimation command
    batch_parser = subparsers.add_parser(
        "batch",
        help="Estimate cost for a batch of queries"
    )
    batch_parser.add_argument("--num-queries", type=int, default=10)
    batch_parser.add_argument("--provider", choices=["openai", "anthropic"], default="openai")
    batch_parser.add_argument("--num-tickers", type=int, default=2)
    
    # Monthly estimation command
    monthly_parser = subparsers.add_parser(
        "monthly",
        help="Estimate monthly cost based on usage pattern"
    )
    monthly_parser.add_argument("--queries-per-day", type=int, default=20)
    monthly_parser.add_argument("--provider", choices=["openai", "anthropic"], default="openai")
    
    args = parser.parse_args()
    
    if args.command == "session":
        analyze_session()
    elif args.command == "compare":
        compare_providers()
    elif args.command == "batch":
        batch_cost_estimation(
            args.num_queries,
            args.provider,
            args.num_tickers
        )
    elif args.command == "monthly":
        estimate_monthly_cost(
            args.queries_per_day,
            args.provider
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
