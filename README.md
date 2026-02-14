# ReAct Investment Research Agent

A minimal, offline-capable AI agent for structured investment research with two deterministic tools and strict guardrails. Returns JSON-only outputs suitable for downstream analysis.

## Features

- **Two Core Tools**
  - `market_snapshot`: Returns price history, returns, volatility, trend, volume metrics
  - `fundamentals_events`: Returns allowlist-filtered fundamentals and earnings calendar
- **Strict Guardrails**
  - Max 6 tool calls per query
  - Max 5 tickers per query
  - Allowed periods: 1mo, 3mo, 6mo, 1y
  - Prompt injection hardening via strict JSON validation
  - Mandatory disclaimer: "Research summary, not financial advice."
- **Offline Testing**
  - All tests run without network access
  - Mocked tool outputs in JSON fixtures
  - Deterministic evaluation runner
- **Production-Ready JSON Outputs**
  - Strict schema validation on all responses
  - Retry logic for tool failures
  - Graceful degradation with limitation notes
- **Cost & Token Tracking** (optional)
  - Track LLM token usage and compute costs
  - Compare pricing between OpenAI and Anthropic
  - Batch cost analysis and monthly projections
  - 60-85% cost reduction strategies available
  - See [docs/COST_ANALYSIS.md](docs/COST_ANALYSIS.md) and [docs/OPTIMIZATION_STRATEGIES.md](docs/OPTIMIZATION_STRATEGIES.md)

## Quick Start

### Setup (macOS, Python 3.11+)

```bash
# Clone/enter workspace
cd react_investment_research

# Create and activate virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Run Tests

```bash
python -m pytest -q
```

Expected output: `35 passed` (16 unit tests + 19 integration tests with real LLM)

### Run Offline Simulation

```bash
python scripts/simulate_user.py --query "compare AAPL vs MSFT" --tickers AAPL,MSFT --period 3mo
```

Returns JSON with comparative analysis of both stocks using mocked data.

### Run CLI

```bash
# Offline mode (recommended for reproducibility)
python -m react_investment_research --offline --query "trend for AAPL" --tickers AAPL --period 3mo

# Live mode (requires yfinance network access)
python -m react_investment_research --query "compare SPY vs QQQ" --tickers SPY,QQQ --period 6mo

# With LLM for intelligent analysis
# Option 1: OpenAI (primary)
OPENAI_API_KEY=sk-... python -m react_investment_research --use-llm \
  --query "compare AAPL vs MSFT performance" --tickers AAPL,MSFT --period 3mo

# Option 2: Anthropic Claude (fallback)
ANTHROPIC_API_KEY=sk-ant-... python -m react_investment_research --use-llm \
  --query "compare AAPL vs MSFT performance" --tickers AAPL,MSFT --period 3mo
```

## Output Schema

All final outputs conform to this JSON schema:

```json
{
  "query": "user question",
  "tickers": ["AAPL", "MSFT"],
  "summary": {
    "thesis_bullets": ["AAPL: bullish trend, return 8.33% over 3mo"],
    "risks": ["AAPL: high volatility (22.5%)"]
  },
  "fundamentals": {
    "AAPL": {
      "marketCap": 2800000000000,
      "trailingPE": 25.1,
      "forwardPE": 23.4,
      "trailingEps": 5.12,
      "forwardEps": 6.28
    }
  },
  "tool_returns": {
    "AAPL": {
      "market_snapshot": {"ticker": "AAPL", "period": "3mo", "prices": {"return_pct": 8.33}},
      "fundamentals_events": {"ticker": "AAPL", "fundamentals": {"trailingPE": 25.1}}
    }
  },
  "data_used": ["market_snapshot:AAPL", "fundamentals_events:AAPL"],
  "tool_calls": [
    {"name": "market_snapshot", "args": {...}},
    {"name": "fundamentals_events", "args": {...}}
  ],
  "limitations": [],
  "disclaimer": "Research summary, not financial advice."
}
```

## Tool Contracts

### `market_snapshot(ticker, period, interval="1d", benchmarks=[])`

Returns technical analysis snapshot for a single ticker over a time period.

**Output:**
```json
{
  "ticker": "AAPL",
  "asof": "2026-01-31",
  "period": "3mo",
  "interval": "1d",
  "prices": {
    "start": 180.0,
    "end": 195.0,
    "return_pct": 8.33,
    "max_drawdown_pct": -6.5
  },
  "risk": {
    "volatility_ann_pct": 22.5,
    "atr_14": 3.1
  },
  "trend": {
    "sma_20": 191.2,
    "sma_50": 187.9,
    "trend_label": "bullish|bearish|sideways"
  },
  "volume": {
    "avg_20d": 56000000,
    "latest": 62000000,
    "zscore_latest": 1.2
  },
  "relative": [],
  "notes": []
}
```

### `fundamentals_events(ticker, fields=[], include_calendar=true, lookback_days=90)`

Returns fundamental metrics and upcoming events for a ticker. Only allowlisted fields are returned.

**Allowlist:** `marketCap`, `trailingPE`, `forwardPE`, `trailingEps`, `forwardEps`, `priceToBook`, `dividendYield`, `profitMargins`, `beta`, `sector`, `industry`

**Output:**
```json
{
  "ticker": "AAPL",
  "asof": "2026-01-31",
  "fundamentals": {
    "marketCap": 2800000000000,
    "trailingPE": 25.1,
    "forwardPE": 23.4,
    "trailingEps": 5.12,
    "forwardEps": 6.28
  },
  "calendar": {
    "Earnings Date": {"2026-02-01": "2026-02-01"}
  },
  "flags": []
}
```

## Cost & Token Tracking

Track and analyze LLM usage costs with the optional cost analysis feature.

### Enable Cost Reporting in Output

```bash
# Include cost analysis in JSON output
python -m react_investment_research --use-llm \
  --query "compare AAPL vs MSFT" \
  --tickers AAPL,MSFT \
  --period 3mo \
  --report-cost
```

Output includes cost breakdown:
```json
{
  "cost_analysis": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "tokens": {
      "input": 1250,
      "output": 340,
      "total": 1590,
      "per_ticker": 795
    },
    "cost": {
      "total_usd": 0.000392,
      "input_cost_usd": 0.000188,
      "output_cost_usd": 0.000204,
      "cost_per_ticker_usd": 0.000196
    }
  }
}
```

### Cost Analysis CLI

```bash
# View session cost summary
python -m react_investment_research.cost_analyzer_cli session

# Compare OpenAI vs Anthropic pricing
python -m react_investment_research.cost_analyzer_cli compare

# Estimate batch query costs
python -m react_investment_research.cost_analyzer_cli batch --num-queries 10 --num-tickers 2

# Project monthly costs
python -m react_investment_research.cost_analyzer_cli monthly --queries-per-day 20
```

### Cost Optimization

See [docs/OPTIMIZATION_STRATEGIES.md](docs/OPTIMIZATION_STRATEGIES.md) for 4-level optimization roadmap:

- **Level 1** (5 min): Reduce token limits, adjust model selection → **20% savings**
- **Level 2** (2-4 hrs): Implement caching, prompt compression → **50% savings**
- **Level 3** (1-2 weeks): Fine-tune domain-specific model → **75% savings**
- **Level 4** (2+ weeks): Hybrid local + remote LLM → **85% savings**

## Architecture

```
react_investment_research/
├── __init__.py
├── __main__.py          # CLI entrypoint
├── cli.py               # Argument parsing
├── agent.py             # ReAct agent with guardrails
├── schemas.py           # JSON schema definitions
├── mocks.py             # Offline mock tool implementations
├── eval.py              # Evaluation runner
├── tools/
│   ├── __init__.py
│   ├── market_snapshot.py  # Technical analysis tool
│   ├── fundamentals_events.py  # Fundamentals tool
│   └── providers.py     # yfinance abstraction
└── data/
    └── mocks/           # JSON fixtures for offline testing
        ├── market_snapshot_*.json
        └── fundamentals_events_*.json

tests/
├── test_agent.py
├── test_market_snapshot.py
└── test_fundamentals_events.py

scripts/
└── simulate_user.py     # Deterministic CLI simulation

docs/
├── PRD.md               # Product requirements
├── ARCHITECTURE.md      # System design
├── API_SPEC.md          # Tool contracts
├── CONVENTIONS.md       # Code style and error handling
├── ENV.md               # Setup and run instructions
├── TEST_PLAN.md         # Test strategy
└── TASKS.md             # Build plan
```

## Guardrails in Action

1. **Tool Budget**: Query with 5+ tickers gets truncated to fit max_tool_calls (6).
   ```
   "limitations": ["Tool budget exceeded. Skipping some tickers."]
   ```

2. **Schema Validation**: Invalid tool output triggers one retry, then degrades gracefully.

3. **Proxy Tickers**: Query with no tickers auto-uses SPY, QQQ, TLT, GLD.
   ```
   "limitations": ["No tickers provided. Using proxy tickers."]
   ```

4. **Disclaimer**: Always included in final output.
   ```
   "disclaimer": "Research summary, not financial advice."
   ```

## Testing

### Run All Tests
```bash
python -m pytest -q
```

### Run Specific Test
```bash
python -m pytest tests/test_agent.py::test_agent_offline_schema -v
```

### Test Coverage
- Schema validation for tool outputs and final response
- Tool computation accuracy (returns, drawdown, SMA, ATR, volatility)
- Allowlist filtering for fundamentals
- Guardrail enforcement (budget, period validation, proxy tickers)
- Offline simulation with mocked data

## Example Queries

### Compare Two Stocks
```bash
python -m react_investment_research --offline \
  --query "compare AAPL vs MSFT performance" \
  --tickers AAPL,MSFT \
  --period 3mo
```

### Macro Proxy Analysis (No Tickers)
```bash
python -m react_investment_research --offline \
  --query "how are the major indexes performing?" \
  --period 6mo
```

### Single Ticker Risk Check
```bash
python -m react_investment_research --offline \
  --query "what is the risk profile of AAPL?" \
  --tickers AAPL \
  --period 1y
```

## Optional: LLM Integration

The system optionally integrates **Claude** (via Anthropic API) for intelligent reasoning about market data.

### Setup

1. Get an Anthropic API key from [console.anthropic.com](https://console.anthropic.com)
2. Set environment variable:
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   ```

### Usage

Enable LLM reasoning with `--use-llm`:

```bash
python -m react_investment_research --use-llm \
  --query "which stock has better risk-adjusted returns?" \
  --tickers AAPL,MSFT --period 6mo
```

**Output with LLM:**
```json
{
  "summary": {
    "thesis_bullets": [
      "AAPL shows strong momentum with positive returns and controlled volatility",
      "MSFT exhibits higher profile with elevated volatility and larger drawdown risk"
    ],
    "risks": [
      "Both tech stocks correlated to broad market sentiment",
      "MSFT's concentrated exposure to AI narrative creates tail risk"
    ]
  }
}
```

### Behavior

- If `--use-llm` is set and `ANTHROPIC_API_KEY` exists → Claude generates insights
- If `--use-llm` is set but no API key → Falls back to deterministic analysis
- If `--offline` is set → LLM is automatically disabled (remains deterministic)
- LLM errors are logged in `limitations` field

## Dependencies

- `yfinance` — Market data (optional at runtime if using --offline)
- `pandas` — Data manipulation
- `numpy` — Numerical computing
- `jsonschema` — Schema validation
- `anthropic` — Claude API client (optional, for LLM integration)
- `pytest` — Testing (dev only)

## Limitations & Future Work

- No news or sentiment analysis
- No portfolio optimization
- No real-time streaming (snapshots only)
- Fundamentals via yfinance `.info` only (no SEC filings)
- Calendar data limited to yfinance availability

## Development

Install in editable mode:
```bash
python -m pip install -e .
```

Then make changes to `react_investment_research/` and re-run tests.

## License

Internal research tool.
