"""
Base document processor interface
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

from translate.google_base import GoogleTranslator


class BaseDocumentProcessor(ABC):
    """Base class for document processors"""

    @abstractmethod
    def extract_text(self, file_path: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def reconstruct_document(
        self, original_path: str, translated_content: Dict[str, Any], output_path: str
    ) -> str:
        pass

    @abstractmethod
    def get_pairs_translation(
        self, translated_content: Dict[str, Any]
    ) -> Dict[str, str]:
        """Extract translation pairs from translated content"""
        return {}
    
    def get_translatable_texts(self, extracted_content: Dict[str, Any]) -> List[str]:
        """Extract all translatable texts - to be overridden by subclasses"""
        return []

    def apply_translations(
        self, extracted_content: Dict[str, Any], translations: List[str]
    ) -> Dict[str, Any]:
        """Apply translations to extracted content - to be overridden by subclasses"""
        return extracted_content


class DocumentProcessor:
    """Main document processor that handles various file formats"""

    def __init__(self):
        from processors.docx_processor import DOCXProcessor
        from processors.pdf_processor import PDFProcessor
        from processors.pptx_processor import PPTXProcessor
        from processors.txt_processor import TXTProcessor
        from processors.xlsx_processor import XLSXProcessor

        self.processors = {
            ".pdf": PDFProcessor(),
            ".docx": DOCXProcessor(),
            ".pptx": PPTXProcessor(),
            ".xlsx": XLSXProcessor(),
            ".txt": TXTProcessor(),
        }
        self.translator = GoogleTranslator()

    def _get_processor(self, ext: str) -> BaseDocumentProcessor:
        """Get the appropriate processor based on file extension"""
        if ext in self.processors:
            return self.processors[ext]
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process the document based on its file extension"""
        ext = Path(file_path).suffix.lower()
        if ext in self.processors:
            processor = self._get_processor(ext)
            output_path = f"{Path(file_path).stem}_translated{ext}"
            extracted_content = processor.extract_text(file_path)
            # print(extracted_content)
            translatable_texts = processor.get_translatable_texts(extracted_content)
            # print(translatable_texts)
            translated_texts = self.translator.translate_texts(translatable_texts)
            # print(translated_texts)
            translated_content = processor.apply_translations(
                extracted_content, translated_texts
            )
            # print(translated_content)
            processor.reconstruct_document(file_path, translated_content, output_path)
            return output_path
        else:
            raise ValueError(f"Unsupported file format: {ext}")
