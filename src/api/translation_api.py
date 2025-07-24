"""
API interface for the translation agent
"""

from typing import Dict, List, Any
from ..core.agent import TranslationAgent
from ..models.enums import SupportedLanguage, FileType
from ..models.data_classes import TranslationRequest


class TranslationAPI:
    """API interface for the translation agent"""
    
    def __init__(self, openai_api_key: str = None, anthropic_api_key: str = None):
        self.agent = TranslationAgent(openai_api_key, anthropic_api_key)
    
    async def translate_file(self, 
                           file_path: str, 
                           target_language: str,
                           source_language: str = None,
                           custom_dictionary_path: str = None,
                           reference_files: List[str] = None) -> Dict[str, Any]:
        """
        Translate a file
        
        Args:
            file_path: Path to the source file
            target_language: Target language code (e.g., 'vi', 'en')
            source_language: Source language code (optional)
            custom_dictionary_path: Path to custom dictionary file (optional)
            reference_files: List of reference file paths (optional)
            
        Returns:
            Dictionary containing translation result
        """
        
        try:
            # Load custom dictionary if provided
            custom_dict = None
            if custom_dictionary_path:
                self.agent.load_custom_dictionary(custom_dictionary_path)
                custom_dict = self.agent.dictionary_manager.dictionaries.get("default")
            
            # Create translation request
            request = TranslationRequest(
                source_file_path=file_path,
                target_language=SupportedLanguage(target_language),
                source_language=SupportedLanguage(source_language) if source_language else None,
                custom_dictionary=custom_dict,
                reference_files=reference_files
            )
            
            # Perform translation
            result = await self.agent.translate_document(request)
            
            return {
                "success": True,
                "translated_file_path": result.translated_file_path,
                "word_count": result.word_count,
                "processing_time": result.processing_time,
                "errors": result.errors
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def chat_about_translation(self, message: str) -> Dict[str, Any]:
        """
        Chat with the translation agent about changes
        
        Args:
            message: User message
            
        Returns:
            Dictionary containing chat response
        """
        
        try:
            response = await self.agent.chat_with_agent(message)
            
            return {
                "success": True,
                "response": response,
                "pending_changes": len(self.agent.chatbot.pending_changes)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get translation statistics"""
        
        return self.agent.get_translation_statistics()
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        
        return [lang.value for lang in SupportedLanguage]
    
    def get_supported_file_types(self) -> List[str]:
        """Get list of supported file types"""
        
        return [file_type.value for file_type in FileType]
