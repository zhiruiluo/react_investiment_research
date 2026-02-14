"""Tests for Tool Registry pattern."""

import pytest
from react_investment_research.tools.registry import Tool, ToolRegistry


def dummy_handler(tickers):
    """Dummy handler for testing."""
    return {"data": "test"}


class TestTool:
    """Tests for Tool dataclass."""

    def test_tool_creation_valid(self):
        """Test creating a valid tool."""
        tool = Tool(
            name="test_tool",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="A test tool",
            usage_examples=["example query"],
            budget_per_ticker=1,
        )
        assert tool.name == "test_tool"
        assert tool.handler is dummy_handler
        assert tool.budget_per_ticker == 1

    def test_tool_creation_with_paid_metadata(self):
        """Test creating a paid tool with pricing."""
        tool = Tool(
            name="sentiment_analysis",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="Sentiment analysis tool",
            is_paid=True,
            pricing_usd_per_call=0.05,
        )
        assert tool.is_paid is True
        assert tool.pricing_usd_per_call == 0.05

    def test_tool_creation_paid_requires_pricing(self):
        """Test that paid tools must have pricing > 0."""
        with pytest.raises(ValueError, match="pricing_usd_per_call"):
            Tool(
                name="paid_tool",
                handler=dummy_handler,
                input_schema={"type": "object"},
                output_schema={"type": "object"},
                description="Test",
                is_paid=True,
                pricing_usd_per_call=0.0,
            )

    def test_tool_prompt_description_shows_paid_label(self):
        """Test that paid tools show [PAID] label in description."""
        paid_tool = Tool(
            name="paid_tool",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="Expensive tool",
            is_paid=True,
            pricing_usd_per_call=0.10,
        )
        description = paid_tool.to_prompt_description()
        assert "[PAID]" in description
        assert "paid_tool" in description

    def test_tool_creation_empty_name(self):
        """Test that tool name cannot be empty."""
        with pytest.raises(ValueError, match="Tool name cannot be empty"):
            Tool(
                name="",
                handler=dummy_handler,
                input_schema={"type": "object"},
                output_schema={"type": "object"},
                description="Test",
            )

    def test_tool_creation_invalid_handler(self):
        """Test that handler must be callable."""
        with pytest.raises(ValueError, match="Tool handler must be callable"):
            Tool(
                name="test",
                handler="not_callable",  # type: ignore
                input_schema={"type": "object"},
                output_schema={"type": "object"},
                description="Test",
            )

    def test_tool_creation_invalid_input_schema(self):
        """Test that input_schema must be dict."""
        with pytest.raises(ValueError, match="input_schema must be a dict"):
            Tool(
                name="test",
                handler=dummy_handler,
                input_schema="invalid",  # type: ignore
                output_schema={"type": "object"},
                description="Test",
            )

    def test_tool_creation_invalid_output_schema(self):
        """Test that output_schema must be dict."""
        with pytest.raises(ValueError, match="output_schema must be a dict"):
            Tool(
                name="test",
                handler=dummy_handler,
                input_schema={"type": "object"},
                output_schema="invalid",  # type: ignore
                description="Test",
            )

    def test_tool_creation_invalid_budget(self):
        """Test that budget_per_ticker must be >= 1."""
        with pytest.raises(ValueError, match="budget_per_ticker must be >= 1"):
            Tool(
                name="test",
                handler=dummy_handler,
                input_schema={"type": "object"},
                output_schema={"type": "object"},
                description="Test",
                budget_per_ticker=0,
            )

    def test_tool_to_prompt_description_with_examples(self):
        """Test prompt description generation with examples."""
        tool = Tool(
            name="test_tool",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="A test tool",
            usage_examples=["example 1", "example 2"],
        )
        description = tool.to_prompt_description()
        assert "test_tool" in description
        assert "A test tool" in description
        assert "example 1" in description

    def test_tool_to_prompt_description_without_examples(self):
        """Test prompt description generation without examples."""
        tool = Tool(
            name="test_tool",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="A test tool",
        )
        description = tool.to_prompt_description()
        assert "test_tool" in description
        assert "A test tool" in description


class TestToolRegistry:
    """Tests for ToolRegistry class."""

    def test_registry_creation(self):
        """Test creating an empty registry."""
        registry = ToolRegistry()
        assert registry.list_names() == []
        assert registry.get_all() == {}

    def test_registry_register_single_tool(self):
        """Test registering a single tool."""
        registry = ToolRegistry()
        tool = Tool(
            name="test_tool",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="Test tool",
        )
        registry.register(tool)
        assert "test_tool" in registry.list_names()
        assert registry.get("test_tool") is tool

    def test_registry_register_duplicate_name(self):
        """Test that duplicate tool names are rejected."""
        registry = ToolRegistry()
        tool1 = Tool(
            name="test_tool",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="Test tool 1",
        )
        registry.register(tool1)
        
        tool2 = Tool(
            name="test_tool",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="Test tool 2",
        )
        with pytest.raises(ValueError, match="already registered"):
            registry.register(tool2)

    def test_registry_get_nonexistent_tool(self):
        """Test getting a tool that doesn't exist."""
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    def test_registry_register_multiple_tools(self):
        """Test registering multiple tools."""
        registry = ToolRegistry()
        tool1 = Tool(
            name="tool1",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="Tool 1",
        )
        tool2 = Tool(
            name="tool2",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="Tool 2",
        )
        registry.register(tool1)
        registry.register(tool2)
        assert sorted(registry.list_names()) == ["tool1", "tool2"]
        assert len(registry.get_all()) == 2

    def test_registry_get_all_returns_copy(self):
        """Test that get_all returns independent copy."""
        registry = ToolRegistry()
        tool = Tool(
            name="test_tool",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="Test",
        )
        registry.register(tool)
        all_tools = registry.get_all()
        all_tools["new_tool"] = tool  # Modify returned dict
        assert "new_tool" not in registry.get_all()  # Original unchanged

    def test_registry_list_names_sorted(self):
        """Test that list_names returns sorted names."""
        registry = ToolRegistry()
        for name in ["zebra", "apple", "monkey"]:
            tool = Tool(
                name=name,
                handler=dummy_handler,
                input_schema={"type": "object"},
                output_schema={"type": "object"},
                description=f"Tool {name}",
            )
            registry.register(tool)
        assert registry.list_names() == ["apple", "monkey", "zebra"]

    def test_registry_get_total_budget_per_ticker(self):
        """Test calculating total budget across tools."""
        registry = ToolRegistry()
        tool1 = Tool(
            name="tool1",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="Tool 1",
            budget_per_ticker=2,
        )
        tool2 = Tool(
            name="tool2",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="Tool 2",
            budget_per_ticker=3,
        )
        registry.register(tool1)
        registry.register(tool2)
        assert registry.get_total_budget_per_ticker() == 5

    def test_registry_to_prompt_description_empty(self):
        """Test prompt format for empty registry."""
        registry = ToolRegistry()
        assert registry.to_prompt_description() == "No tools available"

    def test_registry_to_prompt_description_with_tools(self):
        """Test prompt format with registered tools."""
        registry = ToolRegistry()
        tool = Tool(
            name="test_tool",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="A test tool",
            usage_examples=["example query"],
        )
        registry.register(tool)
        description = registry.to_prompt_description()
        assert "test_tool" in description
        assert "A test tool" in description
        assert "example query" in description

    def test_registry_repr(self):
        """Test string representation of registry."""
        registry = ToolRegistry()
        tool1 = Tool(
            name="tool1",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="Tool 1",
        )
        tool2 = Tool(
            name="tool2",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="Tool 2",
        )
        registry.register(tool1)
        registry.register(tool2)
        repr_str = repr(registry)
        assert "ToolRegistry" in repr_str
        assert "tool1" in repr_str
        assert "tool2" in repr_str
    def test_registry_get_available_tool_names(self):
        """Test getting tool names with metadata."""
        registry = ToolRegistry()
        free_tool = Tool(
            name="free",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="Free tool",
            is_paid=False,
        )
        paid_tool = Tool(
            name="premium",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="Paid tool",
            is_paid=True,
            pricing_usd_per_call=0.05,
        )
        registry.register(free_tool)
        registry.register(paid_tool)
        
        tools_info = registry.get_available_tool_names()
        assert "free" in tools_info
        assert "premium" in tools_info
        assert tools_info["free"]["is_paid"] is False
        assert tools_info["premium"]["is_paid"] is True
        assert tools_info["premium"]["pricing_usd_per_call"] == 0.05

    def test_registry_validate_and_filter_tools_valid(self):
        """Test validation with all valid tools."""
        registry = ToolRegistry()
        tool1 = Tool(
            name="tool1",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="Tool 1",
        )
        tool2 = Tool(
            name="tool2",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="Tool 2",
        )
        registry.register(tool1)
        registry.register(tool2)
        
        valid, invalid = registry.validate_and_filter_tools(["tool1", "tool2"])
        assert valid == ["tool1", "tool2"]
        assert invalid == []

    def test_registry_validate_and_filter_tools_invalid(self):
        """Test validation with invalid tools."""
        registry = ToolRegistry()
        tool1 = Tool(
            name="tool1",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="Tool 1",
        )
        registry.register(tool1)
        
        valid, invalid = registry.validate_and_filter_tools(["tool1", "nonexistent"])
        assert "tool1" in valid
        assert "nonexistent" in invalid

    def test_registry_create_filtered_registry(self):
        """Test creating filtered registry with subset of tools."""
        registry = ToolRegistry()
        tool1 = Tool(
            name="tool1",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="Tool 1",
        )
        tool2 = Tool(
            name="tool2",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="Tool 2",
        )
        registry.register(tool1)
        registry.register(tool2)
        
        filtered = registry.create_filtered_registry(["tool1"])
        assert filtered.list_names() == ["tool1"]
        assert filtered.get("tool2") is None

    def test_registry_create_filtered_registry_invalid_tool(self):
        """Test filtered registry rejects invalid tools."""
        registry = ToolRegistry()
        tool1 = Tool(
            name="tool1",
            handler=dummy_handler,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            description="Tool 1",
        )
        registry.register(tool1)
        
        with pytest.raises(ValueError, match="Invalid tool"):
            registry.create_filtered_registry(["nonexistent"])