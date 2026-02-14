# TASKS

## Build plan (fast implementation)
1. Create project layout and requirements.
2. Implement JSON schemas for tools and final output.
3. Implement `market_snapshot` with yfinance and computed metrics.
4. Implement `fundamentals_events` with allowlist mapping.
5. Implement agent guardrails (budget, schema, disclaimer, proxy tickers).
6. Implement CLI entrypoint that prints JSON.
7. Add offline mocks and evaluation runner.
8. Write tests for tools, guardrails, and output contract.

## Tests integrated by phase
1. After schemas: add schema validation tests.
2. After each tool: add unit tests using mocked data.
3. After agent: add guardrail tests.
4. Before finish: add CLI offline simulation test.
