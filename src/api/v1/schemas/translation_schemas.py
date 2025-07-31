"""
Pydantic schemas for translation API
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class ModelProvider(str, Enum):
    OPENAI = "openai"
    AZURE = "azure"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"


class OpenAIModel(str, Enum):
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_35_TURBO = "gpt-3.5-turbo"
    GPT_4_1_MINI = "gpt-4.1-mini"


class LanguageCode(str, Enum):
    VIETNAMESE = "vi"
    ENGLISH = "en"
    JAPANESE = "ja"
    KOREAN = "ko"
    CHINESE = "zh"
    FRENCH = "fr"
    GERMAN = "de"
    SPANISH = "es"
    THAI = "th"
    AUTO = "auto"


# Base schemas
class BaseTranslationRequest(BaseModel):
    target_lang: LanguageCode = Field(
        default=LanguageCode.VIETNAMESE, description="Target language code"
    )
    source_lang: Optional[LanguageCode] = Field(
        default=None, description="Source language code (auto-detect if None)"
    )
    model_provider: ModelProvider = Field(
        default=ModelProvider.OPENAI, description="Translation model provider"
    )
    model_name: str = Field(default="gpt-4o-mini", description="Model name")
    temperature: float = Field(
        default=0.1, ge=0.0, le=2.0, description="Model temperature"
    )
    context: Optional[str] = Field(
        default=None, description="Additional context for translation"
    )
    glossary: Optional[Dict[str, str]] = Field(
        default=None, description="Translation glossary/dictionary"
    )

    @validator("temperature")
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v


# Text translation schemas
class TextTranslationRequest(BaseTranslationRequest):
    text: Union[str, List[str]] = Field(
        ..., description="Text to translate (string or list)"
    )
    use_context_aware: bool = Field(
        default=True, description="Use context-aware translation for lists"
    )
    batch_size: int = Field(
        default=10, ge=1, le=50, description="Batch size for list translation"
    )


class TextTranslationResponse(BaseModel):
    success: bool
    translated_text: Union[str, List[str]] = Field(..., description="Translated text")
    source_lang: str = Field(..., description="Detected or specified source language")
    target_lang: str = Field(..., description="Target language")
    model_used: str = Field(..., description="Model used for translation")
    text_count: int = Field(..., description="Number of texts translated")
    processing_time: float = Field(..., description="Processing time in seconds")
    error: Optional[str] = Field(default=None, description="Error message if any")


# Document translation schemas
class DocumentTranslationRequest(BaseTranslationRequest):
    output_path: Optional[str] = Field(
        default=None, description="Output file path (auto-generated if None)"
    )


class DocumentTranslationResponse(BaseModel):
    success: bool
    original_file: str = Field(..., description="Original file path")
    translated_file: Optional[str] = Field(
        default=None, description="Translated file path"
    )
    source_lang: str = Field(..., description="Source language")
    target_lang: str = Field(..., description="Target language")
    model_used: str = Field(..., description="Model used")
    text_count: int = Field(..., description="Number of translatable texts found")
    translation_count: int = Field(..., description="Number of texts translated")
    file_size: Optional[int] = Field(
        default=None, description="Output file size in bytes"
    )
    file_type: Optional[str] = Field(default=None, description="Document type")
    processing_time: float = Field(..., description="Processing time in seconds")
    error: Optional[str] = Field(default=None, description="Error message if any")


# Model comparison schemas
class ModelConfig(BaseModel):
    provider: ModelProvider = Field(..., description="Model provider")
    model: str = Field(..., description="Model name")
    temperature: float = Field(
        default=0.1, ge=0.0, le=2.0, description="Model temperature"
    )


class ModelComparisonRequest(BaseTranslationRequest):
    models: Optional[List[ModelConfig]] = Field(
        default=None, description="Models to compare"
    )


class ModelComparisonResult(BaseModel):
    success: bool
    translated_texts: Optional[List[str]] = Field(default=None)
    text_count: Optional[int] = Field(default=None)
    error: Optional[str] = Field(default=None)


class ModelComparisonResponse(BaseModel):
    success: bool
    original_file: str = Field(..., description="Original file path")
    target_lang: str = Field(..., description="Target language")
    source_text_count: int = Field(..., description="Number of source texts")
    models_tested: List[str] = Field(..., description="Models tested")
    results: Dict[str, ModelComparisonResult] = Field(
        ..., description="Results for each model"
    )
    processing_time: float = Field(..., description="Total processing time")
    error: Optional[str] = Field(default=None, description="Error message if any")


# Document info schemas
class DocumentInfoResponse(BaseModel):
    success: bool
    file_path: str = Field(..., description="File path")
    file_type: Optional[str] = Field(default=None, description="Document type")
    text_count: Optional[int] = Field(
        default=None, description="Number of translatable texts"
    )
    translatable_texts: Optional[List[str]] = Field(
        default=None, description="Preview of translatable texts"
    )
    is_supported: bool = Field(..., description="Whether file type is supported")
    file_size: Optional[int] = Field(default=None, description="File size in bytes")
    error: Optional[str] = Field(default=None, description="Error message if any")


class SupportedFormatsResponse(BaseModel):
    success: bool
    supported_extensions: List[str] = Field(
        ..., description="Supported file extensions"
    )
    processors: Dict[str, str] = Field(..., description="Description of each processor")


# Health check schema
class HealthResponse(BaseModel):
    status: str = Field(..., description="API status")
    timestamp: str = Field(..., description="Response timestamp")
    version: str = Field(default="1.0.0", description="API version")


# Error schemas
class ErrorResponse(BaseModel):
    success: bool = Field(default=False)
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(
        default=None, description="Detailed error information"
    )
    timestamp: str = Field(..., description="Error timestamp")
