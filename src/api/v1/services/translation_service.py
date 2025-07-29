"""
Translation service integrating document processors and translators
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from api.core.dependencies import BaseTranslationService
from api.v1.services.document_service import DocumentProcessingService


class TranslationService:
    """Enhanced translation service using document processors"""

    def __init__(self, base_service: BaseTranslationService):
        self.base_service = base_service
        self.document_service = DocumentProcessingService()

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
