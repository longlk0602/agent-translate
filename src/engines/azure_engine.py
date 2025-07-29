"""
Azure Translator engine
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional

import aiohttp

from ..models.enums import SupportedLanguage
from .base import BaseTranslationEngine


class AzureEngine(BaseTranslationEngine):
    """Translation engine using Azure Translator"""

    def __init__(self, api_key: str, region: str = "global", endpoint: str = None):
        """
        Initialize Azure Translator engine

        Args:
            api_key: Azure Translator API key
            region: Azure region (default: "global")
            endpoint: Custom endpoint URL (optional)
        """
        self.api_key = api_key
        self.region = region
        self.endpoint = endpoint or "https://api.cognitive.microsofttranslator.com"

    async def translate_text(
        self,
        text: str,
        target_lang: SupportedLanguage,
        source_lang: Optional[SupportedLanguage] = None,
        custom_dict: Optional[Dict[str, str]] = None,
        context: Optional[str] = None,
    ) -> str:
        """Translate text using Azure Translator"""

        # Map SupportedLanguage to Azure language codes
        target_code = self._map_to_azure_lang(target_lang)
        source_code = self._map_to_azure_lang(source_lang) if source_lang else None

        url = f"{self.endpoint}/translate"

        # Build parameters
        params = {"api-version": "3.0", "to": target_code}

        if source_code:
            params["from"] = source_code

        # Build headers
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Ocp-Apim-Subscription-Region": self.region,
            "Content-Type": "application/json",
            "X-ClientTraceId": str(uuid.uuid4()),
        }

        # Build request body
        body = [{"text": text}]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, params=params, headers=headers, json=body
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    translated = result[0]["translations"][0]["text"]

                    # Apply custom dictionary
                    if custom_dict:
                        translated = self._apply_custom_dictionary(
                            translated, custom_dict
                        )

                    return translated
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"Azure Translator API error {response.status}: {error_text}"
                    )

    async def translate_texts(
        self,
        texts: List[str],
        target_lang: SupportedLanguage,
        source_lang: Optional[SupportedLanguage] = None,
        custom_dict: Optional[Dict[str, str]] = None,
        context: Optional[str] = None,
    ) -> List[str]:
        """Translate multiple texts using Azure Translator batch API"""

        if not texts:
            return []

        # Map SupportedLanguage to Azure language codes
        target_code = self._map_to_azure_lang(target_lang)
        source_code = self._map_to_azure_lang(source_lang) if source_lang else None

        url = f"{self.endpoint}/translate"

        # Build parameters
        params = {"api-version": "3.0", "to": target_code}

        if source_code:
            params["from"] = source_code

        # Build headers
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Ocp-Apim-Subscription-Region": self.region,
            "Content-Type": "application/json",
            "X-ClientTraceId": str(uuid.uuid4()),
        }

        # Build request body - Azure supports up to 100 texts per request
        body = [{"text": text} for text in texts]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, params=params, headers=headers, json=body
            ) as response:
                if response.status == 200:
                    results = await response.json()
                    translated_texts = []

                    for result in results:
                        translated = result["translations"][0]["text"]

                        # Apply custom dictionary
                        if custom_dict:
                            translated = self._apply_custom_dictionary(
                                translated, custom_dict
                            )

                        translated_texts.append(translated)

                    return translated_texts
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"Azure Translator API error {response.status}: {error_text}"
                    )

    async def detect_language(self, text: str) -> str:
        """Detect language of the given text"""

        url = f"{self.endpoint}/detect"

        params = {"api-version": "3.0"}

        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Ocp-Apim-Subscription-Region": self.region,
            "Content-Type": "application/json",
            "X-ClientTraceId": str(uuid.uuid4()),
        }

        body = [{"text": text}]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, params=params, headers=headers, json=body
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result[0]["language"]
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"Azure Language Detection API error {response.status}: {error_text}"
                    )

    async def get_supported_languages(self) -> Dict:
        """Get list of supported languages from Azure Translator"""

        url = f"{self.endpoint}/languages"
        params = {"api-version": "3.0"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"Azure Languages API error {response.status}: {error_text}"
                    )

    def _map_to_azure_lang(self, lang: SupportedLanguage) -> str:
        """Map SupportedLanguage enum to Azure language codes"""
        # Azure uses ISO 639-1 language codes
        azure_mapping = {
            SupportedLanguage.ENGLISH: "en",
            SupportedLanguage.SPANISH: "es",
            SupportedLanguage.FRENCH: "fr",
            SupportedLanguage.GERMAN: "de",
            SupportedLanguage.ITALIAN: "it",
            SupportedLanguage.PORTUGUESE: "pt",
            SupportedLanguage.RUSSIAN: "ru",
            SupportedLanguage.JAPANESE: "ja",
            SupportedLanguage.KOREAN: "ko",
            SupportedLanguage.CHINESE_SIMPLIFIED: "zh-Hans",
            SupportedLanguage.CHINESE_TRADITIONAL: "zh-Hant",
            SupportedLanguage.ARABIC: "ar",
            SupportedLanguage.HINDI: "hi",
            SupportedLanguage.VIETNAMESE: "vi",
            SupportedLanguage.THAI: "th",
            SupportedLanguage.DUTCH: "nl",
            SupportedLanguage.POLISH: "pl",
            SupportedLanguage.TURKISH: "tr",
            SupportedLanguage.HEBREW: "he",
            SupportedLanguage.CZECH: "cs",
            SupportedLanguage.HUNGARIAN: "hu",
            SupportedLanguage.FINNISH: "fi",
            SupportedLanguage.SWEDISH: "sv",
            SupportedLanguage.NORWEGIAN: "no",
            SupportedLanguage.DANISH: "da",
        }

        return azure_mapping.get(lang, lang.value)
