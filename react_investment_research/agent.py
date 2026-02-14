from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from . import mocks
from .cost_analyzer import CostAnalyzer, get_global_analyzer
from .llm import LLMClient
from .schemas import validate_schema
from .tools import fundamentals_events, market_snapshot


def _safe_output(query: str, tickers: List[str]) -> Dict[str, Any]:
    return {
        "query": query,
        "tickers": tickers,
        "summary": {"thesis_bullets": [], "risks": []},
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
    def __init__(self, offline: bool = False, use_llm: bool = True, track_costs: bool = True) -> None:
        self.offline = offline
        self.use_llm = use_llm and not offline
        self.llm = LLMClient() if self.use_llm else None
        self.track_costs = track_costs and self.use_llm
        self.max_tool_calls = 6
        self.max_tickers = 5
        self.allowed_periods = {"1mo", "3mo", "6mo", "1y"}
        self.proxy_tickers = ["SPY", "QQQ", "TLT", "GLD"]

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
            tool_func = market_snapshot if name == "market_snapshot" else fundamentals_events

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
        limitations: List[str] = []

        if not tickers:
            tickers = list(self.proxy_tickers)
            limitations.append("No tickers provided. Using proxy tickers.")

        if len(tickers) > self.max_tickers:
            limitations.append("Too many tickers provided. Truncating to max allowed.")
            tickers = tickers[: self.max_tickers]

        if period not in self.allowed_periods:
            limitations.append("Invalid period provided. Using default 3mo.")
            period = "3mo"

        output = _safe_output(query, tickers)
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

        for ticker in tickers_for_calls:
            snapshot = self._call_tool(
                "market_snapshot",
                {"ticker": ticker, "period": period, "interval": "1d", "benchmarks": []},
                tool_calls,
                output["limitations"],
            )
            fundamentals = self._call_tool(
                "fundamentals_events",
                {"ticker": ticker, "fields": [], "include_calendar": True, "lookback_days": 90},
                tool_calls,
                output["limitations"],
            )

            data_used.append(f"market_snapshot:{ticker}")
            data_used.append(f"fundamentals_events:{ticker}")
            snapshots[ticker] = snapshot
            fundamentals_by_ticker[ticker] = fundamentals.get("fundamentals", {})
            tool_returns[ticker] = {
                "market_snapshot": snapshot,
                "fundamentals_events": fundamentals,
            }

            thesis, risk = self._summarize_snapshot(ticker, snapshot)
            thesis_bullets.append(thesis)
            if risk:
                risks.append(risk)
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
            fallback["limitations"].append(f"Final output invalid: {error}")
            return fallback

        return output
