import os
from typing import Dict, List, Optional

import openai

from .base import BaseTranslator


class OpenAITranslator(BaseTranslator):
    """OpenAI-based translator implementation"""

    def __init__(
        self, api_key: str, model: str = "gpt-4-turbo-preview", temperature: float = 0.1
    ):
        """
        Initialize OpenAI translator

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use for translation
            temperature: Model temperature for translation consistency
        """
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.client = openai.OpenAI(api_key=api_key)

    def translate_text(
        self,
        text: str,
        target_lang: str = "vi",
        source_lang: Optional[str] = None,
        context: Optional[str] = None,
        custom_dict: Optional[Dict[str, str]] = None,
        glossary: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Translate a single text block using OpenAI

        Args:
            text: Text to translate
            target_lang: Target language code (default: "vi" for Vietnamese)
            source_lang: Source language code (optional)
            context: Additional context for translation
            custom_dict: Custom dictionary for specific term translations (deprecated, use glossary)
            glossary: Glossary/Dictionary for specific term translations

        Returns:
            Translated text
        """
        if not text.strip():
            return text

        # Merge custom_dict and glossary (glossary takes precedence)
        final_glossary = {}
        if custom_dict:
            final_glossary.update(custom_dict)
        if glossary:
            final_glossary.update(glossary)

        try:
            # Pre-process text with glossary terms if available
            preprocessed_text = text
            glossary_markers = {}

            if final_glossary:
                preprocessed_text, glossary_markers = self._preprocess_with_glossary(
                    text, final_glossary
                )

            # Build system prompt
            system_prompt = self._build_system_prompt(
                target_lang, source_lang, context, final_glossary
            )

            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": preprocessed_text},
                ],
                temperature=self.temperature,
            )

            translated = response.choices[0].message.content

            # Post-process: restore glossary terms and apply final dictionary
            if final_glossary:
                translated = self._postprocess_with_glossary(
                    translated, glossary_markers, final_glossary
                )

            return translated if translated else ""

        except Exception as e:
            raise Exception(f"OpenAI translation error: {e}")

    def translate_texts(
        self,
        texts: List[str],
        target_lang: str = "vi",
        source_lang: Optional[str] = None,
        context: Optional[str] = None,
        custom_dict: Optional[Dict[str, str]] = None,
        glossary: Optional[Dict[str, str]] = None,
    ) -> List[str]:
        """
        Translate a list of text blocks

        Args:
            texts: List of texts to translate
            target_lang: Target language code (default: "vi" for Vietnamese)
            source_lang: Source language code (optional)
            context: Additional context for translation
            custom_dict: Custom dictionary for specific term translations (deprecated, use glossary)
            glossary: Glossary/Dictionary for specific term translations

        Returns:
            List of translated texts
        """
        results = []
        for text in texts:
            translated = self.translate_text(
                text, target_lang, source_lang, context, custom_dict, glossary
            )
            results.append(translated)
        return results

    def translate_texts_with_context(
        self,
        texts: List[str],
        target_lang: str = "vi",
        source_lang: Optional[str] = None,
        context: Optional[str] = None,
        custom_dict: Optional[Dict[str, str]] = None,
        glossary: Optional[Dict[str, str]] = None,
        batch_size: int = 10,
    ) -> List[str]:
        """
        Translate a list of text blocks using the entire list as context for consistency

        Args:
            texts: List of texts to translate
            target_lang: Target language code (default: "vi" for Vietnamese)
            source_lang: Source language code (optional)
            context: Additional context for translation
            custom_dict: Custom dictionary for specific term translations (deprecated, use glossary)
            glossary: Glossary/Dictionary for specific term translations
            batch_size: Number of texts to translate in each batch (default: 10)

        Returns:
            List of translated texts in the same order as input
        """
        if not texts:
            return []

        # Filter out empty texts but remember their positions
        text_mapping = {}
        non_empty_texts = []
        for i, text in enumerate(texts):
            if text.strip():
                text_mapping[len(non_empty_texts)] = i
                non_empty_texts.append(text)

        if not non_empty_texts:
            return texts  # Return original if all texts are empty

        # Merge custom_dict and glossary (glossary takes precedence)
        final_glossary = {}
        if custom_dict:
            final_glossary.update(custom_dict)
        if glossary:
            final_glossary.update(glossary)

        # Process texts in batches
        all_translated = []

        for i in range(0, len(non_empty_texts), batch_size):
            batch_texts = non_empty_texts[i : i + batch_size]

            # Create context from the entire document for consistency
            document_context = "\n".join(
                non_empty_texts[:50]
            )  # Use first 50 texts as context
            if context:
                document_context = f"{context}\n\nDocument context:\n{document_context}"

            try:
                # Preprocess all texts in batch with glossary
                preprocessed_batch = []
                batch_glossary_markers = []

                for text in batch_texts:
                    if final_glossary:
                        preprocessed_text, glossary_markers = (
                            self._preprocess_with_glossary(text, final_glossary)
                        )
                        preprocessed_batch.append(preprocessed_text)
                        batch_glossary_markers.append(glossary_markers)
                    else:
                        preprocessed_batch.append(text)
                        batch_glossary_markers.append({})

                # Build system prompt for batch translation
                system_prompt = self._build_batch_system_prompt(
                    target_lang, source_lang, document_context, final_glossary
                )

                # Create numbered input for the model
                numbered_input = ""
                for idx, text in enumerate(preprocessed_batch):
                    numbered_input += f"{idx + 1}. {text}\n"

                # Make API call
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": numbered_input.strip()},
                    ],
                    temperature=self.temperature,
                )

                translated_response = response.choices[0].message.content

                # Parse the numbered response
                batch_translated = self._parse_numbered_response(
                    translated_response, len(batch_texts)
                )

                # Post-process with glossary markers
                final_batch = []
                for j, translated_text in enumerate(batch_translated):
                    if j < len(batch_glossary_markers) and batch_glossary_markers[j]:
                        final_text = self._postprocess_with_glossary(
                            translated_text, batch_glossary_markers[j], final_glossary
                        )
                        final_batch.append(final_text)
                    else:
                        final_batch.append(translated_text)

                all_translated.extend(final_batch)

            except Exception as e:
                # Fallback: translate individually if batch fails
                print(
                    f"Batch translation failed, falling back to individual translation: {e}"
                )
                for text in batch_texts:
                    try:
                        translated = self.translate_text(
                            text,
                            target_lang,
                            source_lang,
                            context,
                            custom_dict,
                            glossary,
                        )
                        all_translated.append(translated)
                    except Exception:
                        all_translated.append(
                            text
                        )  # Keep original if translation fails

        # Reconstruct the full result list with proper positioning
        result = [""] * len(texts)
        for i, translated in enumerate(all_translated):
            original_index = text_mapping.get(i, i)
            if original_index < len(result):
                result[original_index] = translated

        # Fill in empty texts at their original positions
        for i, text in enumerate(texts):
            if not text.strip():
                result[i] = text

        return result

    def _build_system_prompt(
        self,
        target_lang: str,
        source_lang: Optional[str] = None,
        context: Optional[str] = None,
        glossary: Optional[Dict[str, str]] = None,
    ) -> str:
        """Build system prompt for translation"""

        # Language mapping for better prompts
        lang_names = {
            "vi": "Vietnamese",
            "en": "English",
            "zh": "Chinese",
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
        }

        target_lang_name = lang_names.get(target_lang, target_lang)
        source_lang_name = (
            lang_names.get(source_lang, source_lang)
            if source_lang
            else "the source language"
        )

        prompt = f"""You are a professional translator. Translate the following text from {source_lang_name} to {target_lang_name}.

Requirements:
- Maintain the original formatting and structure exactly
- Keep technical terms accurate and appropriate
- Preserve the tone, style, and meaning
- Do not add explanations or additional content
- Return only the translated text
- If text contains code, URLs, or special formatting, preserve them exactly
- Pay special attention to glossary terms marked with __GLOSSARY_TERM_X__ patterns - these should be translated according to the provided glossary"""

        if context:
            prompt += f"\n\nContext for translation: {context}"

        if glossary:
            prompt += f"\n\nGlossary/Dictionary (use these specific translations when the terms appear):"
            for source_term, target_term in glossary.items():
                prompt += f"\n- {source_term} → {target_term}"

        return prompt

    def _build_batch_system_prompt(
        self,
        target_lang: str,
        source_lang: Optional[str] = None,
        context: Optional[str] = None,
        glossary: Optional[Dict[str, str]] = None,
    ) -> str:
        """Build system prompt for batch translation"""

        # Language mapping for better prompts
        lang_names = {
            "vi": "Vietnamese",
            "en": "English",
            "zh": "Chinese",
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
        }

        target_lang_name = lang_names.get(target_lang, target_lang)
        source_lang_name = (
            lang_names.get(source_lang, source_lang)
            if source_lang
            else "the source language"
        )

        prompt = f"""You are a professional translator. Translate the following numbered text segments from {source_lang_name} to {target_lang_name}.

Requirements:
- Translate each numbered item and return them in the EXACT same numbered format
- Maintain consistency in terminology and style across all translations
- Preserve the original formatting and structure of each segment
- Keep technical terms accurate and appropriate
- Preserve the tone, style, and meaning
- Do not add explanations or additional content
- If text contains code, URLs, or special formatting, preserve them exactly
- Pay special attention to glossary terms marked with __GLOSSARY_TERM_X__ patterns
- Use the document context to ensure consistent translation of repeated terms and concepts

Format your response as:
1. [First translation]
2. [Second translation]
3. [Third translation]
... and so on"""

        if context:
            prompt += f"\n\nContext for translation: {context}"

        if glossary:
            prompt += f"\n\nGlossary/Dictionary (use these specific translations when the terms appear):"
            for source_term, target_term in glossary.items():
                prompt += f"\n- {source_term} → {target_term}"

        return prompt

    def _parse_numbered_response(self, response: str, expected_count: int) -> List[str]:
        """Parse numbered response from the model"""
        import re

        # Split by numbered items
        lines = response.strip().split("\n")
        translations = []
        current_translation = ""

        for line in lines:
            # Check if line starts with a number
            match = re.match(r"^\d+\.\s*(.*)$", line.strip())
            if match:
                # Save previous translation if exists
                if current_translation.strip():
                    translations.append(current_translation.strip())
                # Start new translation
                current_translation = match.group(1)
            else:
                # Continue current translation
                if current_translation or line.strip():
                    current_translation += "\n" + line if current_translation else line

        # Add the last translation
        if current_translation.strip():
            translations.append(current_translation.strip())

        # Ensure we have the expected number of translations
        while len(translations) < expected_count:
            translations.append("")

        return translations[:expected_count]

    def _preprocess_with_glossary(
        self, text: str, glossary: Dict[str, str]
    ) -> tuple[str, Dict[str, str]]:
        """
        Preprocess text by marking glossary terms for consistent translation

        Args:
            text: Original text
            glossary: Dictionary of terms to translate

        Returns:
            Tuple of (preprocessed_text, glossary_markers)
        """
        import re

        preprocessed_text = text
        glossary_markers = {}

        # Sort glossary by length (longest first) to avoid partial replacements
        sorted_terms = sorted(glossary.keys(), key=len, reverse=True)

        for i, term in enumerate(sorted_terms):
            if term in preprocessed_text:
                # Create unique marker for this term
                marker = f"__GLOSSARY_TERM_{i}__"
                glossary_markers[marker] = {
                    "original_term": term,
                    "target_term": glossary[term],
                }

                # Replace term with marker (case-sensitive)
                preprocessed_text = preprocessed_text.replace(term, marker)

                # Also handle different cases
                if term.lower() in preprocessed_text.lower():
                    # Handle lowercase
                    marker_lower = f"__GLOSSARY_TERM_{i}_LOWER__"
                    glossary_markers[marker_lower] = {
                        "original_term": term.lower(),
                        "target_term": glossary[term].lower(),
                    }
                    preprocessed_text = re.sub(
                        re.escape(term.lower()),
                        marker_lower,
                        preprocessed_text,
                        flags=re.IGNORECASE,
                    )

                # Handle uppercase
                if term.upper() in preprocessed_text:
                    marker_upper = f"__GLOSSARY_TERM_{i}_UPPER__"
                    glossary_markers[marker_upper] = {
                        "original_term": term.upper(),
                        "target_term": glossary[term].upper(),
                    }
                    preprocessed_text = preprocessed_text.replace(
                        term.upper(), marker_upper
                    )

                # Handle capitalized
                if term.capitalize() in preprocessed_text:
                    marker_cap = f"__GLOSSARY_TERM_{i}_CAP__"
                    glossary_markers[marker_cap] = {
                        "original_term": term.capitalize(),
                        "target_term": glossary[term].capitalize(),
                    }
                    preprocessed_text = preprocessed_text.replace(
                        term.capitalize(), marker_cap
                    )

        return preprocessed_text, glossary_markers

    def _postprocess_with_glossary(
        self,
        translated_text: str,
        glossary_markers: Dict[str, str],
        glossary: Dict[str, str],
    ) -> str:
        """
        Postprocess translated text by replacing markers with glossary translations

        Args:
            translated_text: Translated text with markers
            glossary_markers: Dictionary of markers and their corresponding terms
            glossary: Original glossary dictionary

        Returns:
            Final translated text with glossary terms properly replaced
        """
        result = translated_text

        # Replace markers with target terms
        for marker, term_info in glossary_markers.items():
            if marker in result:
                result = result.replace(marker, term_info["target_term"])

        # Final pass: apply glossary dictionary for any remaining terms
        result = self._apply_custom_dictionary(result, glossary)

        return result

    def _apply_custom_dictionary(self, text: str, custom_dict: Dict[str, str]) -> str:
        """Apply custom dictionary replacements to translated text"""
        if not custom_dict:
            return text

        for source_term, target_term in custom_dict.items():
            # Case-sensitive replacement first
            text = text.replace(source_term, target_term)
            # Then case-insensitive variants
            text = text.replace(source_term.lower(), target_term.lower())
            text = text.replace(source_term.upper(), target_term.upper())
            text = text.replace(source_term.capitalize(), target_term.capitalize())

        return text

    @classmethod
    def from_env(cls, model: str = "gpt-4-turbo-preview", temperature: float = 0.1):
        """
        Create OpenAITranslator instance from environment variables

        Args:
            model: OpenAI model to use
            temperature: Model temperature

        Returns:
            OpenAITranslator instance

        Raises:
            ValueError: If OPENAI_API_KEY environment variable is not set
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        return cls(api_key=api_key, model=model, temperature=temperature)

    def load_glossary_from_file(self, file_path: str) -> Dict[str, str]:
        """
        Load glossary from various file formats

        Args:
            file_path: Path to glossary file (supports .json, .csv, .txt)

        Returns:
            Dictionary with source->target term mappings
        """
        import csv
        import json
        from pathlib import Path

        path = Path(file_path)
        glossary = {}

        if not path.exists():
            raise FileNotFoundError(f"Glossary file not found: {file_path}")

        if path.suffix.lower() == ".json":
            with open(path, "r", encoding="utf-8") as f:
                glossary = json.load(f)

        elif path.suffix.lower() == ".csv":
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        glossary[row[0].strip()] = row[1].strip()

        elif path.suffix.lower() == ".txt":
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and "→" in line:
                        parts = line.split("→")
                        if len(parts) == 2:
                            glossary[parts[0].strip()] = parts[1].strip()
                    elif line and "=" in line:
                        parts = line.split("=")
                        if len(parts) == 2:
                            glossary[parts[0].strip()] = parts[1].strip()
                    elif line and ":" in line:
                        parts = line.split(":")
                        if len(parts) == 2:
                            glossary[parts[0].strip()] = parts[1].strip()
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

        return glossary

    def save_glossary_to_file(self, glossary: Dict[str, str], file_path: str) -> None:
        """
        Save glossary to file

        Args:
            glossary: Dictionary with source->target term mappings
            file_path: Path to save glossary (supports .json, .csv, .txt)
        """
        import csv
        import json
        from pathlib import Path

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.suffix.lower() == ".json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump(glossary, f, ensure_ascii=False, indent=2)

        elif path.suffix.lower() == ".csv":
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Source", "Target"])
                for source, target in glossary.items():
                    writer.writerow([source, target])

        elif path.suffix.lower() == ".txt":
            with open(path, "w", encoding="utf-8") as f:
                for source, target in glossary.items():
                    f.write(f"{source} → {target}\n")
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

    def create_glossary_from_texts(
        self,
        source_texts: List[str],
        target_texts: List[str],
        extract_terms: bool = True,
    ) -> Dict[str, str]:
        """
        Create glossary by analyzing parallel texts

        Args:
            source_texts: List of source language texts
            target_texts: List of target language texts (parallel to source_texts)
            extract_terms: Whether to extract technical terms automatically

        Returns:
            Generated glossary dictionary
        """
        if len(source_texts) != len(target_texts):
            raise ValueError("Source and target texts must have the same length")

        glossary = {}

        # Simple term extraction (can be enhanced with NLP libraries)
        if extract_terms:
            import re

            # Extract potential technical terms (capitalized words, acronyms, etc.)
            for source_text, target_text in zip(source_texts, target_texts):
                # Find capitalized words and acronyms in source
                source_terms = re.findall(
                    r"\b[A-Z][A-Za-z]*\b|\b[A-Z]{2,}\b", source_text
                )
                target_terms = re.findall(
                    r"\b[A-Z][A-Za-z]*\b|\b[A-Z]{2,}\b", target_text
                )

                # Simple alignment (this is a basic approach)
                for term in source_terms:
                    if term in source_text and term not in glossary:
                        # Try to find corresponding term in target
                        # This is a simplified approach - real implementation would use alignment algorithms
                        for target_term in target_terms:
                            if len(target_term) > 2:  # Avoid very short terms
                                glossary[term] = target_term
                                break

        return glossary
