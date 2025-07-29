"""
Translation endpoints
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from api.core.dependencies import get_translation_service
from api.v1.schemas import (
    DocumentInfoResponse,
    DocumentTranslationRequest,
    DocumentTranslationResponse,
    ErrorResponse,
    HealthResponse,
    ModelComparisonRequest,
    ModelComparisonResponse,
    SupportedFormatsResponse,
    TextTranslationRequest,
    TextTranslationResponse,
)
from api.v1.services.translation_service import TranslationService

router = APIRouter(prefix="/translation", tags=["translation"])


@router.post(
    "/text",
    response_model=TextTranslationResponse,
    summary="Translate text or list of texts",
    description="Translate a single text or list of texts with context-aware translation",
)
async def translate_text(
    request: TextTranslationRequest,
    service: TranslationService = Depends(get_translation_service),
) -> TextTranslationResponse:
    """Translate text or list of texts"""

    try:
        translated_text = await service.translate_text(
            text=request.text,
            target_lang=request.target_lang.value,
            source_lang=request.source_lang.value if request.source_lang else None,
            model_provider=request.model_provider.value,
            model_name=request.model_name,
            temperature=request.temperature,
            context=request.context,
            glossary=request.glossary,
            use_context_aware=request.use_context_aware,
            batch_size=request.batch_size,
        )

        return TextTranslationResponse(
            success=True,
            translated_text=translated_text,
            source_lang=request.source_lang.value if request.source_lang else "auto",
            target_lang=request.target_lang.value,
            model_used=f"{request.model_provider.value}_{request.model_name}",
            text_count=len(request.text) if isinstance(request.text, list) else 1,
            processing_time=0.0,  # Will be updated by service
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/document/upload",
    response_model=DocumentTranslationResponse,
    summary="Upload and translate document",
    description="Upload a document file and translate it",
)
async def translate_uploaded_document(
    file: UploadFile = File(..., description="Document file to translate"),
    target_lang: str = Form(default="vi", description="Target language"),
    source_lang: Optional[str] = Form(default=None, description="Source language"),
    model_provider: str = Form(default="openai", description="Model provider"),
    model_name: str = Form(default="gpt-4o-mini", description="Model name"),
    temperature: float = Form(default=0.1, description="Model temperature"),
    context: Optional[str] = Form(default=None, description="Translation context"),
    glossary: Optional[str] = Form(default=None, description="Glossary as JSON string"),
    service: TranslationService = Depends(get_translation_service),
) -> DocumentTranslationResponse:
    """Upload and translate document"""

    # Create temporary file
    temp_file = None
    try:
        # Save uploaded file temporarily
        suffix = Path(file.filename).suffix if file.filename else ""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        content = await file.read()
        temp_file.write(content)
        temp_file.close()

        # Parse glossary if provided
        parsed_glossary = None
        if glossary:
            import json

            try:
                parsed_glossary = json.loads(glossary)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400, detail="Invalid glossary JSON format"
                )

        # Translate document
        result = await service.translate_document(
            file_path=temp_file.name,
            target_lang=target_lang,
            source_lang=source_lang,
            model_provider=model_provider,
            model_name=model_name,
            temperature=temperature,
            context=context,
            glossary=parsed_glossary,
        )

        return DocumentTranslationResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


@router.post(
    "/document/path",
    response_model=DocumentTranslationResponse,
    summary="Translate document by file path",
    description="Translate a document by providing its file path",
)
async def translate_document_by_path(
    request: DocumentTranslationRequest,
    file_path: str,
    service: TranslationService = Depends(get_translation_service),
) -> DocumentTranslationResponse:
    """Translate document by file path"""

    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

        result = await service.translate_document(
            file_path=file_path,
            target_lang=request.target_lang.value,
            source_lang=request.source_lang.value if request.source_lang else None,
            model_provider=request.model_provider.value,
            model_name=request.model_name,
            temperature=request.temperature,
            context=request.context,
            glossary=request.glossary,
            output_path=request.output_path,
        )

        return DocumentTranslationResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/compare/upload",
    response_model=ModelComparisonResponse,
    summary="Compare models on uploaded document",
    description="Compare multiple translation models on an uploaded document",
)
async def compare_models_on_upload(
    file: UploadFile = File(..., description="Document file to translate"),
    target_lang: str = Form(default="vi", description="Target language"),
    context: Optional[str] = Form(default=None, description="Translation context"),
    glossary: Optional[str] = Form(default=None, description="Glossary as JSON string"),
    models: Optional[str] = Form(
        default=None, description="Models to compare as JSON string"
    ),
    service: TranslationService = Depends(get_translation_service),
) -> ModelComparisonResponse:
    """Compare multiple models on uploaded document"""

    temp_file = None
    try:
        # Save uploaded file temporarily
        suffix = Path(file.filename).suffix if file.filename else ""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        content = await file.read()
        temp_file.write(content)
        temp_file.close()

        # Parse inputs
        parsed_glossary = None
        if glossary:
            import json

            parsed_glossary = json.loads(glossary)

        parsed_models = None
        if models:
            import json

            parsed_models = json.loads(models)

        # Compare models
        result = await service.compare_models_for_document(
            file_path=temp_file.name,
            target_lang=target_lang,
            models=parsed_models,
            context=context,
            glossary=parsed_glossary,
        )

        return ModelComparisonResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


@router.post(
    "/compare/path",
    response_model=ModelComparisonResponse,
    summary="Compare models on document by path",
    description="Compare multiple translation models on a document by file path",
)
async def compare_models_by_path(
    request: ModelComparisonRequest,
    file_path: str,
    service: TranslationService = Depends(get_translation_service),
) -> ModelComparisonResponse:
    """Compare models on document by file path"""

    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

        # Convert ModelConfig objects to dicts
        models_dict = None
        if request.models:
            models_dict = [
                {
                    "provider": model.provider.value,
                    "model": model.model,
                    "temperature": model.temperature,
                }
                for model in request.models
            ]

        result = await service.compare_models_for_document(
            file_path=file_path,
            target_lang=request.target_lang.value,
            models=models_dict,
            context=request.context,
            glossary=request.glossary,
        )

        return ModelComparisonResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/document/info",
    response_model=DocumentInfoResponse,
    summary="Get document information",
    description="Get information about a document without translating",
)
async def get_document_info(
    file_path: str, service: TranslationService = Depends(get_translation_service)
) -> DocumentInfoResponse:
    """Get document information"""

    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

        result = service.get_document_info(file_path)
        return DocumentInfoResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/formats",
    response_model=SupportedFormatsResponse,
    summary="Get supported formats",
    description="Get list of supported document formats",
)
async def get_supported_formats(
    service: TranslationService = Depends(get_translation_service),
) -> SupportedFormatsResponse:
    """Get supported document formats"""

    try:
        result = service.get_supported_formats()
        return SupportedFormatsResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check API health status",
)
async def health_check() -> HealthResponse:
    """Health check endpoint"""

    return HealthResponse(
        status="healthy", timestamp=datetime.now().isoformat(), version="1.0.0"
    )
