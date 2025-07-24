"""
Translation Agent Package

A comprehensive translation system with AI-powered translation engines,
document processing capabilities, and interactive chatbot interface.
"""

from .core.agent import TranslationAgent
from .api.translation_api import TranslationAPI
from .models.enums import SupportedLanguage, FileType
from .models.data_classes import TranslationRequest, TranslationResult
from .utils.config import TranslationConfig

__version__ = "1.0.0"
__author__ = "Translation Agent Team"

__all__ = [
    "TranslationAgent",
    "TranslationAPI", 
    "SupportedLanguage",
    "FileType",
    "TranslationRequest",
    "TranslationResult",
    "TranslationConfig"
]
