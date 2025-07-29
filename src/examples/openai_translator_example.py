"""
Example usage of OpenAITranslator
"""

import os

from src.translate.openai_translator import OpenAITranslator


def main():
    """Example usage of OpenAITranslator"""

    # Initialize translator with API key
    # Option 1: Direct initialization
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        translator = OpenAITranslator(api_key=api_key)
    else:
        print("Please set OPENAI_API_KEY environment variable")
        return

    # Option 2: Using from_env class method
    # translator = OpenAITranslator.from_env()

    # Example 1: Basic text translation
    print("=== Basic Translation ===")
    text = "Hello, how are you doing today?"
    translated = translator.translate_text(text, target_lang="vi")
    print(f"Original: {text}")
    print(f"Translated: {translated}")
    print()

    # Example 2: Translation with context
    print("=== Translation with Context ===")
    text = "The server is down"
    context = "This is a technical error message in a software application"
    translated = translator.translate_text(text, target_lang="vi", context=context)
    print(f"Original: {text}")
    print(f"Context: {context}")
    print(f"Translated: {translated}")
    print()

    # Example 3: Translation with glossary (new improved feature)
    print("=== Translation with Glossary ===")
    text = "Please contact the administrator for API access and check the database logs"

    # Create glossary for technical terms
    glossary = {
        "administrator": "quản trị viên hệ thống",
        "API": "giao diện lập trình ứng dụng (API)",
        "database": "cơ sở dữ liệu",
        "logs": "nhật ký hệ thống",
    }

    translated = translator.translate_text(text, target_lang="vi", glossary=glossary)
    print(f"Original: {text}")
    print(f"Glossary: {glossary}")
    print(f"Translated: {translated}")
    print()

    # Example 4: Load glossary from file
    print("=== Load Glossary from File ===")

    # Create a sample glossary file
    sample_glossary = {
        "server": "máy chủ",
        "client": "máy khách",
        "network": "mạng",
        "security": "bảo mật",
        "authentication": "xác thực",
    }

    # Save to file (will create the file)
    try:
        translator.save_glossary_to_file(sample_glossary, "sample_glossary.json")
        print("Saved sample glossary to sample_glossary.json")

        # Load from file
        loaded_glossary = translator.load_glossary_from_file("sample_glossary.json")
        print(f"Loaded glossary: {loaded_glossary}")

        # Use loaded glossary for translation
        text = "The server requires client authentication for network security"
        translated = translator.translate_text(
            text, target_lang="vi", glossary=loaded_glossary
        )
        print(f"Translation with loaded glossary: {translated}")
    except Exception as e:
        print(f"Glossary file example failed: {e}")
    print()

    # Example 4: Batch translation with glossary
    print("=== Batch Translation with Glossary ===")
    texts = [
        "Welcome to our application",
        "Please enter your username",
        "Your password is incorrect",
        "Login successful",
        "Server connection failed",
    ]

    # Use glossary for consistent terminology
    app_glossary = {
        "application": "ứng dụng",
        "username": "tên người dùng",
        "password": "mật khẩu",
        "login": "đăng nhập",
        "server": "máy chủ",
    }

    translated_texts = translator.translate_texts(
        texts, target_lang="vi", glossary=app_glossary
    )

    for original, translated in zip(texts, translated_texts):
        print(f"'{original}' → '{translated}'")
    print()

    # Example 5: Different target language with glossary
    print("=== Translation to Different Languages with Glossary ===")
    text = "Good morning, have a nice day!"
    languages = ["vi", "zh", "ja", "ko", "fr"]

    # Create a simple glossary
    greeting_glossary = {
        "Good morning": "Chào buổi sáng",
        "have a nice day": "chúc bạn một ngày tốt lành",
    }

    for lang in languages:
        # Only apply Vietnamese glossary for Vietnamese translation
        current_glossary = greeting_glossary if lang == "vi" else None
        translated = translator.translate_text(
            text, target_lang=lang, glossary=current_glossary
        )
        print(f"{lang}: {translated}")

    # Example 6: Create glossary from parallel texts
    print("\n=== Create Glossary from Parallel Texts ===")
    source_texts = [
        "The API server is running",
        "Database connection established",
        "Authentication successful",
    ]
    target_texts = [
        "Máy chủ API đang chạy",
        "Kết nối cơ sở dữ liệu đã được thiết lập",
        "Xác thực thành công",
    ]

    try:
        auto_glossary = translator.create_glossary_from_texts(
            source_texts, target_texts
        )
        print(f"Auto-generated glossary: {auto_glossary}")
    except Exception as e:
        print(f"Auto-glossary creation failed: {e}")


if __name__ == "__main__":
    main()
