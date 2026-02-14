from __future__ import annotations

from typing import Any, Dict, Tuple

from jsonschema import Draft7Validator

MARKET_SNAPSHOT_SCHEMA: Dict[str, Any] = {
    "anyOf": [
        {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "ticker",
                "asof",
                "period",
                "interval",
                "prices",
                "risk",
                "trend",
                "volume",
                "relative",
                "notes",
            ],
            "properties": {
                "ticker": {"type": "string"},
                "asof": {"type": "string"},
                "period": {"type": "string"},
                "interval": {"type": "string"},
                "prices": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["start", "end", "return_pct", "max_drawdown_pct"],
                    "properties": {
                        "start": {"type": "number"},
                        "end": {"type": "number"},
                        "return_pct": {"type": "number"},
                        "max_drawdown_pct": {"type": "number"},
                    },
                },
                "risk": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["volatility_ann_pct", "atr_14"],
                    "properties": {
                        "volatility_ann_pct": {"type": "number"},
                        "atr_14": {"type": "number"},
                    },
                },
                "trend": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["sma_20", "sma_50", "trend_label"],
                    "properties": {
                        "sma_20": {"type": "number"},
                        "sma_50": {"type": "number"},
                        "trend_label": {"type": "string"},
                    },
                },
                "volume": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["avg_20d", "latest", "zscore_latest"],
                    "properties": {
                        "avg_20d": {"type": "number"},
                        "latest": {"type": "number"},
                        "zscore_latest": {"type": "number"},
                    },
                },
                "relative": {"type": "array"},
                "notes": {"type": "array"},
            },
        },
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["error", "ticker", "reason"],
            "properties": {
                "error": {"type": "string"},
                "ticker": {"type": "string"},
                "reason": {"type": "string"},
            },
        },
    ]
}

FUNDAMENTALS_EVENTS_SCHEMA: Dict[str, Any] = {
    "anyOf": [
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["ticker", "asof", "fundamentals", "calendar", "flags"],
            "properties": {
                "ticker": {"type": "string"},
                "asof": {"type": "string"},
                "fundamentals": {"type": "object"},
                "calendar": {"type": "object"},
                "flags": {"type": "array"},
            },
        },
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["error", "ticker", "reason"],
            "properties": {
                "error": {"type": "string"},
                "ticker": {"type": "string"},
                "reason": {"type": "string"},
            },
        },
    ]
}

FINAL_OUTPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "query",
        "tickers",
        "summary",
        "tickers_source",
        "tickers_inferred",
        "fundamentals",
        "tool_returns",
        "data_used",
        "tool_calls",
        "limitations",
        "disclaimer",
    ],
    "properties": {
        "query": {"type": "string"},
        "tickers": {"type": "array", "items": {"type": "string"}},
        "summary": {
            "type": "object",
            "additionalProperties": False,
            "required": ["thesis_bullets", "risks"],
            "properties": {
                "thesis_bullets": {"type": "array", "items": {"type": "string"}},
                "risks": {"type": "array", "items": {"type": "string"}},
            },
        },
        "tickers_source": {"type": "string"},
        "tickers_inferred": {"type": "array", "items": {"type": "string"}},
        "fundamentals": {
            "type": "object",
            "additionalProperties": True,
        },
        "tool_returns": {
            "type": "object",
            "additionalProperties": True,
        },
        "data_used": {"type": "array", "items": {"type": "string"}},
        "tool_calls": {"type": "array"},
        "limitations": {"type": "array", "items": {"type": "string"}},
        "disclaimer": {"type": "string"},
        "cost_analysis": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "additionalProperties": True,
                },
            ]
        },
    },
}

SCHEMAS: Dict[str, Dict[str, Any]] = {
    "market_snapshot": MARKET_SNAPSHOT_SCHEMA,
    "fundamentals_events": FUNDAMENTALS_EVENTS_SCHEMA,
    "final_output": FINAL_OUTPUT_SCHEMA,
}


def validate_schema(name: str, payload: Dict[str, Any]) -> Tuple[bool, str | None]:
    schema = SCHEMAS[name]
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: e.path)
    if errors:
        return False, errors[0].message
    return True, None
