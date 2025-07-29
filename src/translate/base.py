from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List


class BaseTranslator(ABC):
    """Abstract base class for translation processors"""

    @abstractmethod
    def translate_text(self, text: str) -> str:
        """Translate a single text block"""
        pass

    @abstractmethod
    def translate_texts(self, texts: List[str]) -> List[str]:
        """Translate a list of text blocks"""
        pass
