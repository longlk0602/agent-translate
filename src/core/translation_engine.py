"""
Main translation engine that orchestrates different translation services
"""

import logging
from typing import Dict, Optional

from ..engines.anthropic_engine import AnthropicEngine
from ..engines.google_engine import GoogleEngine
from ..engines.openai_engine import OpenAIEngine
from ..models.enums import SupportedLanguage

logger = logging.getLogger(__name__)


class TranslationEngine:
    """Handles AI-powered translation with context awareness"""

    def __init__(self, openai_api_key: str = None, anthropic_api_key: str = None):
        self.openai_engine = OpenAIEngine(openai_api_key) if openai_api_key else None
        self.anthropic_engine = (
            AnthropicEngine(anthropic_api_key) if anthropic_api_key else None
        )
        self.google_engine = GoogleEngine()
        self.translation_cache = {}

    async def translate_text(
        self,
        text: str,
        target_lang: SupportedLanguage,
        source_lang: Optional[SupportedLanguage] = None,
        custom_dict: Optional[Dict[str, str]] = None,
        context: Optional[str] = None,
    ) -> str:
        """Translate text with AI enhancement"""

        # Check cache first
        cache_key = (
            f"{text}_{target_lang.value}_{source_lang.value if source_lang else 'auto'}"
        )
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]

        try:
            # Use AI translation if available
            if self.openai_engine:
                translated = await self.openai_engine.translate_text(
                    text, target_lang, source_lang, custom_dict, context
                )
            elif self.anthropic_engine:
                translated = await self.anthropic_engine.translate_text(
                    text, target_lang, source_lang, custom_dict, context
                )
            else:
                # Fallback to Google Translate
                translated = await self.google_engine.translate_text(
                    text, target_lang, source_lang, custom_dict, context
                )

            # Cache result
            self.translation_cache[cache_key] = translated
            return translated

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            # Fallback to Google Translate
            return await self.google_engine.translate_text(
                text, target_lang, source_lang, custom_dict, context
            )
