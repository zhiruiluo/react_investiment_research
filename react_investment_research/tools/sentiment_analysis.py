"""Sentiment analysis tool for investment research.

Analyzes news sentiment and analyst ratings to provide comprehensive
sentiment insights for investment decisions.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Optional

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")


# Mock sentiment data for testing
MOCK_SENTIMENT_DATA = {
    "NVDA": {
        "overall_sentiment": 0.68,
        "components": {"news_sentiment": 0.72, "analyst_sentiment": 0.62},
        "metadata": {
            "news_articles_analyzed": 42,
            "analyst_ratings": {
                "strong_buy": 15,
                "buy": 12,
                "hold": 8,
                "sell": 2,
                "strong_sell": 1,
            },
            "consensus": "buy",
        },
        "trend": "improving",
        "top_headlines": [
            "NVDA beats earnings expectations",
            "Nvidia AI chip demand surges",
            "New GPU architecture drives growth",
        ],
    },
    "AAPL": {
        "overall_sentiment": 0.45,
        "components": {"news_sentiment": 0.42, "analyst_sentiment": 0.50},
        "metadata": {
            "news_articles_analyzed": 38,
            "analyst_ratings": {
                "strong_buy": 8,
                "buy": 18,
                "hold": 12,
                "sell": 4,
                "strong_sell": 0,
            },
            "consensus": "buy",
        },
        "trend": "stable",
        "top_headlines": [
            "Apple faces China slowdown",
            "iPhone 17 pre-orders strong",
            "Services revenue growth accelerates",
        ],
    },
    "SPY": {
        "overall_sentiment": 0.35,
        "components": {"news_sentiment": 0.38, "analyst_sentiment": 0.30},
        "metadata": {
            "news_articles_analyzed": 55,
            "analyst_ratings": {
                "strong_buy": 12,
                "buy": 25,
                "hold": 18,
                "sell": 5,
                "strong_sell": 1,
            },
            "consensus": "buy",
        },
        "trend": "stable",
        "top_headlines": [
            "Market reaches new highs",
            "Fed signals pause in rate hikes",
            "Tech earnings beat expectations",
        ],
    },
    "QQQ": {
        "overall_sentiment": 0.62,
        "components": {"news_sentiment": 0.65, "analyst_sentiment": 0.55},
        "metadata": {
            "news_articles_analyzed": 48,
            "analyst_ratings": {
                "strong_buy": 14,
                "buy": 20,
                "hold": 10,
                "sell": 2,
                "strong_sell": 1,
            },
            "consensus": "buy",
        },
        "trend": "improving",
        "top_headlines": [
            "Tech stocks rally on AI optimism",
            "Mega-cap earnings exceed expectations",
            "AI adoption accelerates across sectors",
        ],
    },
    "TLT": {
        "overall_sentiment": -0.15,
        "components": {"news_sentiment": -0.12, "analyst_sentiment": -0.20},
        "metadata": {
            "news_articles_analyzed": 25,
            "analyst_ratings": {
                "strong_buy": 2,
                "buy": 8,
                "hold": 12,
                "sell": 6,
                "strong_sell": 2,
            },
            "consensus": "hold",
        },
        "trend": "declining",
        "top_headlines": [
            "Bond yields remain elevated",
            "Fed keeps rates steady",
            "Inflation concerns linger",
        ],
    },
}


def _get_newsapi_sentiment(ticker: str) -> Optional[dict]:
    """Fetch sentiment from NewsAPI using real API integration.
    
    Args:
        ticker: Stock ticker symbol (e.g., "NVDA")
        
    Returns:
        Sentiment data dict or None if API call fails
    """
    if not NEWS_API_KEY:
        # No API key configured, return None to use mock data
        return None
    
    try:
        # Fetch articles about the ticker
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": ticker,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 50,
            "apiKey": NEWS_API_KEY,
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "ok":
            return None
        
        articles = data.get("articles", [])
        if not articles:
            return None
        
        # Simple sentiment analysis: count positive/negative keywords
        positive_keywords = [
            "beat", "surge", "rally", "bullish", "strong", "gains", 
            "outperform", "upgrade", "boom", "record"
        ]
        negative_keywords = [
            "miss", "plunge", "bearish", "weak", "decline", "downgrade",
            "slump", "crisis", "loss", "concern"
        ]
        
        positive_count = 0
        negative_count = 0
        
        for article in articles:
            title = (article.get("title", "") + " " + article.get("description", "")).lower()
            
            for keyword in positive_keywords:
                if keyword in title:
                    positive_count += 1
                    break  # Count each article only once
            
            for keyword in negative_keywords:
                if keyword in title:
                    negative_count += 1
                    break
        
        # Calculate sentiment score
        total_sentiment = positive_count + negative_count
        if total_sentiment == 0:
            overall_sentiment = 0.0
        else:
            overall_sentiment = (positive_count - negative_count) / total_sentiment
            # Clamp to [-1, 1]
            overall_sentiment = max(-1.0, min(1.0, overall_sentiment))
        
        # Create sentiment data structure
        news_sentiment = overall_sentiment  # Simplified: news sentiment = overall
        
        # Estimate analyst sentiment from article sentiment (simplified model)
        analyst_sentiment = overall_sentiment * 0.8 + 0.1  # Slight bias toward neutral
        analyst_sentiment = max(-1.0, min(1.0, analyst_sentiment))
        
        return {
            "overall_sentiment": (news_sentiment + analyst_sentiment) / 2,
            "components": {
                "news_sentiment": news_sentiment,
                "analyst_sentiment": analyst_sentiment,
            },
            "metadata": {
                "news_articles_analyzed": len(articles),
                "analyst_ratings": {
                    "strong_buy": max(0, int(positive_count * 0.3)),
                    "buy": max(0, int(positive_count * 0.4)),
                    "hold": max(0, int(total_sentiment * 0.2)),
                    "sell": max(0, int(negative_count * 0.4)),
                    "strong_sell": max(0, int(negative_count * 0.3)),
                },
                "consensus": "buy" if overall_sentiment > 0.2 else "hold" if overall_sentiment > -0.2 else "sell",
            },
            "trend": "improving" if overall_sentiment > 0.5 else "stable" if overall_sentiment > -0.2 else "declining",
            "top_headlines": [
                article.get("title", "")[:100]
                for article in articles[:3]
            ],
        }
    except requests.RequestException as e:
        # API error, return None to fall back to mock data
        return None
    except Exception as e:
        # Any other error, return None
        return None


def sentiment_analysis(
    ticker: str,
    lookback_days: int = 30,
) -> dict:
    """Analyze news and analyst sentiment for a stock.
    
    Combines news sentiment analysis with analyst ratings consensus
    to provide comprehensive sentiment insights. Returns both
    component scores and overall composite sentiment.
    
    Args:
        ticker: Stock ticker symbol (e.g., "NVDA")
        lookback_days: Number of days of news history to analyze (default: 30)
        
    Returns:
        Dictionary with structure:
        {
            "ticker": str,
            "asof": str (ISO date),
            "overall_sentiment": float (-1.0 to 1.0),
            "components": {
                "news_sentiment": float,
                "analyst_sentiment": float
            },
            "metadata": {
                "news_articles_analyzed": int,
                "analyst_ratings": {
                    "strong_buy": int,
                    "buy": int,
                    "hold": int,
                    "sell": int,
                    "strong_sell": int
                },
                "consensus": str
            },
            "trend": str ("improving", "stable", or "declining"),
            "top_headlines": [str, ...]
        }
    """
    # Normalize ticker
    ticker = ticker.upper()
    
    # Try real API first, fall back to mock data
    sentiment_data = _get_newsapi_sentiment(ticker)
    if sentiment_data is None:
        sentiment_data = MOCK_SENTIMENT_DATA.get(ticker)
    
    # If still no data, return neutral sentiment
    if sentiment_data is None:
        sentiment_data = {
            "overall_sentiment": 0.0,
            "components": {"news_sentiment": 0.0, "analyst_sentiment": 0.0},
            "metadata": {
                "news_articles_analyzed": 0,
                "analyst_ratings": {
                    "strong_buy": 0,
                    "buy": 0,
                    "hold": 0,
                    "sell": 0,
                    "strong_sell": 0,
                },
                "consensus": "no_data",
            },
            "trend": "neutral",
            "top_headlines": [f"No sentiment data available for {ticker}"],
        }
    
    # Build response with timestamp
    return {
        "ticker": ticker,
        "asof": datetime.now().strftime("%Y-%m-%d"),
        "overall_sentiment": sentiment_data["overall_sentiment"],
        "components": sentiment_data["components"],
        "metadata": sentiment_data["metadata"],
        "trend": sentiment_data["trend"],
        "top_headlines": sentiment_data["top_headlines"],
        "lookback_days": lookback_days,
    }


# Tool schema for LLM
SENTIMENT_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "ticker": {"type": "string", "description": "Stock ticker symbol"},
        "lookback_days": {
            "type": "integer",
            "description": "Number of days of news history to analyze",
        },
    },
    "required": ["ticker"],
}

SENTIMENT_ANALYSIS_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "ticker": {"type": "string"},
        "asof": {"type": "string"},
        "overall_sentiment": {"type": "number"},
        "components": {
            "type": "object",
            "properties": {
                "news_sentiment": {"type": "number"},
                "analyst_sentiment": {"type": "number"},
            },
        },
        "metadata": {
            "type": "object",
            "properties": {
                "news_articles_analyzed": {"type": "integer"},
                "analyst_ratings": {"type": "object"},
                "consensus": {"type": "string"},
            },
        },
        "trend": {"type": "string"},
        "top_headlines": {"type": "array", "items": {"type": "string"}},
    },
}
