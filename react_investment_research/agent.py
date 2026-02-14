from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from . import mocks
from .cost_analyzer import CostAnalyzer, get_global_analyzer
from .llm import LLMClient
from .schemas import validate_schema
from .tools import market_snapshot, fundamentals_events
from .tools.sentiment_analysis import sentiment_analysis
from .tools.providers import YFinanceProvider
from .tools.registry import Tool, ToolRegistry


def _safe_output(query: str, tickers: List[str]) -> Dict[str, Any]:
    return {
        "query": query,
        "tickers": tickers,
        "summary": {"thesis_bullets": [], "risks": []},
        "tickers_source": "explicit",
        "tickers_inferred": [],
        "fundamentals": {},
        "tool_returns": {},
        "data_used": [],
        "tool_calls": [],
        "limitations": [],
        "disclaimer": "Research summary, not financial advice.",
        "cost_analysis": None,
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


class ResearchAgent:
    def __init__(self, offline: bool = False, use_llm: bool = True, track_costs: bool = True, available_tools: Optional[List[str]] = None) -> None:
        self.offline = offline
        self.use_llm = use_llm and not offline
        self.llm = LLMClient() if self.use_llm else None
        self.track_costs = track_costs and self.use_llm
        self.max_tool_calls = 6
        self.max_tickers = 5
        self.allowed_periods = {"1mo", "3mo", "6mo", "1y"}
        self.proxy_tickers = ["SPY", "QQQ", "TLT", "GLD"]
        self.provider = YFinanceProvider()
        
        # Initialize full registry first
        self._full_registry = self._initialize_tool_registry()
        
        # Filter to available tools (default to free-tier tools only)
        self.registry = self._get_available_tools_registry(available_tools)

    def _initialize_tool_registry(self) -> ToolRegistry:
        """Initialize and return the tool registry with market_snapshot and fundamentals_events."""
        registry = ToolRegistry()
        
        # Define market_snapshot tool
        market_snapshot_tool = Tool(
            name="market_snapshot",
            handler=market_snapshot,
            input_schema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                    "period": {"type": "string"},
                    "interval": {"type": "string"},
                    "benchmarks": {"type": "array"},
                },
                "required": ["ticker", "period"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                    "period": {"type": "string"},
                    "prices": {"type": "object"},
                    "trend": {"type": "object"},
                    "risk": {"type": "object"},
                    "volume": {"type": "object"},
                },
            },
            description="Fetch technical analysis metrics (returns, volatility, trend, drawdowns, volume z-score, ATR, SMA)",
            usage_examples=[
                "What's the 1-year trend for NVDA?",
                "Show me volatility for AAPL",
                "Compare price movements for tech stocks",
            ],
            budget_per_ticker=1,
        )
        registry.register(market_snapshot_tool)
        
        # Define fundamentals_events tool
        fundamentals_tool = Tool(
            name="fundamentals_events",
            handler=fundamentals_events,
            input_schema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                    "fields": {"type": "array"},
                    "include_calendar": {"type": "boolean"},
                    "lookback_days": {"type": "integer"},
                },
                "required": ["ticker"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                    "fundamentals": {"type": "object"},
                    "calendar": {"type": "array"},
                },
            },
            description="Fetch company fundamentals (P/E, EPS, market cap, dividend, etc.) and upcoming earnings calendar",
            usage_examples=[
                "What's NVDA's P/E ratio and earnings next quarter?",
                "Show me EPS and dividend yield for AAPL",
                "When's the next earnings date?",
            ],
            budget_per_ticker=1,
        )
        registry.register(fundamentals_tool)
        
        # Define sentiment_analysis tool (paid)
        from .tools.sentiment_analysis import SENTIMENT_ANALYSIS_SCHEMA, SENTIMENT_ANALYSIS_OUTPUT_SCHEMA
        sentiment_tool = Tool(
            name="sentiment_analysis",
            handler=sentiment_analysis,
            input_schema=SENTIMENT_ANALYSIS_SCHEMA,
            output_schema=SENTIMENT_ANALYSIS_OUTPUT_SCHEMA,
            description="Analyze news and analyst sentiment for a stock. Provides sentiment score, components (news vs analyst), and trend analysis.",
            usage_examples=[
                "What's the sentiment for NVDA?",
                "Is there positive news about AAPL?",
                "Compare sentiment between tech stocks",
            ],
            budget_per_ticker=1,
            is_paid=True,
            pricing_usd_per_call=0.05,
        )
        registry.register(sentiment_tool)
        
        return registry

    def _get_available_tools_registry(self, requested_tools: Optional[List[str]]) -> ToolRegistry:
        """Get the tools registry filtered to available tools.
        
        Args:
            requested_tools: List of specific tools to use, or None to use default
            
        Returns:
            Filtered ToolRegistry
            
        Raises:
            ValueError: If invalid tools are requested
        """
        if requested_tools:
            # User explicitly requested specific tools
            valid, invalid = self._full_registry.validate_and_filter_tools(requested_tools)
            if invalid:
                available = self._full_registry.list_names()
                raise ValueError(
                    f"Invalid tool(s): {invalid}. Available tools: {available}"
                )
            # Create filtered registry with requested tools
            return self._full_registry.create_filtered_registry(valid)
        else:
            # Default: use only FREE tools for non-paying users
            free_tools = [
                name for name, tool in self._full_registry.get_all().items()
                if not tool.is_paid
            ]
            return self._full_registry.create_filtered_registry(free_tools)

    def _validate_tickers(self, tickers: List[str]) -> Tuple[List[str], List[str]]:
        valid: List[str] = []
        invalid: List[str] = []
        for ticker in tickers:
            try:
                info = self.provider.get_info(ticker)
            except Exception:
                info = {}
            if info:
                valid.append(ticker)
            else:
                invalid.append(ticker)
        return valid, invalid

    def _decide_and_call_tools_llm(
        self,
        query: str,
        tickers: List[str],
        period: str,
        tool_calls: List[Dict[str, Any]],
        limitations: List[str],
    ) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        """Let LLM decide which tools to call and execute them.
        
        Returns:
            (snapshots, fundamentals_by_ticker, tool_returns)
        """
        snapshots: Dict[str, Dict[str, Any]] = {}
        fundamentals_by_ticker: Dict[str, Dict[str, Any]] = {}
        tool_returns: Dict[str, Dict[str, Any]] = {}
        
        # Get LLM tool routing decision
        tools_description = self.registry.to_prompt_description()
        tool_decision = self.llm.decide_tools(query, tickers, tools_description) if self.llm else {}
        
        if tool_decision.get("llm_error"):
            limitations.append(f"LLM tool routing failed: {tool_decision['llm_error']}")
            # Fallback to all tools
            tools_to_call = [
                {"tool": "market_snapshot", "tickers": tickers},
                {"tool": "fundamentals_events", "tickers": tickers},
            ]
        else:
            tools_to_call = tool_decision.get("tools", [])
        
        # Execute tools as decided by LLM
        for tool_spec in tools_to_call:
            tool_name = tool_spec.get("tool")
            target_tickers = tool_spec.get("tickers", [])
            
            # Validate tool exists in registry
            if not self.registry.get(tool_name):
                limitations.append(f"Invalid tool requested by LLM: {tool_name}")
                continue
            
            # Execute for each ticker
            for ticker in target_tickers:
                if tool_name == "market_snapshot":
                    snapshot = self._call_tool(
                        "market_snapshot",
                        {"ticker": ticker, "period": period, "interval": "1d", "benchmarks": []},
                        tool_calls,
                        limitations,
                    )
                    snapshots[ticker] = snapshot
                    if ticker not in tool_returns:
                        tool_returns[ticker] = {}
                    tool_returns[ticker]["market_snapshot"] = snapshot
                    
                elif tool_name == "fundamentals_events":
                    fundamentals = self._call_tool(
                        "fundamentals_events",
                        {"ticker": ticker, "fields": [], "include_calendar": True, "lookback_days": 90},
                        tool_calls,
                        limitations,
                    )
                    fundamentals_by_ticker[ticker] = fundamentals.get("fundamentals", {})
                    if ticker not in tool_returns:
                        tool_returns[ticker] = {}
                    tool_returns[ticker]["fundamentals_events"] = fundamentals
                
                elif tool_name == "sentiment_analysis":
                    sentiment = self._call_tool(
                        "sentiment_analysis",
                        {"ticker": ticker, "lookback_days": 30},
                        tool_calls,
                        limitations,
                    )
                    if ticker not in tool_returns:
                        tool_returns[ticker] = {}
                    tool_returns[ticker]["sentiment_analysis"] = sentiment
        
        return snapshots, fundamentals_by_ticker, tool_returns

    def _call_tool(
        self,
        name: str,
        args: Dict[str, Any],
        tool_calls: List[Dict[str, Any]],
        limitations: List[str],
    ) -> Dict[str, Any]:
        tool_calls.append({"name": name, "args": args})
        if self.offline:
            tool_func = getattr(mocks, name)
        else:
            if name == "market_snapshot":
                tool_func = market_snapshot
            elif name == "fundamentals_events":
                tool_func = fundamentals_events
            elif name == "sentiment_analysis":
                tool_func = sentiment_analysis
            else:
                raise ValueError(f"Unknown tool: {name}")

        payload = tool_func(**args)
        ok, error = validate_schema(name, payload)
        if ok:
            return payload

        payload = tool_func(**args)
        ok, error = validate_schema(name, payload)
        if ok:
            return payload

        limitations.append(f"{name} output invalid: {error}")
        return {"error": "INVALID_OUTPUT", "ticker": args.get("ticker", ""), "reason": error or "schema"}

    def _summarize_snapshot(self, ticker: str, snapshot: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        if "error" in snapshot:
            return f"{ticker}: snapshot unavailable", "Data unavailable"
        trend = snapshot["trend"]["trend_label"]
        ret = snapshot["prices"]["return_pct"]
        vol = snapshot["risk"]["volatility_ann_pct"]
        thesis = f"{ticker}: {trend} trend, return {ret:.2f}% over {snapshot['period']}"
        risk = None
        if vol >= 40.0:
            risk = f"{ticker}: high volatility ({vol:.1f}%)"
        if snapshot["prices"]["max_drawdown_pct"] <= -20.0:
            risk = f"{ticker}: large drawdown ({snapshot['prices']['max_drawdown_pct']:.1f}%)"
        return thesis, risk

    def _llm_summarize(
        self,
        query: str,
        tickers: List[str],
        snapshots: Dict[str, Dict[str, Any]],
        fundamentals: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Use LLM to generate summary from tool outputs."""
        if not self.llm or not self.llm.enabled:
            return {"thesis_bullets": [], "risks": []}
        tool_outputs = {"snapshots": snapshots, "fundamentals": fundamentals}
        return self.llm.generate_summary(query, tickers, tool_outputs)

    def run(self, query: str, tickers: Optional[List[str]] = None, period: str = "3mo") -> Dict[str, Any]:
        tickers = [t.upper() for t in (tickers or []) if t]
        tickers_source = "explicit" if tickers else "proxy"
        tickers_inferred: List[str] = []
        limitations: List[str] = []

        if not tickers:
            if self.use_llm and self.llm and self.llm.enabled and not self.offline:
                inference = self.llm.infer_tickers(query)
                inferred_raw = [t.upper() for t in inference.get("tickers", []) if t]
                seen = set()
                tickers_inferred = []
                for ticker in inferred_raw:
                    if ticker in seen:
                        continue
                    tickers_inferred.append(ticker)
                    seen.add(ticker)
                    if len(tickers_inferred) >= self.max_tickers:
                        break
                if inference.get("llm_error"):
                    limitations.append(f"LLM ticker inference failed: {inference['llm_error']}")
                valid, invalid = self._validate_tickers(tickers_inferred)
                if invalid:
                    limitations.append(
                        f"Invalid tickers inferred: {invalid}. Please provide explicit tickers."
                    )
                if valid:
                    tickers = valid
                    tickers_source = "llm"
                else:
                    tickers = list(self.proxy_tickers)
                    tickers_source = "proxy"
                    limitations.append("No valid tickers inferred. Using proxy tickers.")
            else:
                tickers = list(self.proxy_tickers)
                tickers_source = "proxy"
                limitations.append("No tickers provided. Using proxy tickers.")

        if len(tickers) > self.max_tickers:
            limitations.append("Too many tickers provided. Truncating to max allowed.")
            tickers = tickers[: self.max_tickers]

        if period not in self.allowed_periods:
            limitations.append("Invalid period provided. Using default 3mo.")
            period = "3mo"

        output = _safe_output(query, tickers)
        output["tickers_source"] = tickers_source
        output["tickers_inferred"] = tickers_inferred
        output["limitations"].extend(limitations)

        if self.use_llm and (not self.llm or not self.llm.enabled):
            output["limitations"].append(
                "LLM disabled: missing API key or client unavailable."
            )

        max_tickers_for_budget = self.max_tool_calls // 2
        tickers_for_calls = tickers
        if len(tickers) > max_tickers_for_budget:
            output["limitations"].append("Tool budget exceeded. Skipping some tickers.")
            tickers_for_calls = tickers[:max_tickers_for_budget]

        tool_calls: List[Dict[str, Any]] = []
        data_used: List[str] = []
        thesis_bullets: List[str] = []
        risks: List[str] = []
        snapshots: Dict[str, Dict[str, Any]] = {}
        fundamentals_by_ticker: Dict[str, Dict[str, Any]] = {}
        tool_returns: Dict[str, Dict[str, Any]] = {}

        # Use LLM-driven tool routing or fallback pipeline
        if self.use_llm and self.llm and self.llm.enabled:
            snapshots, fundamentals_by_ticker, tool_returns = self._decide_and_call_tools_llm(
                query, tickers_for_calls, period, tool_calls, output["limitations"]
            )
            # Update data_used from tool_returns
            for ticker, tools_dict in tool_returns.items():
                for tool_name in tools_dict.keys():
                    data_used.append(f"{tool_name}:{ticker}")
            
            # Generate thesis/risks from snapshots
            for ticker in snapshots:
                thesis, risk = self._summarize_snapshot(ticker, snapshots[ticker])
                thesis_bullets.append(thesis)
                if risk:
                    risks.append(risk)
            
            # Check for fundamentals errors
            for ticker, tools_dict in tool_returns.items():
                if "fundamentals_events" in tools_dict:
                    fundamentals = tools_dict["fundamentals_events"]
                    if "error" in fundamentals:
                        output["limitations"].append(f"{ticker}: fundamentals unavailable")
        else:
            # Fallback pipeline: call all available tools for all tickers
            for ticker in tickers_for_calls:
                tool_names = self.registry.list_names()
                
                for tool_name in tool_names:
                    tool_obj = self.registry.get(tool_name)
                    if not tool_obj:
                        continue
                    
                    # Build args based on tool name
                    if tool_name == "market_snapshot":
                        args = {"ticker": ticker, "period": period, "interval": "1d", "benchmarks": []}
                    elif tool_name == "fundamentals_events":
                        args = {"ticker": ticker, "fields": [], "include_calendar": True, "lookback_days": 90}
                    elif tool_name == "sentiment_analysis":
                        args = {"ticker": ticker, "lookback_days": 30}
                    else:
                        # Skip unknown tools
                        continue
                    
                    result = self._call_tool(tool_name, args, tool_calls, output["limitations"])
                    
                    data_used.append(f"{tool_name}:{ticker}")
                    
                    # Store results by tool type
                    if tool_name == "market_snapshot":
                        snapshots[ticker] = result
                    elif tool_name == "fundamentals_events":
                        fundamentals_by_ticker[ticker] = result.get("fundamentals", {})
                    
                    if ticker not in tool_returns:
                        tool_returns[ticker] = {}
                    tool_returns[ticker][tool_name] = result
                
                # Generate thesis/risks from snapshots if available
                if ticker in snapshots:
                    thesis, risk = self._summarize_snapshot(ticker, snapshots[ticker])
                    thesis_bullets.append(thesis)
                    if risk:
                        risks.append(risk)
                
                # Check for fundamentals errors
                if ticker in tool_returns and "fundamentals_events" in tool_returns[ticker]:
                    fundamentals = tool_returns[ticker]["fundamentals_events"]
                    if "error" in fundamentals:
                        output["limitations"].append(f"{ticker}: fundamentals unavailable")

        if self.llm and self.llm.enabled:
            llm_summary = self._llm_summarize(query, tickers_for_calls, snapshots, fundamentals_by_ticker)
            if llm_summary.get("thesis_bullets"):
                thesis_bullets = llm_summary["thesis_bullets"]
            if llm_summary.get("risks"):
                risks = llm_summary["risks"]
            if llm_summary.get("llm_error"):
                output["limitations"].append(f"LLM error: {llm_summary['llm_error']}")
            
            # Track costs if enabled
            if self.track_costs and llm_summary.get("llm_tokens"):
                analyzer = get_global_analyzer()
                analysis = analyzer.track_query(
                    query=query,
                    tickers=tickers_for_calls,
                    period=period,
                    provider=llm_summary.get("llm_provider", "unknown"),
                    model=llm_summary.get("llm_model", "unknown"),
                    input_tokens=llm_summary["llm_tokens"].get("input", 0),
                    output_tokens=llm_summary["llm_tokens"].get("output", 0),
                )
                output["cost_analysis"] = analysis.to_dict()

        output["summary"] = {"thesis_bullets": thesis_bullets, "risks": risks}
        output["fundamentals"] = fundamentals_by_ticker
        output["tool_returns"] = _json_safe(tool_returns)
        output["data_used"] = data_used
        output["tool_calls"] = tool_calls

        ok, error = validate_schema("final_output", output)
        if not ok:
            fallback = _safe_output(query, tickers)
            fallback["tickers_source"] = tickers_source
            fallback["tickers_inferred"] = tickers_inferred
            fallback["limitations"].append(f"Final output invalid: {error}")
            return fallback

        return output
