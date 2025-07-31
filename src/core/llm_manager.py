"""
LLM Manager for handling multiple LLM providers
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import openai

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def chat_completion(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Generate chat completion with optional tool calling"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider"""
    
    def __init__(self, api_key: str, model: str = "gpt-4.1-mini"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def chat_completion(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Generate chat completion with OpenAI"""
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 1000
            }
            
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            
            response = await self.client.chat.completions.create(**kwargs)
            
            return {
                "success": True,
                "message": response.choices[0].message,
                "usage": response.usage.dict() if response.usage else None
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI provider"""

    def __init__(self, api_key: str, endpoint: str, model: str = "gpt-4o-mini", **kwargs):
        super().__init__(model, **kwargs)
        self.api_key = api_key
        self.endpoint = endpoint
        
        self.client = openai.AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version="2024-02-01"
        )


class LLMManager:
    """Manager for different LLM providers"""
    
    def __init__(self):
        self.providers = {}
    
    def add_provider(self, name: str, provider: LLMProvider):
        """Add LLM provider"""
        self.providers[name] = provider
    
    async def chat_completion(self, provider_name: str, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Generate chat completion using specified provider"""
        if provider_name not in self.providers:
            return {
                "success": False,
                "error": f"Provider {provider_name} not found"
            }
        print(f"Using provider: {self.providers[provider_name].model}")
        return await self.providers[provider_name].chat_completion(messages, tools)
    
    @classmethod
    def create_from_config(cls, config: Dict[str, Any]) -> 'LLMManager':
        """Create LLM manager from configuration"""
        manager = cls()
        
        # OpenAI provider

        if "openai" in config:
            openai_config = config["openai"]
            provider = OpenAIProvider(
                api_key=openai_config["api_key"],
                model=openai_config.get("model", "gpt-4o-mini")
            )
            manager.add_provider("openai", provider)
        
        # Azure OpenAI provider
        if "azure_openai" in config:
            azure_config = config["azure_openai"]
            provider = AzureOpenAIProvider(
                api_key=azure_config["api_key"],
                endpoint=azure_config["endpoint"],
                api_version=azure_config.get("api_version", "2024-02-15-preview"),
                model=azure_config.get("model", "gpt-4o-mini")
            )
            manager.add_provider("azure_openai", provider)
        
        return manager
