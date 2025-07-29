"""
Example usage of Azure Translator using azure-ai-translation-text SDK
"""

import os

from src.translate.azure_translator import AzureTranslator


def main():
    """Example usage of Azure Translator"""

    # Get Azure credentials from environment variables
    api_key = os.getenv("AZURE_TRANSLATOR_KEY")
    region = os.getenv("AZURE_TRANSLATOR_REGION", "global")

    if not api_key:
        print("Error: Please set AZURE_TRANSLATOR_KEY environment variable")
        print(
            "You can get this from Azure Portal > Translator resource > Keys and Endpoint"
        )
        return

    # Initialize Azure Translator
    translator = AzureTranslator(api_key=api_key, region=region)

    print("=== Azure Translator Example (Official SDK) ===\n")

    # Example 1: Simple text translation
    print("1. Simple text translation:")
    text = "Hello, how are you today?"
    try:
        translated = translator.translate_text(text, target_lang="vi")
        print(f"   Original (EN): {text}")
        print(f"   Translated (VI): {translated}")
    except Exception as e:
        print(f"   Error: {e}")

    print()

    # Example 2: Multiple texts translation (individual calls)
    print("2. Multiple texts translation (individual):")
    texts = [
        "Good morning!",
        "How's the weather today?",
        "I love programming.",
        "Azure Translator is amazing!",
        "",  # Test empty string
    ]

    try:
        translated_texts = translator.translate_texts(texts, target_lang="vi")
        for i, (orig, trans) in enumerate(zip(texts, translated_texts), 1):
            print(f"   Text {i}:")
            print(f"      Original: '{orig}'")
            print(f"      Translated: '{trans}'")
    except Exception as e:
        print(f"   Error: {e}")

    print()

    # Example 3: Batch translation (more efficient)
    print("3. Batch translation (more efficient):")
    batch_texts = [
        "Artificial Intelligence is transforming the world.",
        "Machine Learning helps computers learn from data.",
        "Deep Learning uses neural networks.",
        "Natural Language Processing understands human language.",
    ]

    try:
        batch_translated = translator.translate_texts_batch(
            batch_texts, target_lang="vi"
        )
        for i, (orig, trans) in enumerate(zip(batch_texts, batch_translated), 1):
            print(f"   Text {i}:")
            print(f"      Original: {orig}")
            print(f"      Translated: {trans}")
    except Exception as e:
        print(f"   Error: {e}")

    print()

    # Example 4: Different target languages
    print("4. Translation to different languages:")
    source_text = "Hello world!"
    target_langs = ["vi", "fr", "de", "es", "ja", "ko"]

    for lang in target_langs:
        try:
            translated = translator.translate_text(source_text, target_lang=lang)
            print(f"   {lang.upper()}: {translated}")
        except Exception as e:
            print(f"   Error translating to {lang}: {e}")

    print()

    # Example 5: Specify source language
    print("5. Translation with specified source language:")
    text_fr = "Bonjour le monde!"
    try:
        translated = translator.translate_text(
            text_fr, target_lang="vi", source_lang="fr"
        )
        print(f"   Original (FR): {text_fr}")
        print(f"   Translated (VI): {translated}")
    except Exception as e:
        print(f"   Error: {e}")

    print()

    # Example 6: Get supported languages
    print("6. Getting supported languages:")
    try:
        languages = translator.get_supported_languages_sync()
        translation_langs = languages.get("translation", {})
        print(f"   Azure supports {len(translation_langs)} languages for translation")
        if translation_langs:
            print("   First 10 languages:")
            for i, (code, info) in enumerate(translation_langs.items()):
                if i >= 10:
                    break
                name = info.get("name", "Unknown")
                print(f"      {code}: {name}")
        else:
            print("   Note: Language list might not be available with this SDK method")
    except Exception as e:
        print(f"   Error getting supported languages: {e}")

    print()

    # Example 7: Translator stats
    print("7. Translator information:")
    stats = translator.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print()

    # Example 8: Set default language
    print("8. Changing default target language:")
    translator.set_default_target_language("fr")
    print(f"   Default language changed to: {translator.default_target_lang}")

    try:
        # Translate without specifying target language (will use default)
        text = "This will be translated to the default language"
        translated = translator.translate_text(text)
        print(f"   Original: {text}")
        print(f"   Translated (to {translator.default_target_lang}): {translated}")
    except Exception as e:
        print(f"   Error: {e}")


if __name__ == "__main__":
    main()
