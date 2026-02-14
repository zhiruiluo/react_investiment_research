"""Tests for paid tools and tool selection features."""

import pytest

from react_investment_research.agent import ResearchAgent


class TestToolSelection:
    """Tests for tool selection and filtering."""

    def test_agent_default_uses_free_tools_only(self):
        """Test that agent defaults to free tools only."""
        agent = ResearchAgent(offline=True)
        tool_names = agent.registry.list_names()
        
        # All tools should be free by default
        for tool_name in tool_names:
            tool = agent._full_registry.get(tool_name)
            assert not tool.is_paid, f"Tool {tool_name} is paid but included in default"

    def test_agent_rejects_invalid_tools(self):
        """Test that agent raises error for invalid tools."""
        with pytest.raises(ValueError, match="Invalid tool"):
            ResearchAgent(offline=True, available_tools=["nonexistent_tool"])

    def test_agent_accepts_specific_tools(self):
        """Test that agent can use specific requested tools."""
        agent = ResearchAgent(
            offline=True,
            available_tools=["market_snapshot", "fundamentals_events"],
        )
        tools = agent.registry.list_names()
        assert set(tools) == {"market_snapshot", "fundamentals_events"}

    def test_agent_rejects_mix_of_valid_and_invalid(self):
        """Test that mixed valid/invalid tools are rejected."""
        with pytest.raises(ValueError, match="Invalid tool"):
            ResearchAgent(
                offline=True,
                available_tools=["market_snapshot", "invalid_tool"],
            )

    def test_agent_runs_with_selected_tools(self):
        """Test that agent can run with only selected tools."""
        agent = ResearchAgent(
            offline=True,
            available_tools=["market_snapshot"],
        )
        
        # Registry should be filtered to only market_snapshot
        tools = agent.registry.list_names()
        assert tools == ["market_snapshot"]
        
        output = agent.run(
            query="Test",
            tickers=["NVDA"],
            period="3mo",
        )
        
        # Should have run successfully
        assert "query" in output
        assert output["query"] == "Test"

    def test_full_registry_has_all_tools(self):
        """Test that full registry contains all tools."""
        agent = ResearchAgent(offline=True)
        full_tools = agent._full_registry.list_names()
        
        # Should have at least the two free tools
        assert "market_snapshot" in full_tools
        assert "fundamentals_events" in full_tools

    def test_tool_metadata_accessible(self):
        """Test that tool metadata is accessible through registry."""
        agent = ResearchAgent(offline=True)
        tools_info = agent.registry.get_available_tool_names()
        
        for tool_name, info in tools_info.items():
            assert "is_paid" in info
            assert "pricing_usd_per_call" in info
            # Free tools should have 0 pricing
            if not info["is_paid"]:
                assert info["pricing_usd_per_call"] == 0.0
