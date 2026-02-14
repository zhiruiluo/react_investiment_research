# Premium Tools & Tool Selection

## Overview

This document describes the tool selection and tiered access system for the React Investment Research agent.

## Tool Tiers

### Free Tools (Default)
- **market_snapshot**: Technical analysis metrics (returns, volatility, trend, drawdowns, volume z-score, ATR, SMA)
- **fundamentals_events**: Company fundamentals and upcoming events/earnings

By default, only free tools are available. Users do not need to specify anything to use free tools.

### Paid Tools
Premium tools require explicit opt-in via the `--tools` CLI flag. Pricing is tracked per tool and included in cost analysis.

**Available Paid Tools:**
- **sentiment_analysis** ($0.05/call): Analyze news and analyst sentiment for a stock. Combines news sentiment with analyst ratings consensus to identify bullish/bearish trends.

## Usage

### Default (Free Tools Only)
```bash
python -m react_investment_research --query "Analyze NVDA" --offline
```

This will use only `market_snapshot` and `fundamentals_events`.

### Selecting Specific Tools
```bash
python -m react_investment_research --query "Analyze NVDA" --offline --tools "market_snapshot"
```

### Using Paid Tools
```bash
# Use sentiment_analysis alone
python -m react_investment_research --query "What's the sentiment for NVDA?" --offline \
  --tickers NVDA --tools "sentiment_analysis"

# Combine sentiment_analysis with free tools
python -m react_investment_research --query "Analyze NVDA in detail" --offline \
  --tickers NVDA --tools "market_snapshot,fundamentals_events,sentiment_analysis"
```

### View Available Tools
```bash
python -m react_investment_research --help
```

The help text shows:
- All available tools
- Whether each tool is [FREE] or [PAID]
- Pricing per call for paid tools
- Default behavior (free tools only)

## Tool Filtering & Validation

The system validates tool selections and provides helpful error messages:

### Invalid Tool Error
```bash
$ python -m react_investment_research --query "Test" --offline --tools "invalid_tool"
```

Response:
```json
{
  "error": "Invalid tool(s): ['invalid_tool']. Available tools: ['fundamentals_events', 'market_snapshot']"
}
```

### Mixed Valid/Invalid Tools
If you specify both valid and invalid tools, the request is rejected:
```bash
$ python -m react_investment_research --query "Test" --offline --tools "market_snapshot,invalid_tool"
```

Response:
```json
{
  "error": "Invalid tool(s): ['invalid_tool']. Available tools: ['fundamentals_events', 'market_snapshot']"
}
```

## Architecture

### Tool Metadata
Each tool in the registry has metadata:
- `name`: Tool identifier
- `is_paid`: Boolean flag (False for free, True for paid)
- `pricing_usd_per_call`: Cost per call (0.0 for free tools, > 0.0 for paid)
- `description`: Displayed in LLM prompts with `[PAID]` label if applicable

### Validation Flow
1. User specifies `--tools` flag with comma-delimited list
2. CLI parses tool names and passes to `ResearchAgent`
3. Agent validates against full tool registry
4. If invalid: ValueError raised with available tools list
5. If valid: Filtered registry created with only specified tools
6. Tool availability shown to LLM in prompt

### Default Behavior
When no `--tools` flag specified:
- Agent filters registry to FREE tools only
- Secure by default: users can't accidentally access paid tools
- Cost tracking includes per-tool pricing

## Implementation Details

### Key Components

**[tools/registry.py](tools/registry.py)**
- `Tool` dataclass with `is_paid` and `pricing_usd_per_call` fields
- Validation: paid tools must have pricing > 0.0
- Methods:
  - `get_available_tool_names()` → Returns tool metadata dict
  - `validate_and_filter_tools(tool_names)` → Returns (valid, invalid) tuple
  - `create_filtered_registry(tool_names)` → Returns filtered ToolRegistry

**[agent.py](react_investment_research/agent.py)**
- `__init__` accepts optional `available_tools` parameter
- Method `_get_available_tools_registry()`:
  - If `available_tools` provided: validates and creates filtered registry
  - If None: defaults to FREE tools only
  - Raises ValueError with available tools list on validation error

**[cli.py](react_investment_research/cli.py)**
- `_get_tools_help_text()` generates dynamic help showing all tools with [FREE]/[PAID] labels
- `--tools` argument: comma-delimited list of tool names
- Error handler: Catches ValueError and returns JSON with error message
- Tool parsing: Strips whitespace, handles empty strings

### Test Coverage

**[tests/test_registry.py](tests/test_registry.py)** - 27 tests
- Tool creation with paid metadata
- Pricing validation (paid tools require pricing > 0)
- [PAID] label formatting
- Filtering methods (validate_and_filter_tools, create_filtered_registry)
- Metadata extraction (get_available_tool_names)

**[tests/test_paid_tools.py](tests/test_paid_tools.py)** - 7 tests
- Default behavior: free tools only
- Explicit tool selection
- Invalid tool rejection with error
- Mixed valid/invalid rejection
- Registry filtering verification
- Tool metadata accessibility

**[tests/test_cli.py](tests/test_cli.py)** - Various tests
- CLI help text displays available tools

## Adding New Tools

To add a new tool:

1. Define tool handler function (e.g., `sentiment_analysis()`)
2. Create Tool instance with metadata:
   ```python
   sentiment_tool = Tool(
       name="sentiment_analysis",
       handler=sentiment_analysis,
       is_paid=True,
       pricing_usd_per_call=0.05,  # Must be > 0 for paid tools
       # ... other properties
   )
   ```
3. Register in `agent._initialize_tool_registry()`:
   ```python
   registry.register(sentiment_tool)
   ```
4. Update help text in `cli._get_tools_help_text()` if hardcoded
5. Add tests for tool availability and pricing

## Cost Integration

Tool costs are tracked per tool based on `pricing_usd_per_call`. Cost analyzer integrates tool pricing into query cost calculations.

See [COST_IMPLEMENTATION.md](COST_IMPLEMENTATION.md) for cost tracking details.

## Future Enhancements

- Implement sentiment_analysis tool (user decision pending)
- Add cost limits per tier (e.g., free tier max $1/month)
- Implement authentication for premium tools
- Add usage telemetry
