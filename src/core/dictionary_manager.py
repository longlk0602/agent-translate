"""
Dictionary manager for handling custom dictionaries and reference files
"""

import json
from typing import Any, Dict, List

import pandas as pd

from ..processors.base import DocumentProcessor


class DictionaryManager:
    """Manages custom dictionaries and reference files"""

    def __init__(self):
        self.dictionaries = {}
        self.reference_translations = {}

    def load_dictionary(self, dict_path: str, dict_name: str = "default"):
        """Load custom dictionary from file"""

        if dict_path.endswith(".json"):
            with open(dict_path, "r", encoding="utf-8") as f:
                self.dictionaries[dict_name] = json.load(f)
        elif dict_path.endswith(".csv"):
            df = pd.read_csv(dict_path)
            self.dictionaries[dict_name] = dict(zip(df.iloc[:, 0], df.iloc[:, 1]))
        else:
            raise ValueError("Dictionary must be JSON or CSV format")

    def extract_keywords_from_reference(
        self, reference_files: List[str]
    ) -> Dict[str, str]:
        """Extract translation patterns from reference files"""

        keywords = {}

        for file_path in reference_files:
            # This is a simplified version - in production you'd want more sophisticated
            # bilingual text alignment algorithms
            processor = DocumentProcessor()
            content = processor.extract_text(file_path)

            # Extract potential translation pairs
            # This would need more sophisticated implementation
            text_content = self._extract_all_text(content)
            potential_pairs = self._identify_translation_pairs(text_content)
            keywords.update(potential_pairs)

        return keywords

    def _extract_all_text(self, content: Dict[str, Any]) -> str:
        """Extract all text from document content"""

        text_parts = []

        if "text" in content:
            text_parts.append(content["text"])
        elif "paragraphs" in content:
            for para in content["paragraphs"]:
                text_parts.append(para["text"])
        elif "pages" in content:
            for page in content["pages"]:
                text_parts.append(page["text"])
        elif "slides" in content:
            for slide in content["slides"]:
                for frame in slide["text_frames"]:
                    text_parts.append(frame["text"])

        return "\n".join(text_parts)

    def _identify_translation_pairs(self, text: str) -> Dict[str, str]:
        """Identify potential translation pairs from bilingual text"""

        # This is a simplified implementation
        # In production, you'd use more sophisticated NLP techniques

        lines = text.split("\n")
        pairs = {}

        for i in range(0, len(lines) - 1, 2):
            if i + 1 < len(lines):
                source_line = lines[i].strip()
                target_line = lines[i + 1].strip()

                if source_line and target_line:
                    # Simple heuristic: if lines are roughly similar length
                    # and contain different scripts, they might be translation pairs
                    if (
                        abs(len(source_line) - len(target_line))
                        < max(len(source_line), len(target_line)) * 0.5
                    ):
                        pairs[source_line] = target_line

        return pairs
