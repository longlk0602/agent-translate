"""
API v1 module
"""

from api.v1.endpoints import translation_router
from api.v1.schemas import *
from api.v1.services.document_service import DocumentProcessingService
from api.v1.services.translation_service import TranslationService

__all__ = ["translation_router", "TranslationService", "DocumentProcessingService"]
