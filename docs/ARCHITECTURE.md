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
2. Agent optionally infers tickers with LLM when tickers are omitted and `--use-llm` is enabled.
3. Agent validates tickers, scope, and tool budget.
4. Agent calls `market_snapshot` and `fundamentals_events`.
5. Tool outputs are validated against JSON schema.
6. Agent builds final JSON response.
7. Eval runner uses mock tool outputs for offline tests.

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

## Tool Registry (Dynamic Tool Routing)
The system uses a `ToolRegistry` pattern to enable scalable tool management and LLM-driven tool routing.

### Tool Specification
Each tool is defined by a `Tool` dataclass in `tools/registry.py`:
```python
@dataclass
class Tool:
    name: str                          # Unique tool identifier (e.g., "market_snapshot")
    handler: Callable                  # Function that executes the tool
    input_schema: dict                 # JSON schema for input validation
    output_schema: dict                # JSON schema for output validation
    description: str                   # Human-readable description for LLM
    usage_examples: list[str]          # Example queries where tool applies
    budget_per_ticker: int             # Max calls per ticker (e.g., 1 for market_snapshot)
```

### Central Registry
The `ToolRegistry` class manages all available tools:
```python
registry = ToolRegistry()
registry.register(Tool(
    name="market_snapshot",
    handler=market_snapshot.get_snapshot,
    input_schema={...},
    output_schema={...},
    description="Fetch technical analysis metrics...",
    usage_examples=["What's the trend for NVDA?", "Show me volatility"],
    budget_per_ticker=1
))
```

### LLM-Driven Tool Routing
When processing a query, the agent:
1. Passes query, tickers, and available tool descriptions to LLM via `llm.decide_tools()`
2. LLM returns JSON list of tools to invoke: `[{"tool": "market_snapshot", "tickers": ["NVDA", "AAPL"]}]`
3. Agent enforces per-tool budgets and global `max_tool_calls` cap
4. Agent executes only LLM-selected tools in the decided order

Example prompt to LLM:
```
Query: "Compare NVDQuery: "Compare NVDQuery: "Compare NVDQuery: "Compare NVDQuery: "Co technical analysis (returns, volatility, trend, drawdowns)
  Example usage: "What's the 1-year trend  or   Example usage: "als_events: Fetch company fundamentals and earnings (P/E, EPS, dividend)
  Example usage: "Wh  Example usage: "gs next quarter?"

Decide which tools to call for this query. Return JSON:
{"tools": [{"tool": "market_snapshot", "tickers": {"tools": [{"tool": "market_snapshot", "tickers": {" a new tool to the system:
1. Create tool module in `tools/` directory (e.g.1. Create tool modupy`)
2. Imple2. Imple2. Imple2. Implecepting `tickers` list, returning JSON per tool output schema
3. Define Tool spec with handler, schemas, description, examples, and budget
4. Register in agent initialization: `registry.register(sentiment_tool)`
5. Tool automatically becomes available to LLM for routing decisions

### Backward Compatibility
The system preserves optional backward compatibility via fallback pipeline:
- If `--use-llm` flag is omitted or LLM unavailable, agent defaults to calling both market_snapshot and fundamentals_events on all tickers
- Per-tool budgets still enforced even in fallback mode
```
