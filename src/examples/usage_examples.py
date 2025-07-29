"""
Usage examples for the Translation Agent
"""

import asyncio

from src import TranslationAPI, TranslationConfig
from src.utils import create_sample_dictionary, setup_logging


async def basic_translation_example():
    """Example of basic document translation"""

    print("=== Basic Translation Example ===")

    # Initialize API (you would need to provide your API keys)
    api = TranslationAPI(
        openai_api_key="your_openai_api_key", anthropic_api_key="your_anthropic_api_key"
    )

    # Translate a document
    result = await api.translate_file(
        file_path="document.docx",
        target_language="vi",
        source_language="en",
        custom_dictionary_path="custom_dict.json",
    )

    print(f"Translation result: {result}")


async def chatbot_example():
    """Example of using the chatbot interface"""

    print("\n=== Chatbot Example ===")

    api = TranslationAPI()

    # Chat about translations
    chat_result = await api.chat_about_translation(
        "Thay 'artificial intelligence' thành 'trí tuệ nhân tạo'"
    )
    print(f"Chat response: {chat_result}")

    # Apply changes
    apply_result = await api.chat_about_translation("Áp dụng thay đổi")
    print(f"Apply result: {apply_result}")


def configuration_example():
    """Example of configuration management"""

    print("\n=== Configuration Example ===")

    # Create configuration
    config = TranslationConfig()
    config.default_target_language = "vi"
    config.max_file_size = 100 * 1024 * 1024  # 100MB

    # Save configuration
    config.save_to_file("translation_config.json")

    # Load configuration
    loaded_config = TranslationConfig.from_file("translation_config.json")
    print(f"Loaded config: {loaded_config.default_target_language}")


def utilities_example():
    """Example of utility functions"""

    print("\n=== Utilities Example ===")

    # Setup logging
    logger = setup_logging()
    logger.info("Translation agent started")

    # Create sample dictionary
    create_sample_dictionary()

    # Get supported features
    api = TranslationAPI()
    print(f"Supported languages: {api.get_supported_languages()}")
    print(f"Supported file types: {api.get_supported_file_types()}")


async def advanced_example():
    """Advanced example with monitoring and error handling"""

    print("\n=== Advanced Example ===")

    from src import TranslationAgent
    from src.utils import TranslationMonitor

    # Create agent
    agent = TranslationAgent()

    # Create monitor
    monitor = TranslationMonitor(agent)

    # Check health
    health = await monitor.health_check()
    print(f"Health check: {health}")

    # Get metrics
    metrics = monitor.get_metrics()
    print(f"Metrics: {metrics}")


async def main():
    """Main example function"""

    print("Translation Agent Examples")
    print("=" * 50)

    # Run examples
    await basic_translation_example()
    await chatbot_example()
    configuration_example()
    utilities_example()
    await advanced_example()


if __name__ == "__main__":
    asyncio.run(main())
