import os
from typing import Dict, List, Optional

from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential

from .base import BaseTranslator


class AzureTranslator(BaseTranslator):
    def __init__(
        self,
        api_key: str,
        region: str = "global",
        endpoint: str = "https://api.cognitive.microsofttranslator.com",
    ):
        super().__init__()
        self.api_key = api_key
        self.region = region
        self.endpoint = endpoint
        credential = AzureKeyCredential(api_key)
        self.client = TextTranslationClient(
            endpoint=self.endpoint, credential=credential, region=self.region
        )

    def translate_text(
        self, text: str, target_lang: str = "vi", source_lang: Optional[str] = None
    ) -> str:
        """Translate a single text block"""
        if not text.strip():
            return text
        try:
            response = self.client.translate(
                content=[text], to=[target_lang], from_parameter=source_lang
            )
            return response[0].translations[0].text if response else ""
        except Exception as e:
            raise Exception(f"Translation error: {e}")
