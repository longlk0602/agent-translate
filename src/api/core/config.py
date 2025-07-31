"""
Configuration settings for the API
"""

import os
from typing import List


class Settings:
    """Application settings"""

    # App info
    APP_NAME = "Translation Service API"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = """
    **Comprehensive Translation Service** with multiple AI models and document processing.
    
    ## Features
    - 🌐 **Multiple Languages**: Support for 18+ languages
    - 🤖 **Multiple Models**: OpenAI GPT models and Azure Translator
    - 📄 **Document Processing**: PDF, DOCX, PPTX, TXT, XLSX files
    - 📚 **Custom Glossaries**: Use custom dictionaries for consistent terminology
    - 🎯 **Context-Aware**: Maintain consistency across document translations
    - ⚡ **Batch Processing**: Efficient handling of large documents
    """

    # Server config
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD: bool = os.getenv("RELOAD", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]  # In production, specify allowed origins

    # File upload limits
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    UPLOAD_DIRECTORY: str = "data/uploads"
    OUTPUT_DIRECTORY: str = "data/outputs"

    # Supported file extensions
    SUPPORTED_EXTENSIONS = {
        ".txt": "text/plain",
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".json": "application/json",
        ".csv": "text/csv",
    }

    # Translation settings
    DEFAULT_TARGET_LANGUAGE = "vi"
    DEFAULT_MODEL_PROVIDER = "openai"
    DEFAULT_MODEL_NAME = "gpt-4.1-mini"
    DEFAULT_TEMPERATURE = 0.1
    DEFAULT_BATCH_SIZE = 10

    # Rate limiting (requests per minute)
    RATE_LIMIT_PER_MINUTE = 100


# Global settings instance
settings = Settings()
