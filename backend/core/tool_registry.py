"""
Tool Registry - Dynamic tool registration and discovery
"""

from typing import Any, ClassVar

from smolagents import Tool


class ToolRegistry:
    """Central registry for all available tools"""

    _tools: ClassVar[dict[str, type[Tool]]] = {}

    @classmethod
    def register(cls, tool_class: type[Tool]) -> type[Tool]:
        """Register a tool class"""
        tool_name = tool_class.name
        if tool_name in cls._tools:
            raise ValueError(f"Tool '{tool_name}' already registered")
        cls._tools[tool_name] = tool_class
        return tool_class

    @classmethod
    def get(cls, tool_name: str) -> type[Tool]:
        """Get a tool class by name"""
        if tool_name not in cls._tools:
            raise KeyError(f"Tool '{tool_name}' not found in registry")
        return cls._tools[tool_name]

    @classmethod
    def get_all(cls) -> dict[str, type[Tool]]:
        """Get all registered tools"""
        return cls._tools.copy()

    @classmethod
    def get_by_tag(cls, tag: str) -> list[type[Tool]]:
        """Get all tools with a specific tag"""
        return [tool for tool in cls._tools.values() if hasattr(tool, "tags") and tag in tool.tags]

    @classmethod
    def create_instances(cls, tool_names: list[str]) -> list[Tool]:
        """Create instances of tools by name"""
        return [cls.get(name)() for name in tool_names]

    @classmethod
    def list_tools(cls) -> list[str]:
        """List all registered tool names"""
        return list(cls._tools.keys())


def register_tool(tool_class: type[Tool]) -> type[Tool]:
    """Decorator to register a tool"""
    return ToolRegistry.register(tool_class)


class BaseTool(Tool):
    """Base class for all custom tools with metadata support"""

    tags: ClassVar[list[str]] = []
    category: ClassVar[str] = "general"
    version: ClassVar[str] = "1.0.0"

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        """Get tool metadata"""
        return {
            "name": cls.name,
            "description": cls.description,
            "category": cls.category,
            "tags": cls.tags,
            "version": cls.version,
            "inputs": cls.inputs,
            "output_type": cls.output_type,
        }
