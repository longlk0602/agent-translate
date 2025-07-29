"""
Main translation agent that orchestrates all components
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from ..models.data_classes import TranslationRequest, TranslationResult
from ..models.enums import SupportedLanguage
from ..processors.base import DocumentProcessor
from .chatbot import TranslationChatbot
from .dictionary_manager import DictionaryManager
from .translation_engine import TranslationEngine

logger = logging.getLogger(__name__)


class TranslationAgent:
    """Main translation agent that orchestrates all components"""

    def __init__(self, openai_api_key: str = None, anthropic_api_key: str = None):
        self.document_processor = DocumentProcessor()
        self.translation_engine = TranslationEngine(openai_api_key, anthropic_api_key)
        self.dictionary_manager = DictionaryManager()
        self.chatbot = TranslationChatbot(self.translation_engine)

        self.active_translations = {}
        self.translation_history = []

    async def translate_document(
        self, request: TranslationRequest
    ) -> TranslationResult:
        """Main document translation function"""

        start_time = asyncio.get_event_loop().time()
        errors = []
        translation_log = []

        try:
            # Step 1: Extract content from document
            logger.info(f"Extracting content from {request.source_file_path}")
            content = self.document_processor.extract_text(request.source_file_path)

            # Step 2: Load custom dictionary if provided
            custom_dict = request.custom_dictionary or {}

            # Step 3: Extract keywords from reference files
            if request.reference_files:
                logger.info("Extracting keywords from reference files")
                reference_keywords = (
                    self.dictionary_manager.extract_keywords_from_reference(
                        request.reference_files
                    )
                )
                custom_dict.update(reference_keywords)

            # Step 4: Translate content
            logger.info("Starting translation process")
            translated_content = await self._translate_document_content(
                content, request.target_language, request.source_language, custom_dict
            )

            # Step 5: Reconstruct document
            logger.info("Reconstructing document")
            output_path = self._generate_output_path(
                request.source_file_path, request.target_language
            )
            final_path = self.document_processor.reconstruct_document(
                request.source_file_path, translated_content, output_path
            )

            # Step 6: Calculate statistics
            processing_time = asyncio.get_event_loop().time() - start_time
            word_count = self._count_words(content)

            # Store translation for chatbot
            self.chatbot.current_translations = self._extract_translation_pairs(
                content, translated_content
            )

            result = TranslationResult(
                translated_file_path=final_path,
                translation_log=translation_log,
                word_count=word_count,
                processing_time=processing_time,
                errors=errors,
            )

            self.translation_history.append(result)
            return result

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            errors.append(str(e))

            return TranslationResult(
                translated_file_path="",
                translation_log=translation_log,
                word_count=0,
                processing_time=asyncio.get_event_loop().time() - start_time,
                errors=errors,
            )

    async def _translate_document_content(
        self,
        content: Dict[str, Any],
        target_lang: SupportedLanguage,
        source_lang: Optional[SupportedLanguage] = None,
        custom_dict: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Translate all text content in document structure"""

        if "text" in content:
            # Simple text file
            content["text"] = await self.translation_engine.translate_text(
                content["text"], target_lang, source_lang, custom_dict
            )

        elif "paragraphs" in content:
            # DOCX file
            for para in content["paragraphs"]:
                para["text"] = await self.translation_engine.translate_text(
                    para["text"], target_lang, source_lang, custom_dict
                )

                # Translate individual runs
                for run in para["runs"]:
                    if run["text"].strip():
                        run["text"] = await self.translation_engine.translate_text(
                            run["text"], target_lang, source_lang, custom_dict
                        )

        elif "pages" in content:
            # PDF file
            for page in content["pages"]:
                page["text"] = await self.translation_engine.translate_text(
                    page["text"], target_lang, source_lang, custom_dict
                )

        elif "slides" in content:
            # PPTX file
            for slide in content["slides"]:
                for frame in slide["text_frames"]:
                    frame["text"] = await self.translation_engine.translate_text(
                        frame["text"], target_lang, source_lang, custom_dict
                    )

        elif "sheets" in content:
            # XLSX file
            for sheet in content["sheets"]:
                for row in sheet["cells"]:
                    for cell in row:
                        if cell["value"].strip():
                            cell["value"] = (
                                await self.translation_engine.translate_text(
                                    cell["value"], target_lang, source_lang, custom_dict
                                )
                            )

        return content

    def _generate_output_path(
        self, source_path: str, target_lang: SupportedLanguage
    ) -> str:
        """Generate output file path"""

        path = Path(source_path)
        filename = path.stem
        extension = path.suffix

        output_filename = f"{filename}_{target_lang.value}{extension}"
        return str(path.parent / output_filename)

    def _count_words(self, content: Dict[str, Any]) -> int:
        """Count words in document content"""

        text_content = ""

        if "text" in content:
            text_content = content["text"]
        elif "paragraphs" in content:
            text_content = " ".join([para["text"] for para in content["paragraphs"]])
        elif "pages" in content:
            text_content = " ".join([page["text"] for page in content["pages"]])
        elif "slides" in content:
            text_parts = []
            for slide in content["slides"]:
                for frame in slide["text_frames"]:
                    text_parts.append(frame["text"])
            text_content = " ".join(text_parts)
        elif "sheets" in content:
            text_parts = []
            for sheet in content["sheets"]:
                for row in sheet["cells"]:
                    for cell in row:
                        text_parts.append(cell["value"])
            text_content = " ".join(text_parts)

        return len(text_content.split())

    def _extract_translation_pairs(
        self, original_content: Dict[str, Any], translated_content: Dict[str, Any]
    ) -> Dict[str, str]:
        """Extract original->translated pairs for chatbot"""

        pairs = {}

        if "text" in original_content:
            pairs[original_content["text"]] = translated_content["text"]
        elif "paragraphs" in original_content:
            for orig_para, trans_para in zip(
                original_content["paragraphs"], translated_content["paragraphs"]
            ):
                pairs[orig_para["text"]] = trans_para["text"]
        elif "pages" in original_content:
            for orig_page, trans_page in zip(
                original_content["pages"], translated_content["pages"]
            ):
                pairs[orig_page["text"]] = trans_page["text"]
        elif "slides" in original_content:
            for orig_slide, trans_slide in zip(
                original_content["slides"], translated_content["slides"]
            ):
                for orig_frame, trans_frame in zip(
                    orig_slide["text_frames"], trans_slide["text_frames"]
                ):
                    pairs[orig_frame["text"]] = trans_frame["text"]

        return pairs

    async def chat_with_agent(self, message: str) -> str:
        """Chat interface for translation editing"""

        context = {
            "current_translations": self.chatbot.current_translations,
            "translation_history": self.translation_history,
        }

        return await self.chatbot.process_message(message, context)

    def load_custom_dictionary(self, dict_path: str, dict_name: str = "default"):
        """Load custom dictionary"""

        self.dictionary_manager.load_dictionary(dict_path, dict_name)

    def get_translation_statistics(self) -> Dict[str, Any]:
        """Get translation statistics"""

        if not self.translation_history:
            return {"message": "No translations performed yet"}

        total_words = sum(result.word_count for result in self.translation_history)
        total_time = sum(result.processing_time for result in self.translation_history)
        total_files = len(self.translation_history)

        return {
            "total_files_translated": total_files,
            "total_words_translated": total_words,
            "total_processing_time": total_time,
            "average_words_per_second": (
                total_words / total_time if total_time > 0 else 0
            ),
            "recent_translations": [
                {
                    "file": result.translated_file_path,
                    "words": result.word_count,
                    "time": result.processing_time,
                    "errors": len(result.errors),
                }
                for result in self.translation_history[-5:]
            ],
        }
