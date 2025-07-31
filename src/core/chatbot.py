"""
Enhanced React-based translation chatbot using LLM and specialized tools
"""

import json
import logging
from typing import Any, Dict, List, Optional

from core.react_agent import ReactTranslationAgent
from core.llm_manager import LLMManager, OpenAIProvider, AzureOpenAIProvider

logger = logging.getLogger(__name__)


class TranslationChatbot:
    """React-based chatbot for interactive translation editing"""

    def __init__(self, translation_engine=None, llm_config: Optional[Dict[str, Any]] = None):
        # Keep backward compatibility
        self.translation_engine = translation_engine
        
        # Initialize LLM manager
        if llm_config:
            self.llm_manager = LLMManager.create_from_config(llm_config)
        else:
            # Default config - try to get from environment or translation_engine
            self.llm_manager = self._create_default_llm_manager()
        
        # Initialize React agent
        self.react_agent = ReactTranslationAgent(
            llm_manager=self.llm_manager,
            default_provider="openai"  # Can be configured
        )
        
        # Legacy properties for backward compatibility
        self.conversation_history = []
        self.current_translations = {}
        self.pending_changes = {}
        self.current_session = None
        self.auto_apply_changes = False

    def _create_default_llm_manager(self) -> LLMManager:
        """Create default LLM manager from environment or translation engine"""
        
        manager = LLMManager()
        
        # Try to get API key from translation engine or environment
        openai_api_key = None
        azure_config = None
        
        if self.translation_engine:
            # Extract API keys from translation engine if available
            if hasattr(self.translation_engine, 'openai_api_key'):
                openai_api_key = self.translation_engine.openai_api_key
            elif hasattr(self.translation_engine, 'api_key'):
                openai_api_key = self.translation_engine.api_key
        
        # Try environment variables
        import os
        if not openai_api_key:
            openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Add OpenAI provider if key available
        if openai_api_key:
            provider = OpenAIProvider(api_key=openai_api_key)
            manager.add_provider("openai", provider)
        
        # Try Azure OpenAI
        azure_api_key = os.getenv('AZURE_OPENAI_API_KEY')
        azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        
        if azure_api_key and azure_endpoint:
            provider = AzureOpenAIProvider(
                api_key=azure_api_key,
                endpoint=azure_endpoint
            )
            manager.add_provider("azure_openai", provider)
        
        return manager

    async def process_message(self, message: str, context: Dict[str, Any] = None) -> str:
        """Process user message using React Agent"""
        
        try:
            # Set session context if provided
            if context and "current_session" in context:
                session_data = context["current_session"]
                self.react_agent.set_session_context(session_data)
                self.current_session = session_data
            
            # Process message through React agent
            result = await self.react_agent.process_message(message)
            
            if result.get("success"):
                response = result["response"]
                
                # Update legacy properties for backward compatibility
                if result.get("content_updated"):
                    self.auto_apply_changes = True
                
                # Update conversation history for backward compatibility
                self.conversation_history = self.react_agent.get_conversation_history()
                
                return response
            else:
                error_msg = result.get("response", "I apologize, but I couldn't process your request.")
                return error_msg
                
        except Exception as e:
            logger.error(f"Error in process_message: {e}")
            return f"I apologize, but there was an error processing your request: {str(e)}"

    def set_session_context(self, session_data: Dict[str, Any]):
        """Set session context for the agent"""
        self.react_agent.set_session_context(session_data)
        self.current_session = session_data
        
        # Legacy compatibility - extract translation pairs
        original_content = session_data.get("original_content", {})
        translated_content = session_data.get("translated_content", {})
        self.current_translations = self._extract_translation_pairs(
            original_content, translated_content, session_data.get("file_type", "")
        )

    def _extract_translation_pairs(self, original_content: Dict[str, Any], translated_content: Dict[str, Any], file_type: str) -> Dict[str, str]:
        """Extract translation pairs for backward compatibility"""
        
        pairs = {}
        
        try:
            if file_type == ".txt":
                if "text" in original_content and "text" in translated_content:
                    pairs[original_content["text"]] = translated_content["text"]
            
            elif file_type == ".docx":
                if "paragraphs" in original_content and "paragraphs" in translated_content:
                    for orig_para, trans_para in zip(
                        original_content["paragraphs"], translated_content["paragraphs"]
                    ):
                        orig_text = orig_para.get("original_text", orig_para.get("text", ""))
                        trans_text = trans_para.get("text", "")
                        if orig_text and trans_text:
                            pairs[orig_text] = trans_text
            
            elif file_type == ".pptx":
                if "slides" in original_content and "slides" in translated_content:
                    for orig_slide, trans_slide in zip(
                        original_content["slides"], translated_content["slides"]
                    ):
                        for orig_shape, trans_shape in zip(
                            orig_slide.get("shapes", []), trans_slide.get("shapes", [])
                        ):
                            for orig_frame, trans_frame in zip(
                                orig_shape.get("text_frames", []), trans_shape.get("text_frames", [])
                            ):
                                orig_text = orig_frame.get("original_text", "")
                                trans_text = trans_frame.get("translated_text", "")
                                if orig_text and trans_text:
                                    pairs[orig_text] = trans_text
            
        except Exception as e:
            logger.warning(f"Error extracting translation pairs: {e}")
        
        return pairs

    def get_session_summary(self) -> Dict[str, Any]:
        """Get session summary"""
        return self.react_agent.get_session_summary()

    def clear_conversation(self):
        """Clear conversation history"""
        self.react_agent.clear_conversation()
        self.conversation_history = []

    # Legacy methods for backward compatibility
    def _parse_intent(self, message: str) -> str:
        """Legacy method - now handled by LLM"""
        return "llm_processed"
    
    async def _handle_translation_change(self, message: str, context: Dict[str, Any]) -> str:
        """Legacy method - now handled by React agent"""
        return await self.process_message(message, context)
    
    async def _handle_translation_query(self, message: str, context: Dict[str, Any]) -> str:
        """Legacy method - now handled by React agent"""
        return await self.process_message(message, context)
    
    async def _handle_view_changes(self, context: Dict[str, Any]) -> str:
        """Legacy method - now handled by React agent"""
        return await self.process_message("Show me what changes have been made", context)
    
    async def _handle_apply_changes(self, context: Dict[str, Any]) -> str:
        """Legacy method - now handled by React agent"""
        return await self.process_message("Apply all pending changes", context)
    
    async def _handle_clear_changes(self, context: Dict[str, Any]) -> str:
        """Legacy method - now handled by React agent"""
        return await self.process_message("Clear all pending changes", context)
    
    async def _handle_general_chat(self, message: str, context: Dict[str, Any]) -> str:
        """Legacy method - now handled by React agent"""
        return await self.process_message(message, context)
