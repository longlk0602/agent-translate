"""
Document processing service using the processors
"""

import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from api.core.config import settings
from processors.base import BaseDocumentProcessor
from processors.docx_processor import DOCXProcessor
from processors.pdf_processor import PDFProcessor
from processors.pptx_processor import PPTXProcessor
from processors.txt_processor import TXTProcessor
from processors.xlsx_processor import XLSXProcessor


class DocumentProcessingService:
    """Service for processing documents using the processor classes"""

    def __init__(self):
        self.processors = {
            ".txt": TXTProcessor(),
            ".pdf": PDFProcessor(),
            ".docx": DOCXProcessor(),
            ".pptx": PPTXProcessor(),
            ".xlsx": XLSXProcessor(),
        }

    def get_processor(self, file_extension: str) -> BaseDocumentProcessor:
        """Get appropriate processor for file type"""
        ext = file_extension.lower()
        if ext not in self.processors:
            raise ValueError(f"Unsupported file type: {ext}")
        return self.processors[ext]

    def extract_text_from_file(self, file_path: str) -> Dict[str, Any]:
        """Extract text content from document"""
        path = Path(file_path)
        processor = self.get_processor(path.suffix)
        return processor.extract_text(file_path)

    def get_translatable_texts(self, file_path: str) -> List[str]:
        """Get list of translatable texts from document"""
        path = Path(file_path)
        processor = self.get_processor(path.suffix)
        extracted_content = processor.extract_text(file_path)
        return processor.get_translatable_texts(extracted_content)

    def reconstruct_document(
        self,
        original_file_path: str,
        translated_texts: List[str],
        output_path: Optional[str] = None,
    ) -> str:
        """Reconstruct document with translated content"""

        path = Path(original_file_path)
        processor = self.get_processor(path.suffix)

        # Extract original content
        extracted_content = processor.extract_text(original_file_path)

        # Apply translations
        translated_content = processor.apply_translations(
            extracted_content, translated_texts
        )

        # Generate output path if not provided
        if output_path is None:
            output_dir = Path(settings.OUTPUT_DIRECTORY)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Create unique filename
            file_id = str(uuid.uuid4())[:8]
            output_filename = f"{path.stem}_translated_{file_id}{path.suffix}"
            output_path = str(output_dir / output_filename)

        # Reconstruct document
        return processor.reconstruct_document(
            original_file_path, translated_content, output_path
        )

    def process_document_for_translation(self, file_path: str) -> Dict[str, Any]:
        """Complete document processing for translation pipeline"""

        # Extract text content
        extracted_content = self.extract_text_from_file(file_path)

        # Get translatable texts
        translatable_texts = self.get_translatable_texts(file_path)

        return {
            "extracted_content": extracted_content,
            "translatable_texts": translatable_texts,
            "text_count": len(translatable_texts),
            "file_type": Path(file_path).suffix,
            "original_file": file_path,
        }

    def create_translated_document(
        self,
        original_file_path: str,
        translations: List[str],
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create translated document and return metadata"""

        try:
            output_file = self.reconstruct_document(
                original_file_path=original_file_path,
                translated_texts=translations,
                output_path=output_path,
            )

            return {
                "success": True,
                "original_file": original_file_path,
                "translated_file": output_file,
                "translation_count": len(translations),
                "file_size": Path(output_file).stat().st_size,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "original_file": original_file_path,
            }

    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions"""
        return list(self.processors.keys())

    def is_supported_file(self, filename: str) -> bool:
        """Check if file is supported"""
        ext = Path(filename).suffix.lower()
        return ext in self.processors


# Global document processing service
document_service = DocumentProcessingService()
