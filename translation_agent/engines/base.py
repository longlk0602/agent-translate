"""
Base translation engine interface
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from ..models.enums import SupportedLanguage


class BaseTranslationEngine(ABC):
    """Abstract base class for translation engines"""
    
    @abstractmethod
    async def translate_text(self, text: str, target_lang: SupportedLanguage, 
                           source_lang: Optional[SupportedLanguage] = None,
                           custom_dict: Optional[Dict[str, str]] = None,
                           context: Optional[str] = None) -> str:
        """Translate text with the engine"""
        pass
    
    async def translate_texts(self, texts: List[str], target_lang: SupportedLanguage,
                            source_lang: Optional[SupportedLanguage] = None,
                            custom_dict: Optional[Dict[str, str]] = None,
                            context: Optional[str] = None) -> List[str]:
        """Translate multiple texts (default implementation using single text translation)"""
        results = []
        for text in texts:
            translated = await self.translate_text(
                text, target_lang, source_lang, custom_dict, context
            )
            results.append(translated)
        return results
    
    def _apply_custom_dictionary(self, text: str, custom_dict: Dict[str, str]) -> str:
        """Apply custom dictionary replacements"""
        for source_term, target_term in custom_dict.items():
            # Case-insensitive replacement
            text = text.replace(source_term, target_term)
            text = text.replace(source_term.lower(), target_term.lower())
            text = text.replace(source_term.upper(), target_term.upper())
            text = text.replace(source_term.capitalize(), target_term.capitalize())
        
        return text
