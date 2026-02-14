"""Tests for tool registry and LLM-driven tool routing."""

import json
import os

import pytest

from react_investment_research.agent import ResearchAgent
from react_investment_research.llm import LLMClient
from react_investment_research.tools.registry import Tool, ToolRegistry


class TestLLMDecideTools:
    """Tests for LLM decide_tools method."""

    def test_decide_tools_disabled_without_key(self):
        """Test that decide_tools returns error when LLM is disabled."""
        # Ensure no API keys are set
        original_openai = os.environ.pop("OPENAI_API_KEY", None)
        original_anthropic = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            llm = LLMClient()
            assert not llm.enabled
            
            result = llm.decide_tools("test query", ["NVDA"], "test tools")
            assert result.get("llm_error") == "LLM disabled"
            assert result.get("tools") == []
        finally:
            if original_openai:
                os.environ["OPENAI_API_KEY"] = original_openai
            if original_anthropic:
                os.environ["ANTHROPIC_API_KEY"] = original_anthropic

    def test_decide_tools_returns_correct_format(self):
        """Test that decide_tools response has correct format."""
        # This test would require API keys and actual LLM calls
        # For now, we just verify the method exists and is callable
        llm = LLMClient()
        assert hasattr(llm, "decide_tools")
        assert callable(llm.decide_tools)


class TestToolRegistry:
    """Tests for tool registry integration with agent."""

    def test_agent_registry_initialized(self):
        """Test that agent initializes with tool registry."""
        agent = ResearchAgent(offline=True)
        assert agent.registry is not None
        assert len(agent.registry.list_names()) == 2
        assert "market_snapshot" in agent.registry.list_names()
        assert "fundamentals_events" in agent.registry.list_names()

    def test_agent_registry_tools_registered(self):
        """Test that both tools are properly registered."""
        agent = ResearchAgent(offline=True)
        
        market_snapshot_tool = agent.registry.get("market_snapshot")
        assert market_snapshot_tool is not None
        assert market_snapshot_tool.name == "market_snapshot"
        assert market_snapshot_tool.handler is not None
        assert market_snapshot_tool.budget_per_ticker == 1
        
        fundamentals_tool = agent.registry.get("fundamentals_events")
        assert fundamentals_tool is not None
        assert fundamentals_tool.name == "fundamentals_events"
        assert fundamentals_tool.budget_per_ticker == 1

    def test_agent_registry_total_budget(self):
        """Test that total tool budget is calculated correctly."""
        agent = ResearchAgent(offline=True)
        total_budget = agent.registry.get_total_budget_per_ticker()
        # Should be sum of both tools' budgets: 1 + 1 = 2
        assert total_budget == 2

    def test_agent_registry_prompt_description(self):
        """Test that registry generates proper description for LLM."""
        agent = ResearchAgent(offline=True)
        description = agent.registry.to_prompt_description()
        
        assert isinstance(description, str)
        assert "market_snapshot" in description
        assert "fundamentals_events" in description
        assert "technical analysis" in description.lower()
        assert "earnings" in description.lower() or "calendar" in description.lower()


class TestBackwardCompatibility:
    """Tests for backward compatibility with fallback pipeline."""

    def test_agent_fallback_when_llm_disabled(self):
        """Test that agent uses fallback pipeline when LLM is disabled."""
        # Create agent with use_llm=False
        agent = ResearchAgent(offline=True, use_llm=False)
        
        output = agent.run(
            query="What's NVDA's trend?",
            tickers=["NVDA"],
            period="3mo",
        )
        
        # Should have tool_returns for both tools
        assert "NVDA" in output["tool_returns"]
        assert "market_snapshot" in output["tool_returns"]["NVDA"]
        assert "fundamentals_events" in output["tool_returns"]["NVDA"]

    def test_agent_fallback_multiple_tickers(self):
        """Test that fallback pipeline works with multiple tickers."""
        agent = ResearchAgent(offline=True, use_llm=False)
        
        output = agent.run(
            query="Compare NVDA and AAPL",
            tickers=["NVDA", "AAPL"],
            period="3mo",
        )
        
        # Should have results for both tickers
        assert len(output["tickers"]) == 2
        assert "NVDA" in output["tool_returns"]
        assert "AAPL" in output["tool_returns"]

    def test_agent_offline_mode_uses_mocks(self):
        """Test that offline mode uses mock tools."""
        agent = ResearchAgent(offline=True)
        
        output = agent.run(
            query="Test query",
            tickers=["TEST"],
            period="3mo",
        )
        
        # Offline mode should still return valid output structure
        assert "query" in output
        assert "tickers" in output
        assert "tool_returns" in output


class TestAgentToolCalls:
    """Tests for agent tool calling behavior."""

    def test_agent_calls_both_tools_fallback(self):
        """Test that fallback pipeline calls both tools."""
        agent = ResearchAgent(offline=True, use_llm=False)
        
        output = agent.run(
            query="What's NVDA's trend and fundamentals?",
            tickers=["NVDA"],
            period="3mo",
        )
        
        # Verify tool_calls list shows both tools were called
        tool_call_names = [tc["name"] for tc in output["tool_calls"]]
        assert "market_snapshot" in tool_call_names
        assert "fundamentals_events" in tool_call_names

    def test_agent_tracks_data_used(self):
        """Test that agent tracks which tools were called for which tickers."""
        agent = ResearchAgent(offline=True, use_llm=False)
        
        output = agent.run(
            query="Analysis",
            tickers=["NVDA", "AAPL"],
            period="3mo",
        )
        
        # data_used should list all tool:ticker combinations
        assert "market_snapshot:NVDA" in output["data_used"]
        assert "fundamentals_events:NVDA" in output["data_used"]
        assert "market_snapshot:AAPL" in output["data_used"]
        assert "fundamentals_events:AAPL" in output["data_used"]


class TestAgentOfflineSchema:
    """Ensure offline agent output matches expected schema."""

    def test_offline_output_complete(self):
        """Test that offline output contains all required fields."""
        agent = ResearchAgent(offline=True)
        
        output = agent.run(
            query="test",
            tickers=["TEST"],
            period="3mo",
        )
        
        # Verify all required fields are present
        required_fields = [
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
        ]
        for field in required_fields:
            assert field in output, f"Missing required field: {field}"

    def test_offline_output_is_json_safe(self):
        """Test that offline output can be serialized to JSON."""
        agent = ResearchAgent(offline=True)
        
        output = agent.run(
            query="test",
            tickers=["NVDA"],
            period="3mo",
        )
        
        # Should be able to serialize to JSON without errors
        json_str = json.dumps(output)
        assert isinstance(json_str, str)
        assert len(json_str) > 0
        
        # Should be able to deserialize back
        deserialized = json.loads(json_str)
        assert deserialized["query"] == "test"
        assert deserialized["tickers"] == ["NVDA"]
