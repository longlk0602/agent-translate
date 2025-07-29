"""
Pydantic models for Translation API requests and responses
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ModelProvider(str, Enum):
    """Supported model providers"""

    OPENAI = "openai"
    AZURE = "azure"


class OpenAIModel(str, Enum):
    """OpenAI model options"""

    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"


class LanguageCode(str, Enum):
    """Supported language codes"""

    VIETNAMESE = "vi"
    ENGLISH = "en"
    CHINESE_SIMPLIFIED = "zh"
    CHINESE_TRADITIONAL = "zh-TW"
    JAPANESE = "ja"
    KOREAN = "ko"
    FRENCH = "fr"
    GERMAN = "de"
    SPANISH = "es"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    ARABIC = "ar"
    HINDI = "hi"
    THAI = "th"
    INDONESIAN = "id"
    MALAY = "ms"
    FILIPINO = "tl"


class TranslationRequest(BaseModel):
    """Request model for text translation"""

    text: Union[str, List[str]] = Field(
        ..., description="Text to translate (single string or list)"
    )
    target_lang: LanguageCode = Field(
        default=LanguageCode.VIETNAMESE, description="Target language code"
    )
    source_lang: Optional[LanguageCode] = Field(
        default=None, description="Source language code (auto-detect if not provided)"
    )
    model_provider: ModelProvider = Field(
        default=ModelProvider.OPENAI, description="Model provider"
    )
    model_name: str = Field(default="gpt-4o-mini", description="Specific model name")
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Model temperature for creativity control",
    )
    context: Optional[str] = Field(
        default=None, description="Additional context for translation"
    )
    glossary: Optional[Dict[str, str]] = Field(
        default=None, description="Custom term dictionary"
    )
    use_context_aware: bool = Field(
        default=True, description="Use context-aware translation for lists"
    )
    batch_size: int = Field(
        default=10, ge=1, le=50, description="Batch size for processing"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hello, world!",
                "target_lang": "vi",
                "model_provider": "openai",
                "model_name": "gpt-4o-mini",
                "temperature": 0.1,
                "context": "Greeting message",
                "glossary": {"world": "thế giới"},
            }
        }


class MultiModelRequest(BaseModel):
    """Request model for multi-model comparison"""

    text: Union[str, List[str]] = Field(..., description="Text to translate")
    target_lang: LanguageCode = Field(
        default=LanguageCode.VIETNAMESE, description="Target language code"
    )
    models: List[Dict[str, Any]] = Field(
        ..., description="List of model configurations"
    )
    context: Optional[str] = Field(default=None, description="Translation context")
    glossary: Optional[Dict[str, str]] = Field(
        default=None, description="Custom glossary"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hello, world!",
                "target_lang": "vi",
                "models": [
                    {"provider": "openai", "model": "gpt-4o-mini", "temperature": 0.1},
                    {"provider": "openai", "model": "gpt-4o", "temperature": 0.1},
                ],
                "context": "Greeting message",
            }
        }


class TranslationResponse(BaseModel):
    """Response model for translation"""

    success: bool = Field(..., description="Whether translation was successful")
    result: Union[str, List[str]] = Field(..., description="Translated text(s)")
    source_lang: Optional[str] = Field(
        default=None, description="Detected/specified source language"
    )
    target_lang: str = Field(..., description="Target language")
    model_used: str = Field(..., description="Model used for translation")
    processing_time: Optional[float] = Field(
        default=None, description="Processing time in seconds"
    )
    word_count: Optional[int] = Field(
        default=None, description="Number of words processed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "result": "Xin chào, thế giới!",
                "source_lang": "en",
                "target_lang": "vi",
                "model_used": "gpt-4o-mini",
                "processing_time": 1.23,
                "word_count": 3,
            }
        }


class MultiModelResponse(BaseModel):
    """Response model for multi-model comparison"""

    success: bool = Field(..., description="Whether comparison was successful")
    results: Dict[str, Union[str, List[str]]] = Field(
        ..., description="Results from each model"
    )
    target_lang: str = Field(..., description="Target language")
    processing_time: Optional[float] = Field(
        default=None, description="Total processing time"
    )
    models_used: List[str] = Field(..., description="List of models used")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "results": {
                    "openai_gpt-4o-mini": "Xin chào, thế giới!",
                    "openai_gpt-4o": "Xin chào thế giới!",
                },
                "target_lang": "vi",
                "processing_time": 2.45,
                "models_used": ["openai_gpt-4o-mini", "openai_gpt-4o"],
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""

    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional error details"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Invalid language code provided",
                "error_type": "ValidationError",
                "details": {"field": "target_lang", "value": "invalid"},
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Current timestamp")
    available_models: Dict[str, List[str]] = Field(
        ..., description="Available models by provider"
    )
    supported_languages: List[str] = Field(..., description="Supported language codes")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-07-24T10:30:00Z",
                "available_models": {
                    "openai": ["gpt-4o", "gpt-4o-mini"],
                    "azure": ["translator"],
                },
                "supported_languages": ["vi", "en", "ja", "ko"],
            }
        }


class ModelInfo(BaseModel):
    """Model information"""

    name: str = Field(..., description="Model display name")
    description: str = Field(..., description="Model description")
    provider: str = Field(..., description="Model provider")


class ModelsResponse(BaseModel):
    """Available models response"""

    success: bool = Field(default=True, description="Success status")
    models: Dict[str, Dict[str, ModelInfo]] = Field(
        ..., description="Available models by provider"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "models": {
                    "openai": {
                        "gpt-4o": {
                            "name": "GPT-4o",
                            "description": "Latest GPT-4 optimized model",
                            "provider": "openai",
                        }
                    }
                },
            }
        }


class LanguagesResponse(BaseModel):
    """Supported languages response"""

    success: bool = Field(default=True, description="Success status")
    languages: Dict[str, str] = Field(..., description="Language code to name mapping")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "languages": {"vi": "Vietnamese", "en": "English", "ja": "Japanese"},
            }
        }
