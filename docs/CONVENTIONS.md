# CONVENTIONS

## Code style
- Python 3.11+.
- Prefer small, pure functions.
- Keep tool logic deterministic given the same inputs.
- Use type hints for public functions.

## Error handling rules
- Tools MUST return JSON objects on all paths.
- Do not raise uncaught exceptions from tool entrypoints.
- If external data is unavailable, return `error`, `ticker`, `reason`.

## Testing constraints
- All tests MUST run offline.
- Network calls MUST be mocked.
- Use fixed timestamps for deterministic assertions.

## Output contracts
- Tool outputs MUST be JSON only.
- Final agent output MUST match the required schema.
- Always include disclaimer: "Research summary, not financial advice.".
