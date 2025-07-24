from typing import List
import hashlib
import json
import os
import time
import asyncio
from functools import lru_cache, wraps
from pathlib import Path

from .base import BaseTranslator
from googletrans import Translator


class GoogleTranslator(BaseTranslator):
    def __init__(self, cache_size: int = 1000, cache_ttl: int = 3600):
        self.translator = Translator()
        self.cache_size = cache_size
        self.cache_ttl = cache_ttl
    
    def translate_text(self, text):
        return asyncio.run(self.translator.translate(text, dest='vi').text)

    def translate_texts(self, texts: List[str]) -> List[str]:
        """
        Translate multiple texts efficiently with caching
        """
        # Use asyncio to handle multiple translations concurrently
        async def translate_all():
            tasks = [self.translator.translate(text, dest='vi') for text in texts]
            return await asyncio.gather(*tasks)
        
        results = asyncio.run(translate_all())
        return [result.text for result in results]
    
    
