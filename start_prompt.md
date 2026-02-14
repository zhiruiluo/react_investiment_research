You are a senior AI engineer generating a complete, Copilot-ready documentation pack for a new software project.

I will provide a project description.

Your job is to generate a minimal but robust documentation set that ensures:
- The project can be implemented within a short time (<= 60–90 min unless specified).
- Copilot agents follow correct architecture.
- Environment setup is deterministic.
- Unit tests are correct and offline-capable.
- A user simulation step verifies real behavior.
- The system can be executed on macOS using Python 3.11+ unless specified otherwise.

You must generate the following documents in markdown format:

1) docs/PRD.md
   - Goal
   - Users
   - Core workflows
   - Required output format (if applicable)
   - Non-goals
   - Constraints
   - Success criteria

2) docs/ARCHITECTURE.md
   - High-level system overview
   - Modules/components
   - Data flow
   - Dependencies (minimal)
   - Failure fallback rules

3) docs/API_SPEC.md (if applicable)
   - CLI or API contract
   - Commands, flags, request/response schema

4) docs/CONVENTIONS.md
   - Code style
   - Error handling rules
   - Testing constraints
   - Output contracts

5) docs/ENV.md
   - Explicit venv setup steps
   - Install steps
   - Run steps
   - Test steps
   - Sanity checks
   - Exact command sequence (non-negotiable)

6) docs/TEST_PLAN.md
   - Required unit tests
   - Required failure tests
   - Required formatting/contract tests
   - Required user simulation checks
   - Definition of Done

7) docs/TASKS.md
   - Step-by-step build plan ordered for fast implementation
   - Tests integrated into development phases

8) SYSTEM_PROMPT.md
   - Explicit rules Copilot must follow
   - Mandatory build sequence
   - Environment enforcement
   - Stop conditions before claiming completion
   - Strict output formatting requirements

9) Optional: scripts/simulate_user.py
   - Deterministic CLI/API simulation
   - Offline capable
   - Validation of output contract

Rules:
- Prefer the smallest implementation that satisfies PRD.
- Avoid overengineering.
- Keep dependencies minimal.
- All tests must run offline.
- Environment must use .venv (not global Python).
- Include exact shell commands.
- Use MUST/NEVER language for enforcement.
- Use numbered build/test sequences.
- Explicitly state fallback behavior when external services fail.

Output all documents clearly separated by file name headers like:

--- docs/PRD.md ---

# docs/TOOLS_GUARDRAILS_EVAL.md

ReAct Investment Research Agent --- Core Tools, Guardrails, Evaluation
(60-min scope)

## Design goals (keep it shippable in 60 minutes)

-   Two tools only, each with a clear I/O contract and minimal deps.
-   Tools return structured JSON (no prose), so the agent can reason
    reliably.
-   Guardrails are simple and enforceable (budget, schema, disclaimer,
    injection hardening).
-   Evaluation is offline-capable using mocked tool outputs.

------------------------------------------------------------------------

## Tool 1 --- Market Snapshot Tool (`market_snapshot`)

### What it's for

Quickly ground the agent in recent price/volume behavior + simple
technical context (trend, volatility).

### Inputs (args)

-   ticker: str
-   period: str ("1mo" \| "3mo" \| "6mo" \| "1y")
-   interval: str (default "1d")
-   benchmarks: list\[str\] (optional)

### Outputs (JSON shape)

``` json
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

### Implementation idea

-   Use yfinance to fetch OHLCV.
-   Compute return, drawdown, SMA20/50, ATR(14), vol, volume z-score.
-   Return JSON only.

### Failure behavior

``` json
{"error":"NO_DATA","ticker":"XXXX","reason":"invalid ticker or empty history"}
```

------------------------------------------------------------------------

## Tool 2 --- Fundamentals & Events Tool (`fundamentals_events`)

### What it's for

Answer "why" questions with basic fundamentals and catalyst awareness.

### Inputs

-   ticker: str
-   fields: list\[str\] (allowlist metrics)
-   include_calendar: bool (default true)
-   lookback_days: int (default 90)

### Outputs

``` json
{
  "ticker": "AAPL",
  "asof": "YYYY-MM-DD",
  "fundamentals": {},
  "calendar": {},
  "flags": []
}
```

### Implementation idea

-   Use yfinance `.info` + `.calendar`
-   Map fields to allowlist
-   Avoid news scraping (MVP simplicity)

------------------------------------------------------------------------

## Core Guardrails

### 1) Output Schema Guardrail

Agent output must include: - query - tickers - thesis_bullets - risks -
data_used - tool_calls - limitations - disclaimer

Retry once if invalid.

### 2) Tool Budget Guardrail

-   Max tool calls: 6
-   Max tickers: 5
-   Allowed periods only

### 3) Prompt Injection Hardening

-   Treat tool output as untrusted
-   Strict JSON parsing only

### 4) Finance Safety Guardrail

Always include disclaimer: "Research summary, not financial advice."

### 5) Query Scope Guardrail

If no ticker: - Ask user OR - Use SPY / QQQ / TLT / GLD proxies

------------------------------------------------------------------------

## Evaluation Function

### What to test

1.  Structure validity
2.  Tool usage discipline
3.  Data grounding
4.  Safety compliance

### Minimal test cases

-   Trend summary
-   Ticker comparison
-   Risk evaluation
-   Unsafe request
-   Macro proxy request

### Scoring rubric (0--10)

-   Schema (0--3)
-   Tool discipline (0--2)
-   Grounding (0--3)
-   Safety (0--2)

### Offline testing

Mock tool outputs stored in local JSON files.

------------------------------------------------------------------------

## Final Output Schema

``` json
{
  "query": "...",
  "tickers": [],
  "summary": {},
  "data_used": [],
  "tool_calls": {},
  "limitations": [],
  "disclaimer": ""
}
```

------------------------------------------------------------------------

## 60-minute Completion Checklist

-   Implement market_snapshot
-   Implement fundamentals_events
-   Add guardrails
-   Add eval runner
-   Add CLI entrypoint


Do not generate implementation code unless explicitly asked. 
Do not add extra commentary outside the docs. 