# Simple usage example

import asyncio
from translation_agent import TranslationAPI

async def main():
    """Simple example of using the Translation Agent"""
    
    # Initialize the API
    api = TranslationAPI()
    
    print("Translation Agent - Simple Example")
    print("=" * 40)
    
    # Get supported features
    print(f"Supported languages: {api.get_supported_languages()}")
    print(f"Supported file types: {api.get_supported_file_types()}")
    
    # Example translation (requires actual file)
    # result = await api.translate_file(
    #     file_path="sample.txt",
    #     target_language="vi",
    #     source_language="en"
    # )
    # print(f"Translation result: {result}")
    
    # Example chatbot interaction
    chat_result = await api.chat_about_translation("Hello, how can I change translations?")
    print(f"Chatbot response: {chat_result}")

if __name__ == "__main__":
    asyncio.run(main())
