# React Investment Research - Todo List

## ✅ Completed
- [x] Enhance Tool dataclass with is_paid and pricing_usd_per_call
- [x] Add tool filtering and validation to agent.py
- [x] Add --tools CLI flag with validation
- [x] Update documentation with tool availability
- [x] Implement sentiment_analysis tool with mock data
- [x] Fix LLM tool routing (strip [PAID] labels)
- [x] Create PREMIUM_TOOLS.md documentation
- [x] Add comprehensive test coverage (52+ tests)

## 🔴 Critical (Production Readiness)
- [ ] Fully implement _get_newsapi_sentiment() with real API calls
  - Add robust error handling for network failures
  - Test with live NewsAPI data
  - Add request timeout handling
  - Add rate limit handling

- [ ] Integrate sentiment_analysis pricing into cost_analyzer
  - Track per-tool costs in CostAnalyzer
  - Include Tool.pricing_usd_per_call in calculations
  - Show cost breakdown by tool in output

- [ ] Add API key validation for premium tools
  - Warn if NEWS_API_KEY missing for sentiment_analysis
  - Better error messages for API key issues

## 📋 Should Do (Next Quarter)
- [ ] Implement sentiment data caching
  - Add TTL-based cache (24 hours default)
  - Reduce API calls and costs
  - Cache by ticker + lookback_days key

- [ ] Add rate limiting
  - Per-user rate limits
  - Daily/monthly budget enforcement
  - Warning system before limits

- [ ] Integration tests with real NewsAPI
  - Mock external API calls for CI/CD
  - Test error scenarios
  - Performance benchmarks

- [ ] Design additional premium tools
  - Identify next high-value tool
  - Establish pattern for tool development
  - Pricing model

## 🎯 Nice to Have (Future)
- [ ] Usage telemetry and analytics
  - Track tool usage patterns
  - Identify popular queries
  - Cost trend analysis

- [ ] Implement cost optimization strategies
  - Prompt caching for LLM
  - Fine-tuned models
  - Response summarization

- [ ] Batch operations support
  - Analyze multiple tickers in single call
  - Reduce API overhead

- [ ] Additional premium tools
  - Earnings surprise prediction
  - Technical pattern recognition
  - Risk metrics calculation

## 📊 Current Status
- **Tests Passing:** 52+
- **Tools Available:** 3 (market_snapshot, fundamentals_events, sentiment_analysis)
- **Tool Tiers:** Free (2) + Paid (1)
- **LLM Providers:** OpenAI, Anthropic
- **Production Ready:** Yes (with mock data fallback)
- **Real API Ready:** Partial (NewsAPI placeholder needs implementation)

## 🚀 Recommended Priority Order
1. Real NewsAPI implementation (unblock real sentiment data)
2. Cost analyzer integration (production billing)
3. API key validation (error handling)
4. Sentiment caching (cost reduction)
5. Integration tests (CI/CD confidence)
