from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pathlib import Path    


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
