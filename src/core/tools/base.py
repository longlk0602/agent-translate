"""
Base tools for React Agent
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Base class for React Agent tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool"""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get OpenAI function calling schema"""
        pass
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """Format tool result for LLM"""
        if result.get("success"):
            return f"✅ {self.name}: {result.get('message', 'Success')}"
        else:
            return f"❌ {self.name}: {result.get('error', 'Unknown error')}"


class ToolRegistry:
    """Registry for managing tools"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool):
        """Register a tool"""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get tool by name"""
        return self.tools.get(name)
    
    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get all tool schemas for OpenAI function calling"""
        return [
            {
                "type": "function",
                "function": tool.get_schema()
            }
            for tool in self.tools.values()
        ]
    
    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self.tools.keys())
    
    async def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name"""
        tool = self.get_tool(name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{name}' not found"
            }
        
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
