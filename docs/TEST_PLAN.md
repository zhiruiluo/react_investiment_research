# TEST_PLAN

## Required unit tests
- `market_snapshot` computes return, drawdown, SMA20/50, ATR(14), volatility, volume z-score using fixed mock OHLCV.
- `fundamentals_events` maps only allowlist fields and ignores unknown fields.
- Final output schema validation passes for a normal query.

## Required failure tests
- Invalid ticker returns `error` JSON from tools.
- Tool output invalid JSON triggers one retry then fails gracefully.
- Exceeding tool budget is rejected.

## Required formatting/contract tests
- Tool outputs are JSON objects only, no extra keys outside schema.
- Final response includes `disclaimer` and `limitations` fields.

## Required user simulation checks
- Offline simulation runs the CLI with `--offline` and verifies JSON schema.
- Macro proxy query with no tickers uses SPY/QQQ/TLT/GLD.

## Definition of Done
- All unit and contract tests pass offline.
- CLI produces valid JSON for sample queries.
- Guardrails enforce tool budget and output schema.
