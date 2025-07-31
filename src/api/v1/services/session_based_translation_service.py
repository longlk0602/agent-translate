"""
Enhanced translation service using existing processors with session management
"""

import logging
import time
import copy
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from api.core.dependencies import BaseTranslationService
from api.v1.services.session_service import SessionService
from processors.base import DocumentProcessor
from core.agent import TranslationAgent


class EnhancedTranslationService:
    """Enhanced translation service using existing processors and session management"""

    def __init__(self, base_service: BaseTranslationService):
        self.base_service = base_service
        self.document_processor = DocumentProcessor()
        self.session_service = SessionService()
        self.translation_agent = None
        self.logger = logging.getLogger(__name__)

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

    # Session-based translation methods using existing processors
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
        """Create a translation session with extracted and translated content using existing processors"""

        start_time = time.time()

        try:
            # Check if file extension is supported
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.document_processor.processors:
                raise ValueError(f"Unsupported file type: {file_ext}")

            # Get the appropriate processor
            processor = self.document_processor._get_processor(file_ext)
            print(f"Using processor: {processor.__class__.__name__}")
            # Extract content using existing processor
            original_content = processor.extract_text(file_path)
            print("Content extracted successfully")
            # Get translatable texts using existing processor method
            print(original_content)
            translatable_texts = processor.get_translatable_texts(original_content)
            print(f"Found {len(translatable_texts)} translatable texts")
            if not translatable_texts:
                raise ValueError("No translatable text found in document")

            # Add document context if not provided
            if not context:
                context = f"Document type: {file_ext}"

            # Translate texts using our translation service
            print(f"Translating {len(translatable_texts)} texts from {file_ext} document")
            
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

            print(f"Translated {len(translated_texts)} texts")
            # Apply translations using existing processor method
            translated_content = processor.apply_translations(
                original_content, translated_texts
            )
            print("Translations applied successfully")
            # Create session
            session_id = self.session_service.create_session(
                file_name=Path(file_path).name,
                file_path=file_path,
                file_type=file_ext,
                original_content=original_content,
                translated_content=translated_content,
                source_lang=source_lang or "auto",
                target_lang=target_lang,
                model_provider=model_provider,
                model_name=model_name
            )
            print(f"Session created with ID: {session_id}")
            processing_time = time.time() - start_time

            return {
                "success": True,
                "session_id": session_id,
                "file_name": Path(file_path).name,
                "file_type": file_ext,
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
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "is_finalized": session.is_finalized,
            "chat_history": session.chat_history,
        }

    async def chat_with_session(
        self,
        session_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Chat about translation in session using enhanced agent"""

        self.logger.info(f"Chat session started - ID: {session_id}")
        self.logger.debug(f"User message: {message}")

        session = self.session_service.get_session(session_id)
        if not session:
            self.logger.error(f"Session not found: {session_id}")
            return {
                "success": False,
                "error": "Session not found"
            }

        self.logger.info(f"Session found - File: {session.file_name}, Type: {session.file_type}")

        try:
            # Initialize translation agent if needed
            if not self.translation_agent:
                self.logger.info("Initializing translation agent")
                self.translation_agent = TranslationAgent()

            # Set session context for the agent
            session_data = {
                "session_id": session_id,
                "file_name": session.file_name,
                "file_type": session.file_type,
                "original_content": session.original_content,
                "translated_content": session.translated_content,
                "source_lang": session.source_lang,
                "target_lang": session.target_lang,
                "model_provider": session.model_provider,
                "model_name": session.model_name,
                "created_at": session.created_at,
                "updated_at": session.updated_at
            }
            
            self.logger.debug(f"Setting session context for agent - Session: {session_id}")
            self.translation_agent.set_session_context(session_data)

            # Process chat message
            self.logger.info(f"Processing chat message with translation agent - Session: {session_id}")
            chat_result = await self.translation_agent.process_chat_message(message)
            
            self.logger.info(f"Chat processing completed - Session: {session_id}, "
                           f"Content updated: {chat_result.get('content_updated', False)}")
            
            # Add to chat history
            from datetime import datetime
            session.chat_history.append({
                "timestamp": datetime.now().isoformat(),
                "user_message": message,
                "agent_response": chat_result["response"]
            })
            self.logger.debug(f"Added message to chat history - Session: {session_id}")

            # Update session content if changes were applied
            if chat_result.get("content_updated") and chat_result.get("updated_content"):
                self.logger.info(f"Updating session content - Session: {session_id}")
                session.translated_content = chat_result["updated_content"]
                session.updated_at = time.time()
                self.logger.info(f"Session content updated successfully - Session: {session_id}")

            # Save session
            self.logger.debug(f"Saving session - ID: {session_id}")
            self.session_service.update_session(session_id, session)
            self.logger.info(f"Session saved successfully - ID: {session_id}")

            result = {
                "success": True,
                "response": chat_result["response"],
                "content_updated": chat_result.get("content_updated", False),
                "pending_changes": chat_result.get("pending_changes", 0),
                "chat_history": session.chat_history[-10:],  # Last 10 messages
                "updated_content": chat_result.get("updated_content") if chat_result.get("content_updated") else None
            }
            
            self.logger.info(f"Chat session completed successfully - ID: {session_id}, "
                           f"Content updated: {result['content_updated']}, "
                           f"Pending changes: {result['pending_changes']}")
            
            return result

        except Exception as e:
            self.logger.error(f"Error in chat session {session_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def finalize_and_download_session(
        self,
        session_id: str,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Finalize session and create downloadable file using existing processors"""

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

            # Get the appropriate processor for reconstruction
            processor = self.document_processor._get_processor(session.file_type)
            
            # Reconstruct document using existing processor method
            final_path = processor.reconstruct_document(
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

    def get_supported_formats(self) -> Dict[str, Any]:
        """Get supported document formats from existing processors"""
        
        return {
            "success": True,
            "supported_extensions": list(self.document_processor.processors.keys()),
            "processors": {
                ".txt": "Text files - Plain text documents",
                ".pdf": "PDF files - Portable Document Format",
                ".docx": "Word documents - Microsoft Word format",
                ".pptx": "PowerPoint presentations - Microsoft PowerPoint format",
                ".xlsx": "Excel spreadsheets - Microsoft Excel format",
            },
        }

    # Helper methods adapted for existing processor structure
    def _extract_translation_pairs_from_content(
        self,
        original_content: Dict[str, Any],
        translated_content: Dict[str, Any],
        file_type: str
    ) -> Dict[str, str]:
        """Extract translation pairs for chatbot based on file type and existing structure"""

        pairs = {}
        
        if file_type == ".txt":
            # For TXT files
            if "text" in original_content and "text" in translated_content:
                pairs[original_content["text"]] = translated_content["text"]
        
        elif file_type == ".docx":
            # For DOCX files - using existing structure
            if "paragraphs" in original_content and "paragraphs" in translated_content:
                for orig_para, trans_para in zip(
                    original_content["paragraphs"], translated_content["paragraphs"]
                ):
                    pairs[orig_para["original_text"]] = trans_para["text"]
            
            # Tables
            if "tables" in original_content and "tables" in translated_content:
                for orig_table, trans_table in zip(
                    original_content["tables"], translated_content["tables"]
                ):
                    for orig_row, trans_row in zip(orig_table["rows"], trans_table["rows"]):
                        for orig_cell, trans_cell in zip(orig_row["cells"], trans_row["cells"]):
                            if orig_cell["original_text"].strip():
                                pairs[orig_cell["original_text"]] = trans_cell["text"]
        
        elif file_type == ".pptx":
            # For PPTX files - would need to check pptx_processor structure
            pass
        
        elif file_type == ".xlsx":
            # For XLSX files - would need to check xlsx_processor structure
            pass
        
        elif file_type == ".pdf":
            # For PDF files - would need to check pdf_processor structure
            pass
        
        return pairs

    def _apply_changes_to_session_content(
        self,
        content: Dict[str, Any],
        changes: Dict[str, str],
        file_type: str
    ) -> Dict[str, Any]:
        """Apply chatbot changes to content structure based on file type"""

        updated_content = copy.deepcopy(content)
        
        if file_type == ".txt":
            # For TXT files
            if "text" in updated_content:
                for old_text, new_text in changes.items():
                    updated_content["text"] = updated_content["text"].replace(old_text, new_text)
        
        elif file_type == ".docx":
            # For DOCX files
            for old_text, new_text in changes.items():
                # Update paragraphs
                if "paragraphs" in updated_content:
                    for para in updated_content["paragraphs"]:
                        para["text"] = para["text"].replace(old_text, new_text)
                
                # Update tables
                if "tables" in updated_content:
                    for table in updated_content["tables"]:
                        for row in table["rows"]:
                            for cell in row["cells"]:
                                cell["text"] = cell["text"].replace(old_text, new_text)
                
                # Update headers and footers
                if "headers" in updated_content:
                    for header in updated_content["headers"]:
                        header["text"] = header["text"].replace(old_text, new_text)
                
                if "footers" in updated_content:
                    for footer in updated_content["footers"]:
                        footer["text"] = footer["text"].replace(old_text, new_text)
        
        # Add support for other file types as needed
        
        return updated_content

    # Legacy methods for backward compatibility
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
        """Legacy method: Translate document directly without session"""

        # Create session and immediately finalize
        session_result = await self.create_translation_session(
            file_path=file_path,
            target_lang=target_lang,
            source_lang=source_lang,
            model_provider=model_provider,
            model_name=model_name,
            temperature=temperature,
            context=context,
            glossary=glossary,
        )

        if not session_result["success"]:
            return session_result

        # Finalize and download
        download_result = await self.finalize_and_download_session(
            session_result["session_id"],
            output_path
        )

        if download_result["success"]:
            return {
                "success": True,
                "original_file": file_path,
                "translated_file": download_result["output_file"],
                "source_lang": session_result["source_lang"],
                "target_lang": session_result["target_lang"],
                "model_used": session_result["model_used"],
                "text_count": session_result["text_count"],
                "translation_count": session_result["translation_count"],
                "file_size": Path(file_path).stat().st_size,
                "file_type": session_result["file_type"],
                "processing_time": session_result["processing_time"],
            }
        else:
            return download_result
