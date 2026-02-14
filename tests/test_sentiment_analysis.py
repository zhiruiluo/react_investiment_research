"""Tests for sentiment analysis tool."""

import pytest

from react_investment_research.tools.sentiment_analysis import (
    sentiment_analysis,
    MOCK_SENTIMENT_DATA,
)


class TestSentimentAnalysis:
    """Tests for sentiment_analysis tool."""

    def test_sentiment_analysis_nvda(self):
        """Test sentiment analysis for NVDA."""
        result = sentiment_analysis("NVDA")
        
        assert result["ticker"] == "NVDA"
        assert "asof" in result
        assert -1.0 <= result["overall_sentiment"] <= 1.0
        assert "components" in result
        assert "news_sentiment" in result["components"]
        assert "analyst_sentiment" in result["components"]
        assert "metadata" in result
        assert "trend" in result
        assert "top_headlines" in result

    def test_sentiment_analysis_case_insensitive(self):
        """Test that ticker symbols are case-insensitive."""
        result_lower = sentiment_analysis("nvda")
        result_upper = sentiment_analysis("NVDA")
        
        assert result_lower["ticker"] == "NVDA"
        assert result_upper["ticker"] == "NVDA"
        assert result_lower["overall_sentiment"] == result_upper["overall_sentiment"]

    def test_sentiment_analysis_mock_data_consistency(self):
        """Test that mock data returns consistent values."""
        result = sentiment_analysis("AAPL")
        mock_data = MOCK_SENTIMENT_DATA["AAPL"]
        
        assert result["overall_sentiment"] == mock_data["overall_sentiment"]
        assert result["components"] == mock_data["components"]
        assert result["trend"] == mock_data["trend"]

    def test_sentiment_analysis_unknown_ticker(self):
        """Test sentiment analysis for unknown ticker returns neutral."""
        result = sentiment_analysis("UNKNOWNTICKER")
        
        # Should return neutral sentiment
        assert result["overall_sentiment"] == 0.0
        assert result["components"]["news_sentiment"] == 0.0
        assert result["components"]["analyst_sentiment"] == 0.0

    def test_sentiment_analysis_with_lookback_days(self):
        """Test sentiment analysis with custom lookback period."""
        result = sentiment_analysis("NVDA", lookback_days=90)
        
        assert result["lookback_days"] == 90
        assert result["ticker"] == "NVDA"

    def test_sentiment_analysis_components_valid_range(self):
        """Test that all sentiment components are in valid range."""
        for ticker in ["NVDA", "AAPL", "SPY", "QQQ", "TLT"]:
            result = sentiment_analysis(ticker)
            
            assert -1.0 <= result["overall_sentiment"] <= 1.0
            assert -1.0 <= result["components"]["news_sentiment"] <= 1.0
            assert -1.0 <= result["components"]["analyst_sentiment"] <= 1.0

    def test_sentiment_analysis_has_headlines(self):
        """Test that sentiment analysis returns headlines."""
        result = sentiment_analysis("NVDA")
        
        assert len(result["top_headlines"]) > 0
        assert all(isinstance(h, str) for h in result["top_headlines"])

    def test_sentiment_analysis_metadata_structure(self):
        """Test that metadata has correct structure."""
        result = sentiment_analysis("AAPL")
        metadata = result["metadata"]
        
        assert "news_articles_analyzed" in metadata
        assert "analyst_ratings" in metadata
        assert "consensus" in metadata
        
        ratings = metadata["analyst_ratings"]
        assert "strong_buy" in ratings
        assert "buy" in ratings
        assert "hold" in ratings
        assert "sell" in ratings
        assert "strong_sell" in ratings

    def test_sentiment_analysis_trend_values(self):
        """Test that trend is one of allowed values."""
        allowed_trends = {"improving", "stable", "declining", "neutral"}
        
        for ticker in ["NVDA", "AAPL", "SPY", "QQQ", "TLT"]:
            result = sentiment_analysis(ticker)
            assert result["trend"] in allowed_trends

    def test_sentiment_analysis_positive_vs_negative(self):
        """Test that positive sentiment reflects in scores."""
        # NVDA should have positive sentiment
        nvda_result = sentiment_analysis("NVDA")
        assert nvda_result["overall_sentiment"] > 0.5  # Bullish
        
        # TLT should have negative sentiment
        tlt_result = sentiment_analysis("TLT")
        assert tlt_result["overall_sentiment"] < 0.0  # Bearish
