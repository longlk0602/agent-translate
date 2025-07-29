"""
Data classes for the translation agent
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .enums import SupportedLanguage


@dataclass
class TranslationRequest:
    """Request object for document translation"""

    source_file_path: str
    target_language: SupportedLanguage
    source_language: Optional[SupportedLanguage] = None
    custom_dictionary: Optional[Dict[str, str]] = None
    reference_files: Optional[List[str]] = None
    preserve_formatting: bool = True


@dataclass
class TranslationResult:
    """Result object from document translation"""

    translated_file_path: str
    translation_log: List[Dict[str, Any]]
    word_count: int
    processing_time: float
    errors: List[str]
