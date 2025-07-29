"""
Example usage of Azure Translator Engine
"""

import asyncio
import os

from src.engines.azure_engine import AzureEngine
from src.models.enums import SupportedLanguage


async def main():
    """Example usage of Azure Translator"""

    # Initialize Azure Translator
    # You need to set your Azure Translator API key and region
    api_key = os.getenv("AZURE_TRANSLATOR_KEY")  # Set this environment variable
    region = os.getenv(
        "AZURE_TRANSLATOR_REGION", "global"
    )  # Set this environment variable

    if not api_key:
        print("Please set AZURE_TRANSLATOR_KEY environment variable")
        return

    azure_engine = AzureEngine(api_key=api_key, region=region)

    # Example 1: Simple text translation
    print("=== Simple Text Translation ===")
    text = "Hello, how are you today?"
    try:
        translated = await azure_engine.translate_text(
            text=text,
            target_lang=SupportedLanguage.VIETNAMESE,
            source_lang=SupportedLanguage.ENGLISH,
        )
        print(f"Original: {text}")
        print(f"Translated: {translated}")
    except Exception as e:
        print(f"Translation error: {e}")

    # Example 2: Multiple texts translation
    print("\n=== Batch Text Translation ===")
    texts = [
        "Good morning!",
        "How's the weather today?",
        "I love programming.",
        "Azure Translator is amazing!",
    ]

    try:
        translated_texts = await azure_engine.translate_texts(
            texts=texts,
            target_lang=SupportedLanguage.VIETNAMESE,
            source_lang=SupportedLanguage.ENGLISH,
        )

        for orig, trans in zip(texts, translated_texts):
            print(f"Original: {orig}")
            print(f"Translated: {trans}")
            print("---")
    except Exception as e:
        print(f"Batch translation error: {e}")

    # Example 3: Language detection
    print("\n=== Language Detection ===")
    sample_text = "Bonjour, comment allez-vous?"
    try:
        detected_lang = await azure_engine.detect_language(sample_text)
        print(f"Text: {sample_text}")
        print(f"Detected language: {detected_lang}")
    except Exception as e:
        print(f"Language detection error: {e}")

    # Example 4: Custom dictionary usage
    print("\n=== Translation with Custom Dictionary ===")
    text_with_terms = "The API documentation is comprehensive."
    custom_dict = {
        "API": "Giao diện lập trình ứng dụng",
        "documentation": "tài liệu hướng dẫn",
    }

    try:
        translated_with_dict = await azure_engine.translate_text(
            text=text_with_terms,
            target_lang=SupportedLanguage.VIETNAMESE,
            source_lang=SupportedLanguage.ENGLISH,
            custom_dict=custom_dict,
        )
        print(f"Original: {text_with_terms}")
        print(f"Translated with custom dict: {translated_with_dict}")
    except Exception as e:
        print(f"Custom dictionary translation error: {e}")

    # Example 5: Get supported languages
    print("\n=== Supported Languages ===")
    try:
        supported_langs = await azure_engine.get_supported_languages()
        translation_langs = supported_langs.get("translation", {})
        print(f"Azure supports {len(translation_langs)} languages for translation")
        print("First 10 supported languages:")
        for i, (code, info) in enumerate(translation_langs.items()):
            if i >= 10:
                break
            print(f"  {code}: {info.get('name', 'Unknown')}")
    except Exception as e:
        print(f"Getting supported languages error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
