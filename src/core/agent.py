"""
Advanced translation agent with session management and chatbot capabilities
"""

import asyncio
import copy
import logging
import time
from typing import Any, Dict, List, Optional

from models.data_classes import TranslationRequest, TranslationResult
from processors.base import DocumentProcessor
from core.dictionary_manager import DictionaryManager
from core.translation_engine import TranslationEngine
from core.chatbot import TranslationChatbot

import asyncio
import copy
import logging
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from models.data_classes import TranslationRequest, TranslationResult
from models.enums import SupportedLanguage
from processors.base import DocumentProcessor
from core.chatbot import TranslationChatbot
from core.dictionary_manager import DictionaryManager
from core.translation_engine import TranslationEngine

logger = logging.getLogger(__name__)


class TranslationAgent:
    """Enhanced translation agent for session-based workflow with interactive editing"""

    def __init__(self, openai_api_key: str = None, azure_api_key: str = None):
        self.document_processor = DocumentProcessor()
        self.translation_engine = TranslationEngine(openai_api_key, azure_api_key)
        self.dictionary_manager = DictionaryManager()
        self.chatbot = TranslationChatbot(self.translation_engine)

        # Session-specific state
        self.current_session = None
        self.pending_changes = {}
        self.translation_history = []

    def set_session_context(self, session_data: Dict[str, Any]):
        """Set current session context for the agent"""
        self.current_session = session_data
        file_type = session_data.get("file_type")
        # Extract translation pairs for chatbot context
        original_content = session_data.get("original_content", {})
        translated_content = session_data.get("translated_content", {})
        
        self.chatbot.current_translations = self._extract_translation_pairs(
            file_type, translated_content
        )
        self.chatbot.current_session = session_data
        self.pending_changes = {}

    async def process_chat_message(self, message: str) -> Dict[str, Any]:
        """Process chat message and return response with any content updates"""
        
        if not self.current_session:
            return {
                "response": "Không có session nào đang hoạt động. Vui lòng upload file trước.",
                "content_updated": False,
                "pending_changes": 0
            }

        # Process message through chatbot
        response = await self.chatbot.process_message(message, {
            "current_session": self.current_session,
            "original_content": self.current_session.get("original_content", {}),
            "translated_content": self.current_session.get("translated_content", {})
        })

        # Check if there are pending changes
        pending_count = len(self.chatbot.pending_changes)
        
        # Check if changes should be auto-applied
        content_updated = False
        if self.chatbot.auto_apply_changes and self.chatbot.pending_changes:
            content_updated = await self._apply_pending_changes()
            
        return {
            "response": response,
            "content_updated": content_updated,
            "pending_changes": pending_count,
            "updated_content": self.current_session.get("translated_content", {}) if content_updated else None
        }

    async def _apply_pending_changes(self) -> bool:
        """Apply pending changes to the current session content"""
        
        if not self.chatbot.pending_changes or not self.current_session:
            return False

        try:
            translated_content = self.current_session.get("translated_content", {})
            updated_content = self._apply_changes_to_content(
                translated_content, 
                self.chatbot.pending_changes
            )
            
            # Update session content
            self.current_session["translated_content"] = updated_content
            
            # Update chatbot's current translations
            original_content = self.current_session.get("original_content", {})
            self.chatbot.current_translations = self._extract_translation_pairs(
                original_content, updated_content
            )
            
            # Clear pending changes
            self.chatbot.pending_changes.clear()
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying changes: {e}")
            return False

    def _apply_changes_to_content(self, content: Dict[str, Any], changes: Dict[str, str]) -> Dict[str, Any]:
        """Apply changes to content structure"""
        
        updated_content = copy.deepcopy(content)
        
        if "text" in updated_content:
            # Simple text file
            for old_text, new_text in changes.items():
                updated_content["text"] = updated_content["text"].replace(old_text, new_text)
                
        elif "paragraphs" in updated_content:
            # DOCX file
            for para in updated_content["paragraphs"]:
                for old_text, new_text in changes.items():
                    para["text"] = para["text"].replace(old_text, new_text)
                    # Also update runs
                    for run in para.get("runs", []):
                        run["text"] = run["text"].replace(old_text, new_text)
                        
        elif "pages" in updated_content:
            # PDF file
            for page in updated_content["pages"]:
                for old_text, new_text in changes.items():
                    page["text"] = page["text"].replace(old_text, new_text)
                    
        elif "slides" in updated_content:
            # PPTX file
            for slide in updated_content["slides"]:
                for shape in slide.get("shapes", []):
                    for text_frame in shape.get("text_frames", []):
                        for old_text, new_text in changes.items():
                            if "translated_text" in text_frame:
                                text_frame["translated_text"] = text_frame["translated_text"].replace(old_text, new_text)
                            elif "text" in text_frame:
                                text_frame["text"] = text_frame["text"].replace(old_text, new_text)
                                
        elif "sheets" in updated_content:
            # XLSX file
            for sheet in updated_content["sheets"]:
                for row in sheet.get("cells", []):
                    for cell in row:
                        for old_text, new_text in changes.items():
                            if "value" in cell:
                                cell["value"] = str(cell["value"]).replace(old_text, new_text)
        
        return updated_content

    async def apply_all_pending_changes(self) -> Dict[str, Any]:
        """Manually apply all pending changes"""
        
        if not self.chatbot.pending_changes:
            return {
                "success": False,
                "message": "Không có thay đổi nào để áp dụng."
            }
        
        changes_count = len(self.chatbot.pending_changes)
        success = await self._apply_pending_changes()
        
        if success:
            return {
                "success": True,
                "message": f"Đã áp dụng {changes_count} thay đổi thành công.",
                "updated_content": self.current_session.get("translated_content", {})
            }
        else:
            return {
                "success": False,
                "message": "Có lỗi khi áp dụng thay đổi."
            }

    def get_pending_changes(self) -> Dict[str, str]:
        """Get current pending changes"""
        return self.chatbot.pending_changes.copy()

    def clear_pending_changes(self):
        """Clear all pending changes"""
        self.chatbot.pending_changes.clear()

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        
        if not self.current_session:
            return {"message": "Không có session nào đang hoạt động"}
        
        return {
            "session_id": self.current_session.get("session_id"),
            "file_name": self.current_session.get("file_name"),
            "file_type": self.current_session.get("file_type"),
            "source_lang": self.current_session.get("source_lang"),
            "target_lang": self.current_session.get("target_lang"),
            "created_at": self.current_session.get("created_at"),
            "word_count": self._count_words_in_session(),
            "pending_changes": len(self.chatbot.pending_changes),
            "chat_history_length": len(self.chatbot.conversation_history)
        }

    def _count_words_in_session(self) -> int:
        """Count words in current session content"""
        
        if not self.current_session:
            return 0
            
        content = self.current_session.get("original_content", {})
        return self._count_words(content)

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
        self, file_type: str, translated_content: Dict[str, Any]
    ) -> Dict[str, str]:
        """Extract original->translated pairs for chatbot"""

        pairs = {}
        try:
            processor = self.document_processor._get_processor(file_type)
            pairs = processor.get_pairs_translation(translated_content)
        except Exception as e:
            logger.warning(f"Error extracting translation pairs: {e}")

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
