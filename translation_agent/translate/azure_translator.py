import asyncio
from typing import List, Dict, Optional
from azure.ai.translation.text import TextTranslationClient, TranslatorCredential
from azure.ai.translation.text.models import InputTextItem
from azure.core.exceptions import HttpResponseError
from .base import BaseTranslator


class AzureTranslator(BaseTranslator):
    """Azure Translator service implementation using official SDK"""
    
    def __init__(self, api_key: str, region: str = "global", endpoint: str = None):
        """
        Initialize Azure Translator
        
        Args:
            api_key: Azure Translator API key
            region: Azure region (default: "global")
            endpoint: Custom endpoint URL (optional, defaults to global endpoint)
        """
        self.api_key = api_key
        self.region = region
        self.endpoint = endpoint or "https://api.cognitive.microsofttranslator.com"
        self.default_target_lang = "vi"  # Vietnamese as default
        
        # Initialize the client
        credential = TranslatorCredential(api_key, region)
        self.client = TextTranslationClient(endpoint=self.endpoint, credential=credential)
    
    def translate_text(self, text: str, target_lang: str = None, source_lang: str = None) -> str:
        """Translate a single text block"""
        if not text.strip():
            return text
            
        target = target_lang or self.default_target_lang
        
        try:
            # Create input text item
            input_text_elements = [InputTextItem(text=text)]
            
            # Perform translation
            response = self.client.translate(
                content=input_text_elements,
                to=[target],
                from_parameter=source_lang
            )
            
            # Extract translated text
            if response and len(response) > 0 and len(response[0].translations) > 0:
                return response[0].translations[0].text
            else:
                raise Exception("No translation returned from Azure")
                
        except HttpResponseError as e:
            raise Exception(f"Azure Translator API error: {e}")
        except Exception as e:
            raise Exception(f"Translation error: {e}")
    
    def translate_texts(self, texts: List[str], target_lang: str = None, source_lang: str = None) -> List[str]:
        """Translate a list of text blocks"""
        if not texts:
            return []
        
        target = target_lang or self.default_target_lang
        results = []
        
        # Handle empty texts
        for text in texts:
            if not text.strip():
                results.append(text)
                continue
                
            try:
                # Create input text item
                input_text_elements = [InputTextItem(text=text)]
                
                # Perform translation
                response = self.client.translate(
                    content=input_text_elements,
                    to=[target],
                    from_parameter=source_lang
                )
                
                # Extract translated text
                if response and len(response) > 0 and len(response[0].translations) > 0:
                    results.append(response[0].translations[0].text)
                else:
                    results.append(text)  # Fallback to original text
                    
            except HttpResponseError as e:
                print(f"Azure Translator API error for text '{text[:50]}...': {e}")
                results.append(text)  # Fallback to original text
            except Exception as e:
                print(f"Translation error for text '{text[:50]}...': {e}")
                results.append(text)  # Fallback to original text
        
        return results
    
    def translate_texts_batch(self, texts: List[str], target_lang: str = None, source_lang: str = None) -> List[str]:
        """Translate multiple texts in a single batch request (more efficient)"""
        if not texts:
            return []
        
        target = target_lang or self.default_target_lang
        
        # Filter out empty texts but preserve their positions
        text_map = {}
        non_empty_texts = []
        for i, text in enumerate(texts):
            if text.strip():
                text_map[len(non_empty_texts)] = i
                non_empty_texts.append(text)
        
        if not non_empty_texts:
            return texts
        
        try:
            # Create input text items for batch translation
            input_text_elements = [InputTextItem(text=text) for text in non_empty_texts]
            
            # Perform batch translation
            response = self.client.translate(
                content=input_text_elements,
                to=[target],
                from_parameter=source_lang
            )
            
            # Extract translations
            translations = []
            for result in response:
                if len(result.translations) > 0:
                    translations.append(result.translations[0].text)
                else:
                    translations.append("")  # Fallback
            
            # Reconstruct the full results list with empty texts in their original positions
            final_results = [''] * len(texts)
            for i, translated in enumerate(translations):
                original_index = text_map[i]
                final_results[original_index] = translated
            
            # Keep empty texts as they were
            for i, original_text in enumerate(texts):
                if not original_text.strip():
                    final_results[i] = original_text
            
            return final_results
            
        except HttpResponseError as e:
            print(f"Azure Translator batch API error: {e}")
            return texts  # Fallback to original texts
        except Exception as e:
            print(f"Batch translation error: {e}")
            return texts  # Fallback to original texts
    
    def detect_language(self, text: str) -> str:
        """Detect language of the given text"""
        if not text.strip():
            return "unknown"
        
        try:
            # Create input text item
            input_text_elements = [InputTextItem(text=text)]
            
            # Perform language detection
            response = self.client.find_sentence_boundaries(content=input_text_elements)
            
            # Note: The current SDK doesn't have a direct language detection method
            # This is a workaround - in practice, you might want to use the REST API
            # or handle this differently based on your needs
            
            # For now, we'll use a simple heuristic or return 'auto'
            return "auto"
            
        except Exception as e:
            print(f"Language detection error: {e}")
            return "unknown"
    
    def detect_language_sync(self, text: str) -> str:
        """Synchronous version of language detection"""
        return self.detect_language(text)
    
    def get_supported_languages(self) -> Dict:
        """Get list of supported languages from Azure Translator"""
        try:
            # Get supported languages
            response = self.client.get_supported_languages(scope=["translation"])
            
            # Convert to dictionary format similar to REST API
            languages_dict = {"translation": {}}
            
            if hasattr(response, 'translation') and response.translation:
                for lang_code, lang_info in response.translation.items():
                    languages_dict["translation"][lang_code] = {
                        "name": getattr(lang_info, 'name', lang_code),
                        "nativeName": getattr(lang_info, 'native_name', lang_code)
                    }
            
            return languages_dict
            
        except Exception as e:
            print(f"Error getting supported languages: {e}")
            return {"translation": {}}
    
    def get_supported_languages_sync(self) -> Dict:
        """Synchronous version of getting supported languages"""
        return self.get_supported_languages()
    
    def set_default_target_language(self, lang_code: str):
        """Set default target language"""
        self.default_target_lang = lang_code
    
    def get_stats(self) -> Dict:
        """Get translation statistics"""
        return {
            "service": "Azure Translator",
            "api_endpoint": self.endpoint,
            "region": self.region,
            "default_target_lang": self.default_target_lang,
            "sdk_version": "azure-ai-translation-text"
        }
