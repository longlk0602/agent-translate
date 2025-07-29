"""
Configuration management for the translation agent
"""

import json
import logging
import os
from typing import List


class TranslationConfig:
    """Configuration class for the translation agent"""

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.azure_api_key = os.getenv("AZURE_TRANSLATOR_KEY")
        self.azure_region = os.getenv("AZURE_TRANSLATOR_REGION", "global")
        self.azure_endpoint = os.getenv("AZURE_TRANSLATOR_ENDPOINT")
        self.default_target_language = "vi"
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.supported_formats = [".pdf", ".docx", ".pptx", ".xlsx", ".txt"]
        self.enable_caching = True
        self.cache_dir = "translation_cache"
        self.log_level = logging.INFO

    @classmethod
    def from_file(cls, config_path: str):
        """Load configuration from file"""

        config = cls()

        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

                for key, value in config_data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)

        return config

    def save_to_file(self, config_path: str):
        """Save configuration to file"""

        config_data = {
            "default_target_language": self.default_target_language,
            "max_file_size": self.max_file_size,
            "supported_formats": self.supported_formats,
            "enable_caching": self.enable_caching,
            "cache_dir": self.cache_dir,
            "log_level": self.log_level,
        }

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)


def create_sample_dictionary():
    """Create a sample custom dictionary"""

    sample_dict = {
        "artificial intelligence": "trí tuệ nhân tạo",
        "machine learning": "học máy",
        "deep learning": "học sâu",
        "neural network": "mạng nơ-ron",
        "natural language processing": "xử lý ngôn ngữ tự nhiên",
        "computer vision": "thị giác máy tính",
        "algorithm": "thuật toán",
        "data science": "khoa học dữ liệu",
        "big data": "dữ liệu lớn",
        "cloud computing": "điện toán đám mây",
    }

    with open("ai_dictionary.json", "w", encoding="utf-8") as f:
        json.dump(sample_dict, f, ensure_ascii=False, indent=2)

    print("Sample dictionary created: ai_dictionary.json")
