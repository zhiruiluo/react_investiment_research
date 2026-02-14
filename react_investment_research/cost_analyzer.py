"""Cost and token usage analysis for research agent queries."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# OpenAI pricing (as of Feb 2026)
OPENAI_PRICING = {
    "gpt-4o-mini": {
        "input_per_1m": 0.15,  # $0.15 per 1M input tokens
        "output_per_1m": 0.60,  # $0.60 per 1M output tokens
    },
    "gpt-4-turbo": {
        "input_per_1m": 10.00,
        "output_per_1m": 30.00,
    },
}

# Anthropic pricing (as of Feb 2026)
ANTHROPIC_PRICING = {
    "claude-3-5-sonnet-20241022": {
        "input_per_1m": 3.00,  # $3.00 per 1M input tokens
        "output_per_1m": 15.00,  # $15.00 per 1M output tokens
    },
    "claude-3-opus-20250219": {
        "input_per_1m": 15.00,
        "output_per_1m": 75.00,
    },
}


@dataclass
class TokenCount:
    """Token usage for a single request."""

    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class CostBreakdown:
    """Cost breakdown for a single request."""

    input_cost_usd: float = 0.0
    output_cost_usd: float = 0.0

    @property
    def total_usd(self) -> float:
        return self.input_cost_usd + self.output_cost_usd


@dataclass
class QueryCostAnalysis:
    """Complete cost analysis for a single query."""

    query: str
    tickers: List[str]
    period: str
    provider: str
    model: str
    tokens: TokenCount = field(default_factory=TokenCount)
    cost: CostBreakdown = field(default_factory=CostBreakdown)

    @property
    def cost_per_ticker(self) -> float:
        """Cost normalized by number of tickers."""
        if not self.tickers:
            return 0.0
        return self.cost.total_usd / len(self.tickers)

    @property
    def tokens_per_ticker(self) -> int:
        """Token count normalized by number of tickers."""
        if not self.tickers:
            return 0
        return self.tokens.total // len(self.tickers)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "query": self.query,
            "tickers": self.tickers,
            "period": self.period,
            "provider": self.provider,
            "model": self.model,
            "tokens": {
                "input": self.tokens.input_tokens,
                "output": self.tokens.output_tokens,
                "total": self.tokens.total,
                "per_ticker": self.tokens_per_ticker,
            },
            "cost": {
                "total_usd": round(self.cost.total_usd, 6),
                "input_cost_usd": round(self.cost.input_cost_usd, 6),
                "output_cost_usd": round(self.cost.output_cost_usd, 6),
                "cost_per_ticker_usd": round(self.cost_per_ticker, 6),
            },
        }


class CostAnalyzer:
    """Analyze and track costs of research agent queries."""

    def __init__(self) -> None:
        """Initialize cost analyzer."""
        self.queries: List[QueryCostAnalysis] = []

    def calculate_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> CostBreakdown:
        """Calculate cost based on provider, model, and token counts."""
        if provider == "openai":
            pricing = OPENAI_PRICING.get(model, OPENAI_PRICING["gpt-4o-mini"])
        elif provider == "anthropic":
            pricing = ANTHROPIC_PRICING.get(
                model, ANTHROPIC_PRICING["claude-3-5-sonnet-20241022"]
            )
        else:
            return CostBreakdown()

        input_cost = (input_tokens / 1_000_000) * pricing["input_per_1m"]
        output_cost = (output_tokens / 1_000_000) * pricing["output_per_1m"]

        return CostBreakdown(input_cost_usd=input_cost, output_cost_usd=output_cost)

    def track_query(
        self,
        query: str,
        tickers: List[str],
        period: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> QueryCostAnalysis:
        """Track a single query's cost."""
        tokens = TokenCount(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        cost = self.calculate_cost(provider, model, input_tokens, output_tokens)

        analysis = QueryCostAnalysis(
            query=query,
            tickers=tickers,
            period=period,
            provider=provider,
            model=model,
            tokens=tokens,
            cost=cost,
        )
        self.queries.append(analysis)
        return analysis

    def get_session_summary(self) -> Dict[str, Any]:
        """Get cost summary for current session."""
        if not self.queries:
            return {
                "total_queries": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "queries": [],
            }

        total_tokens = sum(q.tokens.total for q in self.queries)
        total_cost_usd = sum(q.cost.total_usd for q in self.queries)
        avg_cost_per_query = (
            total_cost_usd / len(self.queries) if self.queries else 0.0
        )
        avg_tokens_per_query = (
            total_tokens / len(self.queries) if self.queries else 0
        )

        return {
            "total_queries": len(self.queries),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost_usd, 6),
            "avg_cost_per_query": round(avg_cost_per_query, 6),
            "avg_tokens_per_query": avg_tokens_per_query,
            "queries": [q.to_dict() for q in self.queries],
        }

    def get_provider_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Get cost and token breakdown by provider."""
        providers: Dict[str, Dict[str, Any]] = {}

        for query in self.queries:
            provider = query.provider
            if provider not in providers:
                providers[provider] = {
                    "queries": 0,
                    "total_tokens": 0,
                    "total_cost_usd": 0.0,
                    "models": {},
                }

            providers[provider]["queries"] += 1
            providers[provider]["total_tokens"] += query.tokens.total
            providers[provider]["total_cost_usd"] += query.cost.total_usd

            model = query.model
            if model not in providers[provider]["models"]:
                providers[provider]["models"][model] = {
                    "queries": 0,
                    "cost_usd": 0.0,
                }

            providers[provider]["models"][model]["queries"] += 1
            providers[provider]["models"][model]["cost_usd"] += query.cost.total_usd

        # Round costs
        for provider in providers:
            providers[provider]["total_cost_usd"] = round(
                providers[provider]["total_cost_usd"], 6
            )
            for model in providers[provider]["models"]:
                providers[provider]["models"][model]["cost_usd"] = round(
                    providers[provider]["models"][model]["cost_usd"], 6
                )

        return providers

    def get_cost_comparison(self) -> Dict[str, Any]:
        """Compare cost between OpenAI and Anthropic for same queries."""
        openai_pricing = OPENAI_PRICING["gpt-4o-mini"]
        anthropic_pricing = ANTHROPIC_PRICING["claude-3-5-sonnet-20241022"]

        # Typical token usage (estimated from actual queries)
        typical_queries = [
            {"name": "single_ticker", "input": 800, "output": 250},
            {"name": "two_tickers", "input": 1600, "output": 350},
            {"name": "five_tickers", "input": 3500, "output": 400},
        ]

        comparison = {}
        for q in typical_queries:
            openai_cost = (q["input"] / 1_000_000) * openai_pricing[
                "input_per_1m"
            ] + (q["output"] / 1_000_000) * openai_pricing["output_per_1m"]

            anthropic_cost = (q["input"] / 1_000_000) * anthropic_pricing[
                "input_per_1m"
            ] + (q["output"] / 1_000_000) * anthropic_pricing["output_per_1m"]

            savings_pct = ((anthropic_cost - openai_cost) / anthropic_cost) * 100

            comparison[q["name"]] = {
                "tokens": {"input": q["input"], "output": q["output"]},
                "openai_cost_usd": round(openai_cost, 6),
                "anthropic_cost_usd": round(anthropic_cost, 6),
                "anthropic_more_expensive": anthropic_cost > openai_cost,
                "cost_ratio": round(anthropic_cost / openai_cost, 2),
            }

        return comparison


# Global analyzer instance
_global_analyzer = CostAnalyzer()


def get_global_analyzer() -> CostAnalyzer:
    """Get the global cost analyzer instance."""
    return _global_analyzer


def reset_global_analyzer() -> None:
    """Reset the global analyzer (useful for testing)."""
    global _global_analyzer
    _global_analyzer = CostAnalyzer()


def batch_analyze(
    queries: List[Tuple[str, List[str], Optional[str]]],
    provider: str = "openai",
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Analyze cost of a batch of queries.

    Args:
        queries: List of (query_text, tickers, period) tuples
        provider: LLM provider ("openai" or "anthropic")
        model: Specific model to use (optional, uses default)

    Returns:
        Dict with total cost, tokens, and breakdown
    """
    if model is None:
        model = (
            "gpt-4o-mini" if provider == "openai" else "claude-3-5-sonnet-20241022"
        )

    analyzer = CostAnalyzer()
    total_cost = 0.0
    total_tokens = 0

    for query_text, tickers, period in queries:
        # Estimate tokens (rough heuristic)
        num_tickers = len(tickers) if tickers else 1
        estimated_input = 800 + (num_tickers - 1) * 400
        estimated_output = 250 + (num_tickers - 1) * 50

        analysis = analyzer.track_query(
            query=query_text,
            tickers=tickers or [],
            period=period or "3mo",
            provider=provider,
            model=model,
            input_tokens=estimated_input,
            output_tokens=estimated_output,
        )

        total_cost += analysis.cost.total_usd
        total_tokens += analysis.tokens.total

    summary = analyzer.get_session_summary()
    return {
        "total_queries": len(queries),
        "total_cost_usd": round(total_cost, 6),
        "total_tokens": total_tokens,
        "avg_cost_per_query": round(total_cost / len(queries), 6) if queries else 0,
        "avg_tokens_per_query": total_tokens // len(queries) if queries else 0,
        "tokens_summary": {
            "total": total_tokens,
            "avg_per_query": total_tokens // len(queries) if queries else 0,
        },
        "provider": provider,
        "model": model,
    }
