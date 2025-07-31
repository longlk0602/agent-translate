"""
Main translation engine that orchestrates different translation services
"""

import logging
from typing import Dict, Optional

from translate.openai_translator import OpenAITranslator
from translate.azure_translator import AzureTranslator
from translate.google_base import GoogleTranslator

logger = logging.getLogger(__name__)


class TranslationEngine:
    """Handles AI-powered translation with context awareness"""

    def __init__(self, openai_api_key: str = None, azure_api_key: str = None):
        self.openai_translator = OpenAITranslator(api_key=openai_api_key) if openai_api_key else None
        self.azure_translator = AzureTranslator(api_key=azure_api_key) if azure_api_key else None
        self.google_translator = GoogleTranslator()
        self.translation_cache = {}

    async def translate_text(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        custom_dict: Optional[Dict[str, str]] = None,
        context: Optional[str] = None,
    ) -> str:
        """Translate text with AI enhancement"""

        # Check cache first
        cache_key = f"{text}_{target_lang}_{source_lang or 'auto'}"
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]

        try:
            # Use AI translation if available
            if self.openai_translator:
                translated = self.openai_translator.translate_text(
                    text=text, 
                    target_lang=target_lang, 
                    source_lang=source_lang, 
                    glossary=custom_dict, 
                    context=context
                )
            elif self.azure_translator:
                translated = self.azure_translator.translate_text(
                    text=text,
                    target_lang=target_lang,
                    source_lang=source_lang
                )
            else:
                # Fallback to Google Translate
                translated = self.google_translator.translate_text(
                    text=text,
                    target_lang=target_lang,
                    source_lang=source_lang
                )

            # Cache result
            self.translation_cache[cache_key] = translated
            return translated

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            # Fallback to Google Translate
            return self.google_translator.translate_text(
                text=text,
                target_lang=target_lang,
                source_lang=source_lang
            )
