"""Tool Registry Pattern: Dynamic tool management and LLM-driven routing."""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class Tool:
    """Specification for a tool available to the agent.
    
    Attributes:
        name: Unique tool identifier (e.g., "market_snapshot")
        handler: Callable that executes the tool, accepting tickers list
        input_schema: JSON schema for validating tool input
        output_schema: JSON schema for validating tool output
        description: Human-readable description for LLM tool selection
        usage_examples: List of example queries where tool applies
        budget_per_ticker: Max number of calls allowed per ticker (e.g., 1)
    """
    name: str
    handler: Callable
    input_schema: dict
    output_schema: dict
    description: str
    usage_examples: list[str] = field(default_factory=list)
    budget_per_ticker: int = 1

    def __post_init__(self):
        """Validate tool specification."""
        if not self.name:
            raise ValueError("Tool name cannot be empty")
        if not callable(self.handler):
            raise ValueError(f"Tool handler must be callable, got {type(self.handler)}")
        if not isinstance(self.input_schema, dict):
            raise ValueError("input_schema must be a dict")
        if not isinstance(self.output_schema, dict):
            raise ValueError("output_schema must be a dict")
        if self.budget_per_ticker < 1:
            raise ValueError(f"budget_per_ticker must be >= 1, got {self.budget_per_ticker}")

    def to_prompt_description(self) -> str:
        """Format tool spec for LLM prompt."""
        examples_str = "\n  ".join(self.usage_examples) if self.usage_examples else "None"
        return f"""- {self.name}: {self.description}
  Example usage: {examples_str}"""


class ToolRegistry:
    """Central registry for managing all available tools."""

    def __init__(self):
        """Initialize empty tool registry."""
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a new tool.
        
        Args:
            tool: Tool specification to register
            
        Raises:
            ValueError: If tool name already registered
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Get tool by name.
        
        Args:
            name: Tool name to retrieve
            
        Returns:
            Tool if found, None otherwise
        """
        return self._tools.get(name)

    def get_all(self) -> dict[str, Tool]:
        """Get all registered tools.
        
        Returns:
            Dictionary mapping tool names to Tool specs
        """
        return dict(self._tools)

    def list_names(self) -> list[str]:
        """Get list of all registered tool names.
        
        Returns:
            Sorted list of tool names
        """
        return sorted(self._tools.keys())

    def get_total_budget_per_ticker(self) -> int:
        """Calculate total budget across all tools per ticker.
        
        Returns:
            Sum of budget_per_ticker for all registered tools
        """
        return sum(tool.budget_per_ticker for tool in self._tools.values())

    def to_prompt_description(self) -> str:
        """Format all tools for LLM prompt.
        
        Returns:
            Formatted string listing tool descriptions for LLM
        """
        if not self._tools:
            return "No tools available"
        descriptions = [tool.to_prompt_description() for tool in self._tools.values()]
        return "\n".join(descriptions)

    def __repr__(self) -> str:
        """String representation of registry."""
        tools_str = ", ".join(self.list_names())
        return f"ToolRegistry({tools_str})"


# Global default registry instance
default_registry = ToolRegistry()
