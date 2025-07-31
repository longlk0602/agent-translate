"""
React Agent for translation editing using LLM with specialized tools
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from core.llm_manager import LLMManager
from core.tools.base import ToolRegistry
from core.tools.pptx_tools import PPTXSearchTool, PPTXReplaceTool, PPTXAnalyzeTool, PPTXSlideInfoTool
from core.tools.docx_tools import DOCXSearchTool, DOCXReplaceTool, DOCXAnalyzeTool
from core.tools.excel_tools import ExcelSearchTool, ExcelReplaceTool, ExcelAnalyzeTool, ExcelGetRangeTool

logger = logging.getLogger(__name__)


class ReactTranslationAgent:
    """React Agent for translation editing using LLM with specialized tools"""
    def __init__(self, llm_manager: LLMManager, default_provider: str = "openai", system_prompt: str = None):
        self.llm_manager = llm_manager
        self.default_provider = default_provider
        self.system_prompt = system_prompt or "You are a helpful translation editing assistant."
        self.tool_registry = ToolRegistry()
        self.current_session = None
        self.conversation_history = []
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register all available tools"""
        
        # PPTX tools
        self.tool_registry.register(PPTXSearchTool())
        self.tool_registry.register(PPTXReplaceTool())
        self.tool_registry.register(PPTXAnalyzeTool())
        self.tool_registry.register(PPTXSlideInfoTool())
        
        # DOCX tools
        self.tool_registry.register(DOCXSearchTool())
        self.tool_registry.register(DOCXReplaceTool())
        self.tool_registry.register(DOCXAnalyzeTool())
        
        # Excel tools
        self.tool_registry.register(ExcelSearchTool())
        self.tool_registry.register(ExcelReplaceTool())
        self.tool_registry.register(ExcelAnalyzeTool())
        self.tool_registry.register(ExcelGetRangeTool())
        
        logger.info(f"Registered {len(self.tool_registry.list_tools())} tools")
    
    def set_session_context(self, session_data: Dict[str, Any]):
        """Set current session context for the agent"""
        self.current_session = session_data
        self.conversation_history = []
        
        # Add session context to conversation
        file_type = session_data.get("file_type", "")
        file_name = session_data.get("file_name", "")
        
        # Update tools with session content
        self._update_tools_with_session_content(session_data)
        
        system_message = self._create_system_message(file_type, file_name)
        self.conversation_history.append({
            "role": "system",
            "content": system_message
        })
        
        logger.info(f"Set session context for {file_name} ({file_type})")
    
    def _update_tools_with_session_content(self, session_data: Dict[str, Any]):
        """Update tools with current session content"""
        session_content = session_data.get("translated_content", {})
        
        # Update all tools that have set_session_content method
        for tool_name, tool in self.tool_registry.tools.items():
            if hasattr(tool, 'set_session_content'):
                tool.set_session_content(session_content)
                logger.debug(f"Updated {tool_name} with session content")
    
    def _create_system_message(self, file_type: str, file_name: str) -> str:
        """Create system message based on file type"""
        
        available_tools = self._get_tools_for_file_type(file_type)
        tools_description = "\n".join([f"- {tool}: {self.tool_registry.get_tool(tool).description}" for tool in available_tools])
        
        base_message = f"""You are a helpful translation editing assistant working with a {file_type} file named '{file_name}'.

Your role is to help users edit and improve translated content using specialized tools. You can:

1. Search for specific text in the document
2. Replace text with improved translations
3. Analyze document structure
4. Provide information about specific sections

Available tools for {file_type} files:
{tools_description}

Guidelines:
- Always use tools to search before making changes
- Confirm changes with the user before executing
- Provide clear explanations of what you're doing
- Be helpful and conversational
- When user asks to change text, use search first to find it, then replace
- If text is not found, suggest similar terms or alternatives

Current session: {file_name} ({file_type})
"""
        
        return base_message
    
    def _get_tools_for_file_type(self, file_type: str) -> List[str]:
        """Get available tools for specific file type"""
        
        if file_type == ".pptx":
            return ["search_pptx_text", "replace_pptx_text", "analyze_pptx_structure", "get_pptx_slide_info"]
        elif file_type == ".docx":
            return ["search_docx_text", "replace_docx_text", "analyze_docx_structure"]
        elif file_type == ".xlsx":
            return ["search_excel_text", "replace_excel_text", "analyze_excel_structure", "get_excel_range"]
        else:
            return []
    
    async def plan_tool_sequence(self, message: str, available_tools: List[str], provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """Use LLM to plan a sequence of tool calls based on user message, with tool descriptions"""
        provider = provider or self.default_provider
        # Build tool info with description and parameter schema
        tool_info = []
        for tool_name in available_tools:
            tool_obj = self.tool_registry.get_tool(tool_name)
            schema = tool_obj.get_schema() if hasattr(tool_obj, "get_schema") else {}
            param_info = []
            parameters = schema.get("parameters", {})
            properties = parameters.get("properties", {})
            required = parameters.get("required", [])
            for param_name, param_detail in properties.items():
                param_info.append({
                    "name": param_name,
                    "type": param_detail.get("type", "unknown"),
                    "description": param_detail.get("description", ""),
                    "required": param_name in required
                })
            tool_info.append({
                "tool": tool_name,
                "description": getattr(tool_obj, "description", "No description available"),
                "parameters": param_info
            })
        planning_prompt = (
            f"You are an expert translation agent. Given the user request: '{message}', "
            f"and the available tools (with descriptions and parameter requirements): {json.dumps(tool_info, ensure_ascii=False)}, "
            "please plan a step-by-step sequence of tool calls (with arguments) to fulfill the request. "
            "For each tool call, provide all required parameters. "
            "Return a list of tool call plans in JSON format: [{'tool': ..., 'args': {{...}}}]. "
            "If no tool is needed, return an empty list."
        )
        logger.info(planning_prompt)
        planning_messages = [
            {"role": "system", "content": planning_prompt},
            {"role": "user", "content": message}
        ]
        logger.info("Planning tool sequence using LLM...")
        logger.info(provider)
        planning_response = await self.llm_manager.chat_completion(
            provider_name=provider,
            messages=planning_messages
        )
        logger.info(planning_response)
        if not planning_response.get("success"):
            logger.error(f"Planning LLM error: {planning_response.get('error')}")
            return []
        plan_content = planning_response["message"].content
        try:
            plan = json.loads(plan_content)
            logger.info(f"LLM planning result: {plan}")
            return plan if isinstance(plan, list) else []
        except Exception as e:
            logger.error(f"Error parsing planning result: {e}")
            return []

    async def process_message(self, message: str, provider: Optional[str] = None) -> Dict[str, Any]:
        """Process user message using planning and React pattern"""
        if not self.current_session:
            return {
                "success": False,
                "response": "No active session. Please upload a file first.",
                "content_updated": False
            }
        provider = provider or self.default_provider
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        file_type = self.current_session.get("file_type", "")
        available_tools = self._get_tools_for_file_type(file_type)
        tool_schemas = [
            {"type": "function", "function": self.tool_registry.get_tool(tool_name).get_schema()}
            for tool_name in available_tools
        ]
        logger.info(f"Received user message: {message}")
        # Step 1: Planning
        plan = await self.plan_tool_sequence(message, available_tools, provider)
        logger.info(f"Planned tool sequence: {plan}")
        tool_results = []
        content_updated = False
        # Step 2: Execute planned tools
        for step in plan:
            tool_name = step.get("tool")
            tool_args = step.get("args", {})
            if tool_name in available_tools:
                logger.info(f"Executing planned tool: {tool_name} with args: {tool_args}")
                result = await self.tool_registry.execute_tool(tool_name, **tool_args)
                tool_results.append(result)
                if result.get("success") and "updated_content" in result:
                    self.current_session["translated_content"] = result["updated_content"]
                    content_updated = True
            else:
                logger.warning(f"Planned tool {tool_name} not in available tools.")
        # Step 3: Final LLM response
        self.conversation_history.append({
            "role": "assistant",
            "content": f"Planned tool sequence executed. Results: {json.dumps(tool_results)}"
        })
        # Optionally, you can call LLM again to summarize or explain the result
        summary_prompt = (
            "Summarize the results of the tool executions for the user in a helpful way. "
            "If content was updated, mention it."
        )
        summary_messages = self.conversation_history + [
            {"role": "system", "content": summary_prompt}
        ]
        summary_response = await self.llm_manager.chat_completion(
            provider_name=provider,
            messages=summary_messages
        )
        final_response = summary_response["message"].content if summary_response.get("success") else "Tool sequence executed."
        logger.info(f"Final assistant response: {final_response}")
        return {
            "success": True,
            "response": final_response,
            "content_updated": content_updated,
            "tool_results": tool_results,
            "updated_content": self.current_session.get("translated_content") if content_updated else None
        }
    
    def get_conversation_history(self) -> list:
        """Return the current conversation history."""
        return self.conversation_history
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        
        if not self.current_session:
            return {"message": "No active session"}
        
        return {
            "session_id": self.current_session.get("session_id"),
            "file_name": self.current_session.get("file_name"),
            "file_type": self.current_session.get("file_type"),
            "source_lang": self.current_session.get("source_lang"),
            "target_lang": self.current_session.get("target_lang"),
            "available_tools": self._get_tools_for_file_type(self.current_session.get("file_type", "")),
            "conversation_length": len([msg for msg in self.conversation_history if msg["role"] in ["user", "assistant"]]),
            "llm_provider": self.default_provider
        }
    
    def clear_conversation(self):
        """Clear conversation history but keep session context"""
        
        if self.current_session:
            file_type = self.current_session.get("file_type", "")
            file_name = self.current_session.get("file_name", "")
            system_message = self._create_system_message(file_type, file_name)
            
            self.conversation_history = [{
                "role": "system",
                "content": system_message
            }]
        else:
            self.conversation_history = []
