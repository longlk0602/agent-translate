"""
FastAPI router for Translation API
"""

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from .models import (
    ErrorResponse,
    HealthResponse,
    LanguagesResponse,
    ModelInfo,
    ModelsResponse,
    MultiModelRequest,
    MultiModelResponse,
    TranslationRequest,
    TranslationResponse,
)
from .translation_api import TranslationAPI

# Create router
router = APIRouter(prefix="/api/v1", tags=["translation"])

# Global API instance (will be initialized in main.py)
translation_api: Optional[TranslationAPI] = None


def get_translation_api() -> TranslationAPI:
    """Dependency to get translation API instance"""
    if translation_api is None:
        raise HTTPException(
            status_code=500,
            detail="Translation API not initialized. Please check server configuration.",
        )
    return translation_api


@router.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check():
    """
    Health check endpoint to verify service status
    """
    try:
        api = get_translation_api()

        return HealthResponse(
            status="healthy",
            version="1.0.0",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            available_models={
                provider: list(models.keys())
                for provider, models in api.get_available_models().items()
            },
            supported_languages=list(api.get_supported_languages().keys()),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service unhealthy: {str(e)}")


@router.get("/models", response_model=ModelsResponse, summary="Get Available Models")
async def get_models(api: TranslationAPI = Depends(get_translation_api)):
    """
    Get list of available translation models
    """
    try:
        models_data = api.get_available_models()

        # Convert to response format
        formatted_models = {}
        for provider, models in models_data.items():
            formatted_models[provider] = {}
            for model_id, model_info in models.items():
                formatted_models[provider][model_id] = ModelInfo(
                    name=model_info["name"],
                    description=model_info["description"],
                    provider=provider,
                )

        return ModelsResponse(success=True, models=formatted_models)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/languages", response_model=LanguagesResponse, summary="Get Supported Languages"
)
async def get_languages(api: TranslationAPI = Depends(get_translation_api)):
    """
    Get list of supported languages
    """
    try:
        languages = api.get_supported_languages()
        return LanguagesResponse(success=True, languages=languages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translate", response_model=TranslationResponse, summary="Translate Text")
async def translate_text(
    request: TranslationRequest, api: TranslationAPI = Depends(get_translation_api)
):
    """
    Translate text or list of texts

    - **text**: Single text string or list of texts to translate
    - **target_lang**: Target language code (default: vi)
    - **source_lang**: Source language code (optional, auto-detect if not provided)
    - **model_provider**: Model provider (openai or azure)
    - **model_name**: Specific model name
    - **temperature**: Model temperature for creativity control (0.0-1.0)
    - **context**: Additional context for better translation
    - **glossary**: Custom dictionary for specific terms
    - **use_context_aware**: Use context-aware translation for lists
    - **batch_size**: Batch size for processing large lists
    """
    start_time = time.time()

    try:
        # Count words for statistics
        if isinstance(request.text, str):
            word_count = len(request.text.split())
        else:
            word_count = sum(len(text.split()) for text in request.text)

        # Perform translation
        result = api.translate_text(
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

        processing_time = time.time() - start_time

        return TranslationResponse(
            success=True,
            result=result,
            source_lang=request.source_lang.value if request.source_lang else "auto",
            target_lang=request.target_lang.value,
            model_used=f"{request.model_provider.value}_{request.model_name}",
            processing_time=round(processing_time, 2),
            word_count=word_count,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@router.post(
    "/translate/compare",
    response_model=MultiModelResponse,
    summary="Compare Multiple Models",
)
async def compare_models(
    request: MultiModelRequest, api: TranslationAPI = Depends(get_translation_api)
):
    """
    Compare translation results from multiple models

    - **text**: Text to translate
    - **target_lang**: Target language code
    - **models**: List of model configurations to compare
    - **context**: Additional context for translation
    - **glossary**: Custom dictionary for specific terms
    """
    start_time = time.time()

    try:
        results = api.translate_with_multiple_models(
            text=request.text,
            target_lang=request.target_lang.value,
            models=request.models,
            context=request.context,
            glossary=request.glossary,
        )

        processing_time = time.time() - start_time
        models_used = list(results.keys())

        return MultiModelResponse(
            success=True,
            results=results,
            target_lang=request.target_lang.value,
            processing_time=round(processing_time, 2),
            models_used=models_used,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Model comparison failed: {str(e)}"
        )


@router.post("/translate/file", summary="Translate File")
async def translate_file(
    file: UploadFile = File(..., description="File to translate"),
    target_lang: str = "vi",
    source_lang: Optional[str] = None,
    model_provider: str = "openai",
    model_name: str = "gpt-4o-mini",
    context: Optional[str] = None,
    api: TranslationAPI = Depends(get_translation_api),
):
    """
    Translate content from uploaded file

    Supports text files (.txt), JSON files (.json), and CSV files (.csv)
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in [".txt", ".json", ".csv"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Supported: .txt, .json, .csv",
        )

    try:
        # Read file content
        content = await file.read()
        text_content = content.decode("utf-8")

        # Parse content based on file type
        if file_ext == ".txt":
            # Split by lines for text files
            texts = [line.strip() for line in text_content.split("\n") if line.strip()]
        elif file_ext == ".json":
            # Assume JSON array of strings or object with text fields
            data = json.loads(text_content)
            if isinstance(data, list):
                texts = [str(item) for item in data if str(item).strip()]
            elif isinstance(data, dict):
                texts = [str(value) for value in data.values() if str(value).strip()]
            else:
                texts = [str(data)]
        elif file_ext == ".csv":
            # Simple CSV parsing - treat each line as text
            import csv
            import io

            csv_reader = csv.reader(io.StringIO(text_content))
            texts = []
            for row in csv_reader:
                if row:  # Skip empty rows
                    texts.extend([cell.strip() for cell in row if cell.strip()])

        if not texts:
            raise HTTPException(
                status_code=400, detail="No translatable content found in file"
            )

        # Translate using context-aware mode
        result = api.translate_text(
            text=texts,
            target_lang=target_lang,
            source_lang=source_lang,
            model_provider=model_provider,
            model_name=model_name,
            context=context or f"Content from {file.filename}",
            use_context_aware=True,
        )

        return {
            "success": True,
            "filename": file.filename,
            "source_lang": source_lang or "auto",
            "target_lang": target_lang,
            "model_used": f"{model_provider}_{model_name}",
            "original_count": len(texts),
            "translated_count": len(result),
            "original_texts": texts,
            "translated_texts": result,
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file format")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Unable to decode file. Please ensure UTF-8 encoding.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"File translation failed: {str(e)}"
        )


@router.post("/translate/glossary", summary="Translate with Glossary File")
async def translate_with_glossary_file(
    text: str,
    glossary_file: UploadFile = File(
        ..., description="Glossary file (.json, .csv, .txt)"
    ),
    target_lang: str = "vi",
    source_lang: Optional[str] = None,
    model_provider: str = "openai",
    model_name: str = "gpt-4o-mini",
    context: Optional[str] = None,
    api: TranslationAPI = Depends(get_translation_api),
):
    """
    Translate text using glossary from uploaded file
    """
    if not glossary_file.filename:
        raise HTTPException(status_code=400, detail="No glossary file uploaded")

    # Check file extension
    file_ext = Path(glossary_file.filename).suffix.lower()
    if file_ext not in [".json", ".csv", ".txt"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported glossary file type: {file_ext}. Supported: .json, .csv, .txt",
        )

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=file_ext, delete=False
        ) as temp_file:
            content = await glossary_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Translate with glossary file
            result = api.translate_text(
                text=text,
                target_lang=target_lang,
                source_lang=source_lang,
                model_provider=model_provider,
                model_name=model_name,
                context=context,
                glossary_file=temp_file_path,
            )

            return {
                "success": True,
                "original_text": text,
                "translated_text": result,
                "glossary_file": glossary_file.filename,
                "source_lang": source_lang or "auto",
                "target_lang": target_lang,
                "model_used": f"{model_provider}_{model_name}",
            }

        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)

    except Exception as e:
        # Clean up in case of error
        if "temp_file_path" in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass
        raise HTTPException(
            status_code=500, detail=f"Translation with glossary failed: {str(e)}"
        )


@router.get("/translate/download/{result_id}", summary="Download Translation Result")
async def download_result(result_id: str, format: str = "json"):
    """
    Download translation result in specified format

    Note: This is a placeholder endpoint. In production, you would store
    translation results with unique IDs and allow users to download them.
    """
    # This would typically fetch stored results from database/cache
    # For demo purposes, return a sample response

    sample_result = {
        "translation_id": result_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "result": "Sample translated content",
        "metadata": {
            "source_lang": "en",
            "target_lang": "vi",
            "model_used": "gpt-4o-mini",
        },
    }

    if format.lower() == "json":
        return JSONResponse(content=sample_result)
    elif format.lower() == "txt":
        # Return as plain text
        from fastapi.responses import PlainTextResponse

        return PlainTextResponse(content=sample_result["result"])
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")


# Note: Exception handlers are registered in main.py, not in router
