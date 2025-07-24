"""
Google Translate engine
"""

from typing import Optional, Dict
from googletrans import Translator
from .base import BaseTranslationEngine
from ..models.enums import SupportedLanguage


class GoogleEngine(BaseTranslationEngine):
    """Translation engine using Google Translate"""
    
    def __init__(self):
        self.translator = Translator()
    
    async def translate_text(self, text: str, target_lang: SupportedLanguage, 
                           source_lang: Optional[SupportedLanguage] = None,
                           custom_dict: Optional[Dict[str, str]] = None,
                           context: Optional[str] = None) -> str:
        """Translate text using Google Translate"""
        
        src_lang = source_lang.value if source_lang else 'auto'
        result = self.translator.translate(text, src=src_lang, dest=target_lang.value)
        translated = result.text
        
        # Apply custom dictionary
        if custom_dict:
            translated = self._apply_custom_dictionary(translated, custom_dict)
        
        return translated
