"""
Core dependencies and configurations for the API
"""

import os
from typing import Optional

from fastapi import HTTPException

from translate.azure_translator import AzureTranslator
from translate.openai_translator import OpenAITranslator


class BaseTranslationService:
    """Core translation service using proper processors"""

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        azure_api_key: Optional[str] = None,
        azure_region: Optional[str] = None,
    ):
        self.openai_api_key = openai_api_key
        self.azure_api_key = azure_api_key
        self.azure_region = azure_region

        # Available models
        self.available_models = {
            "openai": {
                "gpt-4o": {
                    "name": "GPT-4o",
                    "description": "Latest GPT-4 optimized model",
                },
                "gpt-4o-mini": {
                    "name": "GPT-4o Mini",
                    "description": "Fast and cost-effective GPT-4 model",
                },
                "gpt-4-turbo": {
                    "name": "GPT-4 Turbo",
                    "description": "High-performance GPT-4 model",
                },
                "gpt-3.5-turbo": {
                    "name": "GPT-3.5 Turbo",
                    "description": "Fast and affordable model",
                },
            },
            "azure": {
                "translator": {
                    "name": "Azure Translator",
                    "description": "Microsoft's translation service",
                }
            },
        }

    def get_translator(self, provider: str, model_name: str, temperature: float = 0.1):
        """Get translator instance"""
        if provider == "openai":
            if not self.openai_api_key:
                raise HTTPException(
                    status_code=400, detail="OpenAI API key is required"
                )
            return OpenAITranslator(
                api_key=self.openai_api_key, model=model_name, temperature=temperature
            )
        elif provider == "azure":
            if not self.azure_api_key:
                raise HTTPException(status_code=400, detail="Azure API key is required")
            return AzureTranslator(api_key=self.azure_api_key, region=self.azure_region)
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported provider: {provider}"
            )


# Global service instance
base_translation_service: Optional[BaseTranslationService] = None


def get_base_translation_service() -> BaseTranslationService:
    """Dependency to get base translation service"""
    if base_translation_service is None:
        raise HTTPException(
            status_code=500, detail="Translation service not initialized"
        )
    return base_translation_service


def get_translation_service():
    """Get enhanced translation service with document processing"""
    from api.v1.services.translation_service import TranslationService

    base_service = get_base_translation_service()
    return TranslationService(base_service)


def init_translation_service():
    """Initialize translation service with environment variables"""
    global base_translation_service

    openai_key = os.getenv("OPENAI_API_KEY")
    azure_key = os.getenv("AZURE_API_KEY")
    azure_region = os.getenv("AZURE_REGION")

    base_translation_service = BaseTranslationService(
        openai_api_key=openai_key, azure_api_key=azure_key, azure_region=azure_region
    )

    return base_translation_service
