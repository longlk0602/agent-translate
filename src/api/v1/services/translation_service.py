"""
Translation service integrating document processors and translators
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from api.core.dependencies import BaseTranslationService
from api.v1.services.document_service import DocumentProcessingService
from api.v1.services.session_service import SessionService
from core.agent import TranslationAgent
from core.chatbot import TranslationChatbot


class TranslationService:
    """Enhanced translation service using document processors"""

    def __init__(self, base_service: BaseTranslationService):
        self.base_service = base_service
        self.document_service = DocumentProcessingService()
        self.session_service = SessionService()
        self.translation_agent = None

    async def translate_text(
        self,
        text: Union[str, List[str]],
        target_lang: str = "vi",
        source_lang: Optional[str] = None,
        model_provider: str = "openai",
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.1,
        context: Optional[str] = None,
        glossary: Optional[Dict[str, str]] = None,
        use_context_aware: bool = True,
        batch_size: int = 10,
    ) -> Union[str, List[str]]:
        """Translate text or list of texts"""

        translator = self.base_service.get_translator(
            model_provider, model_name, temperature
        )

        if isinstance(text, str):
            return translator.translate_text(
                text=text,
                target_lang=target_lang,
                source_lang=source_lang,
                context=context,
                glossary=glossary,
            )
        elif isinstance(text, list):
            if use_context_aware and hasattr(
                translator, "translate_texts_with_context"
            ):
                return translator.translate_texts_with_context(
                    texts=text,
                    target_lang=target_lang,
                    source_lang=source_lang,
                    context=context,
                    glossary=glossary,
                    batch_size=batch_size,
                )
            else:
                return translator.translate_texts(
                    texts=text,
                    target_lang=target_lang,
                    source_lang=source_lang,
                    context=context,
                    glossary=glossary,
                )
        else:
            raise ValueError("Text must be string or list of strings")

    async def translate_document(
        self,
        file_path: str,
        target_lang: str = "vi",
        source_lang: Optional[str] = None,
        model_provider: str = "openai",
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.1,
        context: Optional[str] = None,
        glossary: Optional[Dict[str, str]] = None,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Translate document using proper processors"""

        start_time = time.time()

        try:
            # Check if file is supported
            if not self.document_service.is_supported_file(file_path):
                raise ValueError(f"Unsupported file type: {Path(file_path).suffix}")

            # Process document to extract translatable texts
            processing_result = self.document_service.process_document_for_translation(
                file_path
            )
            translatable_texts = processing_result["translatable_texts"]

            if not translatable_texts:
                raise ValueError("No translatable text found in document")

            # Add document context if not provided
            if context is None:
                file_name = Path(file_path).name
                context = f"Document translation for {file_name}"

            # Translate texts using context-aware translation
            translated_texts = await self.translate_text(
                text=translatable_texts,
                target_lang=target_lang,
                source_lang=source_lang,
                model_provider=model_provider,
                model_name=model_name,
                temperature=temperature,
                context=context,
                glossary=glossary,
                use_context_aware=True,
            )

            # Reconstruct document with translations
            reconstruction_result = self.document_service.create_translated_document(
                original_file_path=file_path,
                translations=translated_texts,
                output_path=output_path,
            )

            processing_time = time.time() - start_time

            if reconstruction_result["success"]:
                return {
                    "success": True,
                    "original_file": file_path,
                    "translated_file": reconstruction_result["translated_file"],
                    "source_lang": source_lang or "auto",
                    "target_lang": target_lang,
                    "model_used": f"{model_provider}_{model_name}",
                    "text_count": len(translatable_texts),
                    "translation_count": reconstruction_result["translation_count"],
                    "file_size": reconstruction_result["file_size"],
                    "processing_time": round(processing_time, 2),
                    "file_type": processing_result["file_type"],
                }
            else:
                return {
                    "success": False,
                    "error": reconstruction_result["error"],
                    "original_file": file_path,
                    "translated_file": None,
                    "source_lang": source_lang or "auto",
                    "target_lang": target_lang,
                    "model_used": f"{model_provider}_{model_name}",
                    "text_count": len(translatable_texts),
                    "translation_count": 0,
                    "file_size": None,
                    "file_type": processing_result["file_type"],
                    "processing_time": round(processing_time, 2),
                }

        except Exception as e:
            processing_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "original_file": file_path,
                "translated_file": None,
                "source_lang": source_lang or "auto",
                "target_lang": target_lang,
                "model_used": f"{model_provider}_{model_name}",
                "text_count": 0,
                "translation_count": 0,
                "file_size": None,
                "file_type": None,
                "processing_time": round(processing_time, 2),
            }

    async def compare_models_for_document(
        self,
        file_path: str,
        target_lang: str = "vi",
        models: List[Dict[str, Any]] = None,
        context: Optional[str] = None,
        glossary: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Compare multiple models for document translation"""

        if models is None:
            models = [
                {"provider": "openai", "model": "gpt-4o-mini", "temperature": 0.1},
                {"provider": "openai", "model": "gpt-4o", "temperature": 0.1},
            ]

        start_time = time.time()
        results = {}

        try:
            # Extract texts once
            processing_result = self.document_service.process_document_for_translation(
                file_path
            )
            translatable_texts = processing_result["translatable_texts"]

            if not translatable_texts:
                raise ValueError("No translatable text found in document")

            # Try each model
            for model_config in models:
                model_key = f"{model_config['provider']}_{model_config['model']}"

                try:
                    translated_texts = await self.translate_text(
                        text=translatable_texts,
                        target_lang=target_lang,
                        model_provider=model_config["provider"],
                        model_name=model_config["model"],
                        temperature=model_config.get("temperature", 0.1),
                        context=context,
                        glossary=glossary,
                        use_context_aware=True,
                    )

                    results[model_key] = {
                        "success": True,
                        "translated_texts": translated_texts,
                        "text_count": len(translated_texts),
                    }

                except Exception as e:
                    results[model_key] = {"success": False, "error": str(e)}

            processing_time = time.time() - start_time

            return {
                "success": True,
                "original_file": file_path,
                "target_lang": target_lang,
                "source_text_count": len(translatable_texts),
                "models_tested": list(results.keys()),
                "results": results,
                "processing_time": round(processing_time, 2),
            }

        except Exception as e:
            processing_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "original_file": file_path,
                "processing_time": round(processing_time, 2),
            }

    def get_document_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about document without translating"""

        try:
            if not self.document_service.is_supported_file(file_path):
                raise ValueError(f"Unsupported file type: {Path(file_path).suffix}")

            processing_result = self.document_service.process_document_for_translation(
                file_path
            )

            return {
                "success": True,
                "file_path": file_path,
                "file_type": processing_result["file_type"],
                "text_count": processing_result["text_count"],
                "translatable_texts": processing_result["translatable_texts"][
                    :5
                ],  # Preview
                "is_supported": True,
                "file_size": Path(file_path).stat().st_size,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path,
                "is_supported": False,
            }

    def get_supported_formats(self) -> Dict[str, Any]:
        """Get supported document formats"""
        return {
            "success": True,
            "supported_extensions": self.document_service.get_supported_extensions(),
            "processors": {
                ".txt": "Text files - Plain text documents",
                ".pdf": "PDF files - Portable Document Format",
                ".docx": "Word documents - Microsoft Word format",
                ".pptx": "PowerPoint presentations - Microsoft PowerPoint format",
                ".xlsx": "Excel spreadsheets - Microsoft Excel format",
            },
        }

    # Session-based translation methods
    async def create_translation_session(
        self,
        file_path: str,
        target_lang: str = "vi",
        source_lang: Optional[str] = None,
        model_provider: str = "openai",
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.1,
        context: Optional[str] = None,
        glossary: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a translation session with extracted and translated content"""

        start_time = time.time()

        try:
            # Check if file is supported
            if not self.document_service.is_supported_file(file_path):
                raise ValueError(f"Unsupported file type: {Path(file_path).suffix}")

            # Extract content from document
            processing_result = self.document_service.process_document_for_translation(
                file_path
            )
            original_content = processing_result["document_structure"]
            translatable_texts = processing_result["translatable_texts"]

            if not translatable_texts:
                raise ValueError("No translatable text found in document")

            # Add document context if not provided
            if not context:
                context = f"Document type: {processing_result['file_type']}"

            # Translate texts
            translated_texts = await self.translate_text(
                text=translatable_texts,
                target_lang=target_lang,
                source_lang=source_lang,
                model_provider=model_provider,
                model_name=model_name,
                temperature=temperature,
                context=context,
                glossary=glossary,
                use_context_aware=True,
            )

            # Create translated content structure
            translated_content = self._update_content_with_translations(
                original_content, translatable_texts, translated_texts
            )

            # Create session
            session_id = self.session_service.create_session(
                file_name=Path(file_path).name,
                file_path=file_path,
                file_type=processing_result["file_type"],
                original_content=original_content,
                translated_content=translated_content,
                source_lang=source_lang or "auto",
                target_lang=target_lang,
                model_provider=model_provider,
                model_name=model_name
            )

            processing_time = time.time() - start_time

            return {
                "success": True,
                "session_id": session_id,
                "file_name": Path(file_path).name,
                "file_type": processing_result["file_type"],
                "original_content": original_content,
                "translated_content": translated_content,
                "source_lang": source_lang or "auto",
                "target_lang": target_lang,
                "model_used": f"{model_provider}_{model_name}",
                "text_count": len(translatable_texts),
                "translation_count": len(translated_texts),
                "processing_time": round(processing_time, 2),
            }

        except Exception as e:
            processing_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "processing_time": round(processing_time, 2),
            }

    def get_session_content(self, session_id: str) -> Dict[str, Any]:
        """Get session content"""

        session = self.session_service.get_session(session_id)
        if not session:
            return {
                "success": False,
                "error": "Session not found"
            }

        return {
            "success": True,
            "session_id": session_id,
            "file_name": session.file_name,
            "file_type": session.file_type,
            "original_content": session.original_content,
            "translated_content": session.translated_content,
            "source_lang": session.source_lang,
            "target_lang": session.target_lang,
            "model_used": f"{session.model_provider}_{session.model_name}",
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "is_finalized": session.is_finalized,
            "chat_history": session.chat_history,
        }

    async def chat_with_session(
        self,
        session_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Chat about translation in session"""

        session = self.session_service.get_session(session_id)
        if not session:
            return {
                "success": False,
                "error": "Session not found"
            }

        try:
            # Initialize translation agent if needed
            if not self.translation_agent:
                self.translation_agent = TranslationAgent()

            # Set up chatbot with session content
            chatbot = self.translation_agent.chatbot
            chatbot.current_translations = self._extract_translation_pairs(
                session.original_content, session.translated_content
            )

            # Process message
            response = await chatbot.process_message(message)

            # Update session with any changes
            if chatbot.pending_changes:
                # Apply pending changes to translated content
                updated_content = self._apply_changes_to_content(
                    session.translated_content,
                    chatbot.pending_changes
                )
                self.session_service.update_session_content(session_id, updated_content)

            # Save chat history
            self.session_service.add_chat_message(session_id, message, response)

            return {
                "success": True,
                "response": response,
                "pending_changes": len(chatbot.pending_changes),
                "session_id": session_id
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }

    async def finalize_and_download_session(
        self,
        session_id: str,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Finalize session and create downloadable file"""

        session = self.session_service.get_session(session_id)
        if not session:
            return {
                "success": False,
                "error": "Session not found"
            }

        try:
            # Generate output path if not provided
            if not output_path:
                file_path = Path(session.file_path)
                output_path = str(file_path.parent / f"{file_path.stem}_{session.target_lang}{file_path.suffix}")

            # Reconstruct document with translated content
            final_path = self.document_service.reconstruct_document_from_structure(
                session.file_path,
                session.translated_content,
                output_path
            )

            # Finalize session
            self.session_service.finalize_session(session_id)

            return {
                "success": True,
                "session_id": session_id,
                "output_file": final_path,
                "original_file": session.file_path,
                "file_name": Path(final_path).name,
                "download_ready": True
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }

    def list_sessions(self) -> Dict[str, Any]:
        """List all translation sessions"""

        try:
            sessions = self.session_service.list_sessions()
            return {
                "success": True,
                "sessions": sessions,
                "total_count": len(sessions)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Delete a translation session"""

        try:
            success = self.session_service.delete_session(session_id)
            return {
                "success": success,
                "session_id": session_id,
                "message": "Session deleted successfully" if success else "Session not found"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }

    # Helper methods
    def _update_content_with_translations(
        self,
        original_content: Dict[str, Any],
        original_texts: List[str],
        translated_texts: List[str]
    ) -> Dict[str, Any]:
        """Update document structure with translated texts"""

        # Create translation mapping
        translation_map = dict(zip(original_texts, translated_texts))
        
        # Deep copy of original content
        import copy
        translated_content = copy.deepcopy(original_content)
        
        # Apply translations based on document structure
        self._apply_translations_to_structure(translated_content, translation_map)
        
        return translated_content

    def _apply_translations_to_structure(
        self,
        content: Dict[str, Any],
        translation_map: Dict[str, str]
    ) -> None:
        """Apply translations to document structure"""

        if "text" in content and content["text"] in translation_map:
            content["text"] = translation_map[content["text"]]
        
        elif "paragraphs" in content:
            for para in content["paragraphs"]:
                if para["text"] in translation_map:
                    para["text"] = translation_map[para["text"]]
        
        elif "pages" in content:
            for page in content["pages"]:
                if page["text"] in translation_map:
                    page["text"] = translation_map[page["text"]]
        
        elif "slides" in content:
            for slide in content["slides"]:
                for frame in slide["text_frames"]:
                    if frame["text"] in translation_map:
                        frame["text"] = translation_map[frame["text"]]

    def _extract_translation_pairs(
        self,
        original_content: Dict[str, Any],
        translated_content: Dict[str, Any]
    ) -> Dict[str, str]:
        """Extract translation pairs for chatbot"""

        pairs = {}
        
        if "text" in original_content and "text" in translated_content:
            pairs[original_content["text"]] = translated_content["text"]
        
        elif "paragraphs" in original_content and "paragraphs" in translated_content:
            for orig_para, trans_para in zip(
                original_content["paragraphs"], translated_content["paragraphs"]
            ):
                pairs[orig_para["text"]] = trans_para["text"]
        
        # Add more structure handling as needed
        
        return pairs

    def _apply_changes_to_content(
        self,
        content: Dict[str, Any],
        changes: Dict[str, str]
    ) -> Dict[str, Any]:
        """Apply chatbot changes to content structure"""

        import copy
        updated_content = copy.deepcopy(content)
        
        # Apply changes to all text fields
        for old_text, new_text in changes.items():
            self._replace_text_in_structure(updated_content, old_text, new_text)
        
        return updated_content

    def _replace_text_in_structure(
        self,
        content: Dict[str, Any],
        old_text: str,
        new_text: str
    ) -> None:
        """Replace text in document structure"""

        if "text" in content:
            content["text"] = content["text"].replace(old_text, new_text)
        
        elif "paragraphs" in content:
            for para in content["paragraphs"]:
                para["text"] = para["text"].replace(old_text, new_text)
        
        elif "pages" in content:
            for page in content["pages"]:
                page["text"] = page["text"].replace(old_text, new_text)
        
        elif "slides" in content:
            for slide in content["slides"]:
                for frame in slide["text_frames"]:
                    frame["text"] = frame["text"].replace(old_text, new_text)