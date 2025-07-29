"""
Anthropic translation engine
"""

import json
from typing import Dict, Optional

import anthropic

from ..models.enums import SupportedLanguage
from .base import BaseTranslationEngine


class AnthropicEngine(BaseTranslationEngine):
    """Translation engine using Anthropic Claude models"""

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    async def translate_text(
        self,
        text: str,
        target_lang: SupportedLanguage,
        source_lang: Optional[SupportedLanguage] = None,
        custom_dict: Optional[Dict[str, str]] = None,
        context: Optional[str] = None,
    ) -> str:
        """Translate text using Anthropic Claude"""

        prompt = f"""Translate the following text to {target_lang.value}. 
        
        Requirements:
        - Maintain original formatting and structure
        - Keep technical terms accurate
        - Preserve tone and style
        """

        if custom_dict:
            prompt += (
                f"\n\nCustom dictionary: {json.dumps(custom_dict, ensure_ascii=False)}"
            )

        if context:
            prompt += f"\n\nContext: {context}"

        prompt += f"\n\nText to translate:\n{text}"

        response = await self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )

        translated = response.content[0].text

        # Apply custom dictionary
        if custom_dict:
            translated = self._apply_custom_dictionary(translated, custom_dict)

        return translated
