"""Tests for cost analysis module."""

import pytest

from react_investment_research.cost_analyzer import (
    ANTHROPIC_PRICING,
    OPENAI_PRICING,
    CostAnalyzer,
    CostBreakdown,
    TokenCount,
    batch_analyze,
    get_global_analyzer,
    reset_global_analyzer,
)


class TestTokenCount:
    """Test token count tracking."""

    def test_empty_token_count(self) -> None:
        """Test creating empty token count."""
        tc = TokenCount()
        assert tc.input_tokens == 0
        assert tc.output_tokens == 0
        assert tc.total == 0

    def test_token_count_total(self) -> None:
        """Test token count total calculation."""
        tc = TokenCount(input_tokens=100, output_tokens=50)
        assert tc.total == 150


class TestCostBreakdown:
    """Test cost breakdown calculation."""

    def test_empty_cost_breakdown(self) -> None:
        """Test creating empty cost breakdown."""
        cb = CostBreakdown()
        assert cb.input_cost_usd == 0.0
        assert cb.output_cost_usd == 0.0
        assert cb.total_usd == 0.0

    def test_cost_breakdown_total(self) -> None:
        """Test cost breakdown total calculation."""
        cb = CostBreakdown(input_cost_usd=0.1, output_cost_usd=0.2)
        assert pytest.approx(cb.total_usd, abs=0.0001) == 0.3


class TestCostAnalyzer:
    """Test main cost analyzer."""

    def test_analyzer_initialization(self) -> None:
        """Test cost analyzer initialization."""
        analyzer = CostAnalyzer()
        assert analyzer.queries == []

    def test_calculate_openai_cost(self) -> None:
        """Test OpenAI cost calculation."""
        analyzer = CostAnalyzer()
        cost = analyzer.calculate_cost(
            provider="openai",
            model="gpt-4o-mini",
            input_tokens=1000,
            output_tokens=250,
        )

        # OpenAI pricing: input $0.15/1M, output $0.60/1M
        expected_input = (1000 / 1_000_000) * 0.15
        expected_output = (250 / 1_000_000) * 0.60
        expected_total = expected_input + expected_output

        assert pytest.approx(cost.input_cost_usd, abs=0.000001) == expected_input
        assert pytest.approx(cost.output_cost_usd, abs=0.000001) == expected_output
        assert pytest.approx(cost.total_usd, abs=0.000001) == expected_total

    def test_calculate_anthropic_cost(self) -> None:
        """Test Anthropic cost calculation."""
        analyzer = CostAnalyzer()
        cost = analyzer.calculate_cost(
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            input_tokens=1000,
            output_tokens=250,
        )

        # Anthropic pricing: input $3.00/1M, output $15.00/1M
        expected_input = (1000 / 1_000_000) * 3.00
        expected_output = (250 / 1_000_000) * 15.00
        expected_total = expected_input + expected_output

        assert pytest.approx(cost.input_cost_usd, abs=0.000001) == expected_input
        assert pytest.approx(cost.output_cost_usd, abs=0.000001) == expected_output
        assert pytest.approx(cost.total_usd, abs=0.000001) == expected_total

    def test_track_query(self) -> None:
        """Test query tracking."""
        analyzer = CostAnalyzer()
        analysis = analyzer.track_query(
            query="compare AAPL vs MSFT",
            tickers=["AAPL", "MSFT"],
            period="3mo",
            provider="openai",
            model="gpt-4o-mini",
            input_tokens=1000,
            output_tokens=250,
        )

        assert len(analyzer.queries) == 1
        assert analysis.query == "compare AAPL vs MSFT"
        assert analysis.tickers == ["AAPL", "MSFT"]
        assert analysis.tokens.input_tokens == 1000
        assert analysis.tokens.output_tokens == 250

    def test_query_cost_per_ticker(self) -> None:
        """Test cost per ticker calculation."""
        analyzer = CostAnalyzer()
        analysis = analyzer.track_query(
            query="compare",
            tickers=["A", "B"],
            period="3mo",
            provider="openai",
            model="gpt-4o-mini",
            input_tokens=1000,
            output_tokens=250,
        )

        assert analysis.cost_per_ticker > 0
        assert pytest.approx(analysis.cost_per_ticker, abs=0.000001) == (
            analysis.cost.total_usd / 2
        )

    def test_query_tokens_per_ticker(self) -> None:
        """Test tokens per ticker calculation."""
        analyzer = CostAnalyzer()
        analysis = analyzer.track_query(
            query="compare",
            tickers=["A", "B", "C"],
            period="3mo",
            provider="openai",
            model="gpt-4o-mini",
            input_tokens=1200,
            output_tokens=300,
        )

        assert analysis.tokens_per_ticker == (1200 + 300) // 3

    def test_query_cost_with_no_tickers(self) -> None:
        """Test cost calculation with empty ticker list."""
        analyzer = CostAnalyzer()
        analysis = analyzer.track_query(
            query="query",
            tickers=[],
            period="3mo",
            provider="openai",
            model="gpt-4o-mini",
            input_tokens=1000,
            output_tokens=250,
        )

        assert analysis.cost_per_ticker == 0.0
        assert analysis.tokens_per_ticker == 0

    def test_session_summary_empty(self) -> None:
        """Test session summary with no queries."""
        analyzer = CostAnalyzer()
        summary = analyzer.get_session_summary()

        assert summary["total_queries"] == 0
        assert summary["total_tokens"] == 0
        assert summary["total_cost_usd"] == 0.0

    def test_session_summary_with_queries(self) -> None:
        """Test session summary with multiple queries."""
        analyzer = CostAnalyzer()

        analyzer.track_query(
            "query1", ["A"], "3mo", "openai", "gpt-4o-mini",
            1000, 250
        )
        analyzer.track_query(
            "query2", ["B", "C"], "6mo", "openai", "gpt-4o-mini",
            1600, 350
        )

        summary = analyzer.get_session_summary()

        assert summary["total_queries"] == 2
        assert summary["total_tokens"] == 3200  # 1250 + 1950
        assert summary["total_cost_usd"] > 0
        assert summary["avg_cost_per_query"] > 0
        assert summary["avg_tokens_per_query"] == 1600

    def test_provider_breakdown(self) -> None:
        """Test provider cost breakdown."""
        analyzer = CostAnalyzer()

        analyzer.track_query(
            "query1", ["A"], "3mo", "openai", "gpt-4o-mini",
            1000, 250
        )
        analyzer.track_query(
            "query2", ["B"], "3mo", "anthropic", "claude-3-5-sonnet-20241022",
            1000, 250
        )

        breakdown = analyzer.get_provider_breakdown()

        assert "openai" in breakdown
        assert "anthropic" in breakdown
        assert breakdown["openai"]["queries"] == 1
        assert breakdown["anthropic"]["queries"] == 1

    def test_cost_comparison(self) -> None:
        """Test provider comparison."""
        analyzer = CostAnalyzer()
        comparison = analyzer.get_cost_comparison()

        # Should have comparison for typical query types
        assert "single_ticker" in comparison
        assert "two_tickers" in comparison
        assert "five_tickers" in comparison

        # Anthropic should be more expensive for these models
        single = comparison["single_ticker"]
        assert single["openai_cost_usd"] < single["anthropic_cost_usd"]


class TestBatchAnalyze:
    """Test batch analysis."""

    def test_batch_analyze_single_query(self) -> None:
        """Test batch analysis with single query."""
        queries = [("compare AAPL vs MSFT", ["AAPL", "MSFT"], "3mo")]
        result = batch_analyze(queries, provider="openai")

        assert result["total_queries"] == 1
        assert result["total_tokens"] > 0
        assert result["total_cost_usd"] > 0

    def test_batch_analyze_multiple_queries(self) -> None:
        """Test batch analysis with multiple queries."""
        queries = [
            ("query1", ["A"], "3mo"),
            ("query2", ["B", "C"], "6mo"),
            ("query3", ["D", "E", "F"], "1y"),
        ]
        result = batch_analyze(queries, provider="openai")

        assert result["total_queries"] == 3
        assert result["avg_cost_per_query"] > 0

    def test_batch_analyze_anthropic(self) -> None:
        """Test batch analysis with Anthropic provider."""
        queries = [("query", ["TICKER"], "3mo")]
        result = batch_analyze(queries, provider="anthropic")

        assert result["provider"] == "anthropic"
        assert result["total_cost_usd"] > 0


class TestGlobalAnalyzer:
    """Test global analyzer instance."""

    def test_get_global_analyzer(self) -> None:
        """Test getting global analyzer."""
        analyzer = get_global_analyzer()
        assert isinstance(analyzer, CostAnalyzer)

    def test_global_analyzer_persistence(self) -> None:
        """Test that global analyzer persists across calls."""
        reset_global_analyzer()
        analyzer1 = get_global_analyzer()
        analyzer1.track_query(
            "query", ["A"], "3mo", "openai", "gpt-4o-mini", 100, 50
        )

        analyzer2 = get_global_analyzer()
        assert len(analyzer2.queries) == 1

    def test_reset_global_analyzer(self) -> None:
        """Test resetting global analyzer."""
        analyzer = get_global_analyzer()
        analyzer.track_query(
            "query", ["A"], "3mo", "openai", "gpt-4o-mini", 100, 50
        )

        reset_global_analyzer()
        new_analyzer = get_global_analyzer()
        assert len(new_analyzer.queries) == 0


class TestQueryCostAnalysisToDict:
    """Test query analysis to_dict conversion."""

    def test_analysis_to_dict(self) -> None:
        """Test converting analysis to dictionary."""
        analyzer = CostAnalyzer()
        analysis = analyzer.track_query(
            "compare", ["A", "B"], "3mo",
            "openai", "gpt-4o-mini",
            1000, 250
        )

        result = analysis.to_dict()

        assert result["query"] == "compare"
        assert result["tickers"] == ["A", "B"]
        assert result["provider"] == "openai"
        assert "tokens" in result
        assert "cost" in result
        assert result["cost"]["total_usd"] > 0
