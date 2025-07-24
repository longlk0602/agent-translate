"""
Enum definitions for the translation agent
"""

from enum import Enum


class SupportedLanguage(Enum):
    """Supported languages for translation"""
    ENGLISH = "en"
    VIETNAMESE = "vi"
    CHINESE = "zh"
    CHINESE_SIMPLIFIED = "zh-Hans"
    CHINESE_TRADITIONAL = "zh-Hant"
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
    DUTCH = "nl"
    POLISH = "pl"
    TURKISH = "tr"
    HEBREW = "he"
    CZECH = "cs"
    HUNGARIAN = "hu"
    FINNISH = "fi"
    SWEDISH = "sv"
    NORWEGIAN = "no"
    DANISH = "da"


class FileType(Enum):
    """Supported file types for translation"""
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    TXT = "txt"
