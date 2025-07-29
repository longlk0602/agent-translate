"""
Translation API schemas
"""

from api.v1.schemas.translation_schemas import (  # Enums; Base schemas; Text translation; Document translation; Model comparison; Document info; Health; Error
    BaseTranslationRequest,
    DocumentInfoResponse,
    DocumentTranslationRequest,
    DocumentTranslationResponse,
    ErrorResponse,
    HealthResponse,
    LanguageCode,
    ModelComparisonRequest,
    ModelComparisonResponse,
    ModelComparisonResult,
    ModelConfig,
    ModelProvider,
    OpenAIModel,
    SupportedFormatsResponse,
    TextTranslationRequest,
    TextTranslationResponse,
)

__all__ = [
    "ModelProvider",
    "OpenAIModel",
    "LanguageCode",
    "BaseTranslationRequest",
    "TextTranslationRequest",
    "TextTranslationResponse",
    "DocumentTranslationRequest",
    "DocumentTranslationResponse",
    "ModelConfig",
    "ModelComparisonRequest",
    "ModelComparisonResult",
    "ModelComparisonResponse",
    "DocumentInfoResponse",
    "SupportedFormatsResponse",
    "HealthResponse",
    "ErrorResponse",
]
