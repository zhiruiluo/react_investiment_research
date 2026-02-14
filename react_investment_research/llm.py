from __future__ import annotations

import json
import os
from typing import Any, Dict

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import anthropic
except ImportError:
    anthropic = None


class LLMClient:
    """Optional LLM client for reasoning about tool outputs - supports OpenAI and Anthropic."""

    def __init__(self) -> None:
        self.provider = None
        if os.environ.get("OPENAI_API_KEY") and OpenAI:
            self.provider = "openai"
            self.enabled = True
        elif os.environ.get("ANTHROPIC_API_KEY") and anthropic:
            self.provider = "anthropic"
            self.enabled = True
        else:
            self.enabled = False

    def generate_summary(
        self,
        query: str,
        tickers: list[str],
        tool_outputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Use LLM to generate thesis bullets and risks from tool outputs.
        
        Returns dict with optional llm_tokens and llm_cost_usd fields.
        """
        if not self.enabled:
            return {"thesis_bullets": [], "risks": []}

        if self.provider == "openai":
            return self._openai_summary(query, tickers, tool_outputs)
        elif self.provider == "anthropic":
            return self._anthropic_summary(query, tickers, tool_outputs)

        return {"thesis_bullets": [], "risks": []}

    def _openai_summary(
        self,
        query: str,
        tickers: list[str],
        tool_outputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate summary using OpenAI API."""
        try:
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

            prompt = f"""You are an investment research analyst. Analyze the following market data and generate a research summary.

User Query: {query}
Tickers: {', '.join(tickers)}

Market Data:
{json.dumps(tool_outputs, indent=2)}

Generate a JSON response with:
- thesis_bullets: list of 1-3 key insights about the tickers (string format)
- risks: list of 0-2 key risks or concerns (string format)

Respond with ONLY valid JSON, no markdown or extra text."""

            message = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.choices[0].message.content.strip()
            result = json.loads(response_text)

            return {
                "thesis_bullets": result.get("thesis_bullets", []),
                "risks": result.get("risks", []),
                "llm_tokens": {
                    "input": message.usage.prompt_tokens,
                    "output": message.usage.completion_tokens,
                    "total": message.usage.total_tokens,
                },
                "llm_provider": "openai",
                "llm_model": "gpt-4o-mini",
            }
        except Exception as e:
            return {"thesis_bullets": [], "risks": [], "llm_error": str(e)}

    def _anthropic_summary(
        self,
        query: str,
        tickers: list[str],
        tool_outputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate summary using Anthropic API (fallback)."""
        try:
            client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

            prompt = f"""You are an investment research analyst. Analyze the following market data and generate a research summary.

User Query: {query}
Tickers: {', '.join(tickers)}

Market Data:
{json.dumps(tool_outputs, indent=2)}

Generate a JSON response with:
- thesis_bullets: list of 1-3 key insights about the tickers (string format)
- risks: list of 0-2 key risks or concerns (string format)

Respond with ONLY valid JSON, no markdown or extra text."""

            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text.strip()
            result = json.loads(response_text)

            return {
                "thesis_bullets": result.get("thesis_bullets", []),
                "risks": result.get("risks", []),
                "llm_tokens": {
                    "input": message.usage.input_tokens,
                    "output": message.usage.output_tokens,
                    "total": message.usage.input_tokens + message.usage.output_tokens,
                },
                "llm_provider": "anthropic",
                "llm_model": "claude-3-5-sonnet-20241022",
            }
        except Exception as e:
            return {"thesis_bullets": [], "risks": [], "llm_error": str(e)}
