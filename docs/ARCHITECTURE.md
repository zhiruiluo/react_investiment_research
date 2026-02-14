# ARCHITECTURE

## High-level system overview
A small CLI runs a ReAct agent that calls two tools. The tools fetch or read data, compute simple metrics, and return JSON. The agent validates tool outputs and produces a final JSON response that follows the required schema.

## Modules/components
- `cli`: Parses user input, invokes the agent, prints final JSON.
- `agent`: Orchestrates tool calls, enforces guardrails, assembles final output.
- `tools.market_snapshot`: Fetches OHLCV, computes returns, drawdowns, volatility, SMA, ATR, volume z-score.
- `tools.fundamentals_events`: Fetches allowed fundamentals and calendar data.
- `schemas`: JSON schema validation for tool outputs and final output.
- `eval`: Offline evaluation runner with mocked data.

## Data flow
1. CLI receives query and optional tickers.
2. Agent validates scope and tool budget.
3. Agent calls `market_snapshot` and `fundamentals_events`.
4. Tool outputs are validated against JSON schema.
5. Agent builds final JSON response.
6. Eval runner uses mock tool outputs for offline tests.

## Dependencies (minimal)
- Python 3.11+ (tested with 3.13.7)
- `yfinance` for live market data (optional at runtime)
- `jsonschema` for JSON schema validation
- `pandas`, `numpy` for technical analysis
- `openai` for OpenAI API (primary LLM provider, optional)
- `anthropic` for Anthropic Claude API (fallback LLM provider, optional)
- `python-dotenv` for environment variable loading
- `pytest` for testing

## Failure fallback rules
- If `yfinance` fails or network is unavailable, tools MUST return a JSON error object with `error`, `ticker`, and `reason`.
- If tool output is invalid JSON, the agent MUST retry once; if still invalid, return a final response with an error note in `limitations`.
- If no ticker is provided, agent MUST ask for one or use proxy tickers: SPY, QQQ, TLT, GLD.
