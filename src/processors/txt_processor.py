"""
TXT document processor
"""

from typing import Any, Dict

from .base import BaseDocumentProcessor


class TXTProcessor(BaseDocumentProcessor):
    """Processor for TXT documents"""

    def extract_text(self, file_path: str) -> Dict[str, Any]:
        """Extract text content from TXT file"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = {"text": f.read(), "lines": f.readlines()}
        return content

    def reconstruct_document(
        self, original_path: str, translated_content: Dict[str, Any], output_path: str
    ) -> str:
        """Reconstruct TXT document with translated content"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(translated_content["text"])

        return output_path
