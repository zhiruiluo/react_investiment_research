# PRD

## Goal
Build a minimal ReAct-style investment research agent with two deterministic tools that return JSON-only outputs and a strict final response schema. The system MUST be implementable in 60-90 minutes and runnable on macOS with Python 3.11+.

## Users
- Individual analyst validating a ticker quickly.
- Engineering evaluator testing tool discipline and safety.
- QA tester verifying offline behavior.

## Core workflows
1. User provides a query with one or more tickers.
2. Agent calls `market_snapshot` for recent price and risk context.
3. Agent calls `fundamentals_events` for basic fundamentals and calendar items.
4. Agent composes a final JSON response conforming to the output schema.
5. Evaluator runs offline tests with mocked tool outputs.

## Required output format
Final response MUST be a JSON object with this shape:

```json
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

## Non-goals
- News scraping or sentiment analysis.
- Portfolio optimization or trade execution.
- Real-time streaming data.

## Constraints
- Tools MUST return JSON only, no prose.
- Max tool calls: 6. Max tickers: 5.
- Allowed periods: 1mo, 3mo, 6mo, 1y.
- All tests MUST run offline with mocks.
- Environment MUST use .venv, not global Python.

## Success criteria
- Agent produces valid JSON for all test cases.
- Offline tests pass without network access.
- Tool budget and schema guardrails enforced.
- User simulation step verifies output contract.
