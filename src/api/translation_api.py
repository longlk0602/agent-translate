"""
API interface for the translation agent
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..core.agent import TranslationAgent
from ..models.data_classes import TranslationRequest
from ..models.enums import FileType, SupportedLanguage
from ..translate.azure_translator import AzureTranslator
from ..translate.openai_translator import OpenAITranslator


class TranslationAPI:
    """Comprehensive API interface for translation services"""

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        azure_api_key: Optional[str] = None,
        azure_region: Optional[str] = None,
    ):
        """
        Initialize Translation API

        Args:
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key
            azure_api_key: Azure Translator API key
            azure_region: Azure region
        """
        self.agent = TranslationAgent(openai_api_key, anthropic_api_key)
        self.openai_api_key = openai_api_key
        self.azure_api_key = azure_api_key
        self.azure_region = azure_region

        # Available models
        self.available_models = {
            "openai": {
                "gpt-4o": {
                    "name": "GPT-4o",
                    "description": "Latest GPT-4 optimized model",
                },
                "gpt-4o-mini": {
                    "name": "GPT-4o Mini",
                    "description": "Fast and cost-effective GPT-4 model",
                },
                "gpt-4-turbo": {
                    "name": "GPT-4 Turbo",
                    "description": "High-performance GPT-4 model",
                },
                "gpt-3.5-turbo": {
                    "name": "GPT-3.5 Turbo",
                    "description": "Fast and affordable model",
                },
            },
            "azure": {
                "translator": {
                    "name": "Azure Translator",
                    "description": "Microsoft's translation service",
                }
            },
        }

    def translate_text(
        self,
        text: Union[str, List[str]],
        target_lang: str = "vi",
        source_lang: Optional[str] = None,
        model_provider: str = "openai",
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.1,
        context: Optional[str] = None,
        glossary: Optional[Dict[str, str]] = None,
        glossary_file: Optional[str] = None,
        use_context_aware: bool = True,
        batch_size: int = 10,
    ) -> Union[str, List[str]]:
        """
        Translate text or list of texts

        Args:
            text: Single text string or list of text strings to translate
            target_lang: Target language code (default: "vi" for Vietnamese)
            source_lang: Source language code (optional, auto-detect if None)
            model_provider: Model provider ("openai" or "azure")
            model_name: Specific model name to use
            temperature: Model temperature for consistency (0.0-1.0)
            context: Additional context for translation
            glossary: Dictionary of custom term translations
            glossary_file: Path to glossary file (.json, .csv, .txt)
            use_context_aware: Use context-aware translation for lists (default: True)
            batch_size: Batch size for context-aware translation

        Returns:
            Translated text (string) or list of translated texts (list)

        Raises:
            ValueError: If invalid parameters are provided
            Exception: If translation fails
        """
        # Load glossary from file if provided
        final_glossary = glossary or {}
        if glossary_file:
            file_glossary = self._load_glossary_from_file(glossary_file)
            final_glossary.update(file_glossary)

        # Validate inputs
        if not text:
            raise ValueError("Text input cannot be empty")

        if model_provider not in self.available_models:
            raise ValueError(f"Unsupported model provider: {model_provider}")

        if model_name not in self.available_models[model_provider]:
            raise ValueError(
                f"Unsupported model: {model_name} for provider {model_provider}"
            )

        # Initialize translator based on provider
        translator = self._get_translator(model_provider, model_name, temperature)

        # Handle single text vs list of texts
        if isinstance(text, str):
            # Single text translation
            return translator.translate_text(
                text=text,
                target_lang=target_lang,
                source_lang=source_lang,
                context=context,
                glossary=final_glossary,
            )

        elif isinstance(text, list):
            # List of texts translation
            if use_context_aware and hasattr(
                translator, "translate_texts_with_context"
            ):
                # Use context-aware translation for better consistency
                return translator.translate_texts_with_context(
                    texts=text,
                    target_lang=target_lang,
                    source_lang=source_lang,
                    context=context,
                    glossary=final_glossary,
                    batch_size=batch_size,
                )
            else:
                # Use regular batch translation
                return translator.translate_texts(
                    texts=text,
                    target_lang=target_lang,
                    source_lang=source_lang,
                    context=context,
                    glossary=final_glossary,
                )
        else:
            raise ValueError("Text input must be a string or list of strings")

    def translate_with_multiple_models(
        self,
        text: Union[str, List[str]],
        target_lang: str = "vi",
        models: List[Dict[str, Any]] = None,
        context: Optional[str] = None,
        glossary: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Translate using multiple models for comparison

        Args:
            text: Text to translate
            target_lang: Target language
            models: List of model configurations [{"provider": "openai", "model": "gpt-4o", "temperature": 0.1}]
            context: Translation context
            glossary: Custom glossary

        Returns:
            Dictionary with results from each model
        """
        if models is None:
            models = [
                {"provider": "openai", "model": "gpt-4o-mini", "temperature": 0.1},
                {"provider": "openai", "model": "gpt-4o", "temperature": 0.1},
            ]

        results = {}

        for model_config in models:
            try:
                model_key = f"{model_config['provider']}_{model_config['model']}"
                results[model_key] = self.translate_text(
                    text=text,
                    target_lang=target_lang,
                    model_provider=model_config["provider"],
                    model_name=model_config["model"],
                    temperature=model_config.get("temperature", 0.1),
                    context=context,
                    glossary=glossary,
                    use_context_aware=isinstance(text, list),
                )
            except Exception as e:
                results[model_key] = f"Error: {str(e)}"

        return results

    def get_available_models(self) -> Dict[str, Any]:
        """
        Get list of available translation models

        Returns:
            Dictionary of available models by provider
        """
        return self.available_models

    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get supported language codes and names

        Returns:
            Dictionary mapping language codes to names
        """
        return {
            "vi": "Vietnamese",
            "en": "English",
            "zh": "Chinese (Simplified)",
            "zh-TW": "Chinese (Traditional)",
            "ja": "Japanese",
            "ko": "Korean",
            "fr": "French",
            "de": "German",
            "es": "Spanish",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ar": "Arabic",
            "hi": "Hindi",
            "th": "Thai",
            "id": "Indonesian",
            "ms": "Malay",
            "tl": "Filipino",
        }

    def create_glossary_from_file(
        self,
        source_file: str,
        target_file: str,
        source_lang: str = "en",
        target_lang: str = "vi",
    ) -> Dict[str, str]:
        """
        Create glossary by comparing source and target files

        Args:
            source_file: Path to source language file
            target_file: Path to target language file
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Generated glossary dictionary
        """
        # This would implement automatic glossary extraction
        # For now, return empty dict - can be enhanced later
        return {}

    def save_translation_result(
        self, result: Union[str, List[str]], output_file: str, format_type: str = "auto"
    ) -> bool:
        """
        Save translation result to file

        Args:
            result: Translation result
            output_file: Output file path
            format_type: Output format ("json", "txt", "csv", "auto")

        Returns:
            True if successful, False otherwise
        """
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Auto-detect format from extension
            if format_type == "auto":
                format_type = output_path.suffix.lower().lstrip(".")

            if format_type == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

            elif format_type == "txt":
                with open(output_path, "w", encoding="utf-8") as f:
                    if isinstance(result, list):
                        f.write("\n".join(result))
                    else:
                        f.write(result)

            elif format_type == "csv":
                import csv

                with open(output_path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    if isinstance(result, list):
                        for i, text in enumerate(result, 1):
                            writer.writerow([i, text])
                    else:
                        writer.writerow([1, result])

            return True

        except Exception as e:
            print(f"Error saving result: {e}")
            return False

    def _get_translator(self, provider: str, model_name: str, temperature: float):
        """Get translator instance based on provider and model"""
        if provider == "openai":
            if not self.openai_api_key:
                raise ValueError("OpenAI API key is required for OpenAI models")
            return OpenAITranslator(
                api_key=self.openai_api_key, model=model_name, temperature=temperature
            )

        elif provider == "azure":
            if not self.azure_api_key:
                raise ValueError("Azure API key is required for Azure models")
            return AzureTranslator(api_key=self.azure_api_key, region=self.azure_region)

        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _load_glossary_from_file(self, file_path: str) -> Dict[str, str]:
        """Load glossary from file using OpenAI translator's method"""
        if self.openai_api_key:
            temp_translator = OpenAITranslator(api_key=self.openai_api_key)
            return temp_translator.load_glossary_from_file(file_path)
        else:
            # Fallback: simple file loading
            return self._simple_load_glossary(file_path)

    def _simple_load_glossary(self, file_path: str) -> Dict[str, str]:
        """Simple glossary loading fallback"""
        glossary = {}
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Glossary file not found: {file_path}")

        if path.suffix.lower() == ".json":
            with open(path, "r", encoding="utf-8") as f:
                glossary = json.load(f)
        elif path.suffix.lower() == ".txt":
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and "→" in line:
                        parts = line.split("→", 1)
                        if len(parts) == 2:
                            glossary[parts[0].strip()] = parts[1].strip()

        return glossary

    async def translate_file(
        self,
        file_path: str,
        target_language: str,
        source_language: str = None,
        custom_dictionary_path: str = None,
        reference_files: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Translate a file

        Args:
            file_path: Path to the source file
            target_language: Target language code (e.g., 'vi', 'en')
            source_language: Source language code (optional)
            custom_dictionary_path: Path to custom dictionary file (optional)
            reference_files: List of reference file paths (optional)

        Returns:
            Dictionary containing translation result
        """

        try:
            # Load custom dictionary if provided
            custom_dict = None
            if custom_dictionary_path:
                self.agent.load_custom_dictionary(custom_dictionary_path)
                custom_dict = self.agent.dictionary_manager.dictionaries.get("default")

            # Create translation request
            request = TranslationRequest(
                source_file_path=file_path,
                target_language=SupportedLanguage(target_language),
                source_language=(
                    SupportedLanguage(source_language) if source_language else None
                ),
                custom_dictionary=custom_dict,
                reference_files=reference_files,
            )

            # Perform translation
            result = await self.agent.translate_document(request)

            return {
                "success": True,
                "translated_file_path": result.translated_file_path,
                "word_count": result.word_count,
                "processing_time": result.processing_time,
                "errors": result.errors,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def chat_about_translation(self, message: str) -> Dict[str, Any]:
        """
        Chat with the translation agent about changes

        Args:
            message: User message

        Returns:
            Dictionary containing chat response
        """

        try:
            response = await self.agent.chat_with_agent(message)

            return {
                "success": True,
                "response": response,
                "pending_changes": len(self.agent.chatbot.pending_changes),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
