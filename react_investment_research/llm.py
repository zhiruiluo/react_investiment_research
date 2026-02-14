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

    def infer_tickers(self, query: str) -> Dict[str, Any]:
        """Infer likely tickers from a user query."""
        if not self.enabled:
            return {"tickers": [], "llm_error": "LLM disabled"}

        if self.provider == "openai":
            return self._openai_infer_tickers(query)
        if self.provider == "anthropic":
            return self._anthropic_infer_tickers(query)

        return {"tickers": [], "llm_error": "Unknown LLM provider"}

    def decide_tools(
        self,
        query: str,
        tickers: list[str],
        tools_description: str,
    ) -> Dict[str, Any]:
        """Decide which tools to call for a given query and tickers.
        
        Args:
            query: User query to analyze
            tickers: List of tickers to analyze
            tools_description: Formatted description of available tools
            
        Returns:
            Dict with 'tools' key containing list of tool decisions:
            [{"tool": "market_snapshot", "tickers": ["NVDA"]}, ...]
        """
        if not self.enabled:
            return {"tools": [], "llm_error": "LLM disabled"}

        if self.provider == "openai":
            return self._openai_decide_tools(query, tickers, tools_description)
        if self.provider == "anthropic":
            return self._anthropic_decide_tools(query, tickers, tools_description)

        return {"tools": [], "llm_error": "Unknown LLM provider"}

    def _generate_tool_decision_example(self, tools_description: str, example_tickers: list[str]) -> str:
        """Generate a dynamic example JSON for tool decisions based on available tools.
        
        Parses tool names from tools_description and creates JSON example using
        actual ticker symbols rather than hardcoded examples.
        
        Args:
            tools_description: Formatted description of available tools (from registry)
            example_tickers: List of actual tickers to use in example (first 1-3)
            
        Returns:
            JSON string with tool decision example
        """
        # Extract tool names from description (format: "- tool_name [PAID/FREE]: description")
        tool_names = []
        for line in tools_description.split('\n'):
            if line.strip().startswith('-'):
                # Extract tool name between '-' and ':' or '[PAID]'/'[FREE]'
                parts = line.split(':')
                if len(parts) >= 2:
                    tool_name = parts[0].strip().lstrip('-').strip()
                    # Remove [PAID] or [FREE] tags
                    tool_name = tool_name.replace('[PAID]', '').replace('[FREE]', '').strip()
                    # Remove price info like "$0.05/call"
                    tool_name = tool_name.replace('$0.05/call', '').strip()
                    if tool_name:
                        tool_names.append(tool_name)
        
        # Build example with actual tools and tickers
        if tool_names:
            example_tools = [
                {"tool": tool_names[0], "tickers": example_tickers}
            ]
            # Add second tool if available and we have at least 2 different tools
            if len(tool_names) > 1:
                example_tools.append({
                    "tool": tool_names[1],
                    "tickers": example_tickers if len(example_tickers) > 1 else example_tickers
                })
        else:
            # Fallback if no tools found in description
            example_tools = []
        
        return json.dumps({"tools": example_tools}, indent=2)

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

    def _openai_infer_tickers(self, query: str) -> Dict[str, Any]:
        """Infer tickers using OpenAI API."""
        try:
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

            prompt = f"""Extract up to 5 likely stock or ETF tickers from the user query.

User Query: {query}

Rules:
- Return ONLY a JSON object with a key "tickers".
- Use uppercase ticker symbols only.
- If no tickers are implied, return an empty list.

Example:
{{"tickers": ["NVDA", "AMD"]}}"""

            message = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.choices[0].message.content.strip()
            result = json.loads(response_text)
            tickers = result.get("tickers", [])
            if not isinstance(tickers, list):
                tickers = []

            return {
                "tickers": tickers,
                "llm_tokens": {
                    "input": message.usage.prompt_tokens,
                    "output": message.usage.completion_tokens,
                    "total": message.usage.total_tokens,
                },
                "llm_provider": "openai",
                "llm_model": "gpt-4o-mini",
            }
        except Exception as e:
            return {"tickers": [], "llm_error": str(e)}

    def _anthropic_infer_tickers(self, query: str) -> Dict[str, Any]:
        """Infer tickers using Anthropic API."""
        try:
            client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

            prompt = f"""Extract up to 5 likely stock or ETF tickers from the user query.

User Query: {query}

Rules:
- Return ONLY a JSON object with a key "tickers".
- Use uppercase ticker symbols only.
- If no tickers are implied, return an empty list.

Example:
{{"tickers": ["NVDA", "AMD"]}}"""

            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text.strip()
            result = json.loads(response_text)
            tickers = result.get("tickers", [])
            if not isinstance(tickers, list):
                tickers = []

            return {
                "tickers": tickers,
                "llm_tokens": {
                    "input": message.usage.input_tokens,
                    "output": message.usage.output_tokens,
                    "total": message.usage.input_tokens + message.usage.output_tokens,
                },
                "llm_provider": "anthropic",
                "llm_model": "claude-3-5-sonnet-20241022",
            }
        except Exception as e:
            return {"tickers": [], "llm_error": str(e)}

    def _openai_decide_tools(
        self,
        query: str,
        tickers: list[str],
        tools_description: str,
    ) -> Dict[str, Any]:
        """Decide which tools to invoke using OpenAI API."""
        try:
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

            # Generate dynamic example based on available tickers (limit to 3 for brevity)
            example_tickers = tickers[:3] if len(tickers) > 0 else ["EXAMPLE"]
            example_json = self._generate_tool_decision_example(tools_description, example_tickers)

            prompt = f"""You are an investment research agent. Given a user query and available tools, decide which tools to invoke.

User Query: {query}
Tickers to Analyze: {', '.join(tickers)}

Available Tools:
{tools_description}

For each relevant tool, specify which tickers it should be called for. Return ONLY a JSON object:
{example_json}

Rules:
- Include only relevant tools for the query
- You can call same tool for different ticker subsets if needed
- Return empty list if no tools are relevant
- Use ticker symbols from the provided list only"""

            message = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.choices[0].message.content.strip()
            result = json.loads(response_text)
            tools = result.get("tools", [])
            if not isinstance(tools, list):
                tools = []
            
            # Clean tool names by removing [PAID]/[FREE] tags and price labels
            for tool in tools:
                if isinstance(tool, dict) and "tool" in tool:
                    tool_name = tool["tool"]
                    # Remove [PAID] or [FREE] tags
                    tool_name = tool_name.replace('[PAID]', '').replace('[FREE]', '').strip()
                    # Remove price info like "$0.05/call"
                    tool_name = tool_name.rsplit('$', 1)[0].strip() if '$' in tool_name else tool_name
                    tool["tool"] = tool_name

            return {
                "tools": tools,
                "llm_tokens": {
                    "input": message.usage.prompt_tokens,
                    "output": message.usage.completion_tokens,
                    "total": message.usage.total_tokens,
                },
                "llm_provider": "openai",
                "llm_model": "gpt-4o-mini",
            }
        except Exception as e:
            return {"tools": [], "llm_error": str(e)}

    def _anthropic_decide_tools(
        self,
        query: str,
        tickers: list[str],
        tools_description: str,
    ) -> Dict[str, Any]:
        """Decide which tools to invoke using Anthropic API."""
        try:
            client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

            # Generate dynamic example based on available tickers (limit to 3 for brevity)
            example_tickers = tickers[:3] if len(tickers) > 0 else ["EXAMPLE"]
            example_json = self._generate_tool_decision_example(tools_description, example_tickers)

            prompt = f"""You are an investment research agent. Given a user query and available tools, decide which tools to invoke.

User Query: {query}
Tickers to Analyze: {', '.join(tickers)}

Available Tools:
{tools_description}

For each relevant tool, specify which tickers it should be called for. Return ONLY a JSON object:
{example_json}

Rules:
- Include only relevant tools for the query
- You can call same tool for different ticker subsets if needed
- Return empty list if no tools are relevant
- Use ticker symbols from the provided list only"""

            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text.strip()
            result = json.loads(response_text)
            tools = result.get("tools", [])
            if not isinstance(tools, list):
                tools = []
            
            # Clean tool names by removing [PAID]/[FREE] tags and price labels
            for tool in tools:
                if isinstance(tool, dict) and "tool" in tool:
                    tool_name = tool["tool"]
                    # Remove [PAID] or [FREE] tags
                    tool_name = tool_name.replace('[PAID]', '').replace('[FREE]', '').strip()
                    # Remove price info like "$0.05/call"
                    tool_name = tool_name.rsplit('$', 1)[0].strip() if '$' in tool_name else tool_name
                    tool["tool"] = tool_name

            return {
                "tools": tools,
                "llm_tokens": {
                    "input": message.usage.input_tokens,
                    "output": message.usage.output_tokens,
                    "total": message.usage.input_tokens + message.usage.output_tokens,
                },
                "llm_provider": "anthropic",
                "llm_model": "claude-3-5-sonnet-20241022",
            }
        except Exception as e:
            return {"tools": [], "llm_error": str(e)}

