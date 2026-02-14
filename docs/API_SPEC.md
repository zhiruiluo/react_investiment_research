# API_SPEC

## CLI contract
The project exposes a single CLI that returns JSON to stdout.

### Command
`python -m react_investment_research`

### Flags
- `--query` (required): User question or request.
- `--tickers` (optional): Comma-separated list of tickers.
- `--period` (optional): One of `1mo|3mo|6mo|1y` (default `3mo`).
- `--offline` (optional): Use mocked tool outputs only.
- `--use-llm` (optional): Enable LLM-based analysis (requires OPENAI_API_KEY or ANTHROPIC_API_KEY).
- `--report-cost` (optional): Include cost and token analysis in output (requires `--use-llm`).

### Example
`python -m react_investment_research --query "compare AAPL vs MSFT" --tickers AAPL,MSFT --period 3mo`

## Tool contracts

### Tool: `market_snapshot`
Inputs:
- `ticker` (str)
- `period` (str)
- `interval` (str, default `1d`)
- `benchmarks` (list[str], optional)

Outputs (JSON):
```json
{
  "ticker": "AAPL",
  "asof": "YYYY-MM-DD",
  "period": "3mo",
  "interval": "1d",
  "prices": {
    "start": 0,
    "end": 0,
    "return_pct": 0,
    "max_drawdown_pct": 0
  },
  "risk": {
    "volatility_ann_pct": 0,
    "atr_14": 0
  },
  "trend": {
    "sma_20": 0,
    "sma_50": 0,
    "trend_label": "bullish|bearish|sideways"
  },
  "volume": {
    "avg_20d": 0,
    "latest": 0,
    "zscore_latest": 0
  },
  "relative": [],
  "notes": []
}
```

Failure output:
```json
{"error":"NO_DATA","ticker":"XXXX","reason":"invalid ticker or empty history"}
```

### Tool: `fundamentals_events`
Inputs:
- `ticker` (str)
- `fields` (list[str])
- `include_calendar` (bool, default true)
- `lookback_days` (int, default 90)

Allowlist fields:
`marketCap`, `trailingPE`, `forwardPE`, `trailingEps`, `forwardEps`, `priceToBook`, `dividendYield`, `profitMargins`, `beta`, `sector`, `industry`

Outputs (JSON):
```json
{
  "ticker": "AAPL",
  "asof": "YYYY-MM-DD",
  "fundamentals": {},
  "calendar": {},
  "flags": []
}
```

Final output additions:
`tool_returns` contains raw tool payloads keyed by ticker (market_snapshot and fundamentals_events).
