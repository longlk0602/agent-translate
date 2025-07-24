"""
OpenAI translation engine
"""

import json
from typing import Optional, Dict
import openai
from .base import BaseTranslationEngine
from ..models.enums import SupportedLanguage


class OpenAIEngine(BaseTranslationEngine):
    """Translation engine using OpenAI GPT models"""
    
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
    
    async def translate_text(self, text: str, target_lang: SupportedLanguage, 
                           source_lang: Optional[SupportedLanguage] = None,
                           custom_dict: Optional[Dict[str, str]] = None,
                           context: Optional[str] = None) -> str:
        """Translate text using OpenAI"""
        
        system_prompt = f"""You are a professional translator. Translate the following text to {target_lang.value}.
        
        Requirements:
        - Maintain the original formatting and structure
        - Keep technical terms accurate
        - Preserve the tone and style
        - If uncertain about context, prioritize clarity
        """
        
        if custom_dict:
            system_prompt += f"\n\nCustom dictionary (use these translations when applicable):\n{json.dumps(custom_dict, ensure_ascii=False)}"
        
        if context:
            system_prompt += f"\n\nContext: {context}"
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.1
        )
        
        translated = response.choices[0].message.content
        
        # Apply custom dictionary
        if custom_dict:
            translated = self._apply_custom_dictionary(translated, custom_dict)
        
        return translated
