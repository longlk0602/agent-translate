"""
Session-based translation endpoints
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from api.core.dependencies import get_translation_service
from api.v1.services.session_based_translation_service import EnhancedTranslationService
from api.v1.schemas.session_schemas import (
    SessionCreateRequest,
    SessionResponse,
    ChatRequest,
    ChatResponse,
    DownloadRequest,
    DownloadResponse,
    SessionListResponse,
    SessionDeleteResponse,
)

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["translation-sessions"])


@router.post(
    "/upload",
    response_model=SessionResponse,
    summary="Upload file and create translation session",
    description="Upload a document file, extract content, translate, and create a session for further editing",
)
async def create_session_from_upload(
    file: UploadFile = File(..., description="Document file to translate"),
    target_lang: str = Form(default="vi", description="Target language"),
    source_lang: str = Form(default="en", description="Source language"),
    model_provider: str = Form(default="openai", description="Model provider"),
    model_name: str = Form(default="gpt-4o-mini", description="Model name"),
    temperature: float = Form(default=0.1, description="Model temperature"),
    context: str = Form(default=None, description="Translation context"),
    service: EnhancedTranslationService = Depends(get_translation_service),
) -> SessionResponse:
    """Create translation session from uploaded file"""
    # Save uploaded file to data/uploads
    try:
        suffix = Path(file.filename).suffix if file.filename else ""
        uploads_dir = Path("data/uploads")
        uploads_dir.mkdir(parents=True, exist_ok=True)
        # Generate a unique filename
        import uuid
        unique_id = uuid.uuid4().hex
        save_path = uploads_dir / f"{unique_id}{suffix}"
        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        print(f"Uploaded file saved at: {save_path}")
        # Create translation session
        result = await service.create_translation_session(
            file_path=str(save_path),
            target_lang=target_lang,
            source_lang=source_lang,
            model_provider=model_provider,
            model_name=model_name,
            temperature=temperature,
            context=context,
        )

        return SessionResponse(**result)

    except Exception as e:
        return SessionResponse(
            success=False,
            error=str(e)
        )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Get session content",
    description="Get the content of a translation session",
)
async def get_session(
    session_id: str,
    service: EnhancedTranslationService = Depends(get_translation_service),
) -> SessionResponse:
    """Get session content"""

    try:
        result = service.get_session_content(session_id)
        return SessionResponse(**result)
    except Exception as e:
        return SessionResponse(
            success=False,
            error=str(e)
        )


@router.post(
    "/{session_id}/chat",
    response_model=ChatResponse,
    summary="Chat about translation",
    description="Chat with the AI agent about the translation content",
)
async def chat_with_session(
    session_id: str,
    request: ChatRequest,
    service: EnhancedTranslationService = Depends(get_translation_service),
) -> ChatResponse:
    """Chat about translation in session"""

    logger.info(f"Starting chat session: {session_id}")
    logger.info(f"User message: {request.message[:100]}...")  # Log first 100 chars

    try:
        logger.info(f"Processing chat message for session {session_id}")
        result = await service.chat_with_session(session_id, request.message)
        
        # Log the result details
        logger.info(f"Chat result for session {session_id}: success={result.get('success')}, "
                   f"content_updated={result.get('content_updated')}, "
                   f"pending_changes={result.get('pending_changes', 0)}")
        
        if result.get('content_updated'):
            logger.info(f"Content was updated in session {session_id}")
        
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Error in chat session {session_id}: {str(e)}")
        return ChatResponse(
            success=False,
            error=str(e),
            session_id=session_id
        )


@router.post(
    "/{session_id}/download",
    response_model=DownloadResponse,
    summary="Finalize and prepare download",
    description="Finalize the translation session and prepare the document for download",
)
async def prepare_download(
    session_id: str,
    request: DownloadRequest = DownloadRequest(),
    service: EnhancedTranslationService = Depends(get_translation_service),
) -> DownloadResponse:
    """Finalize session and prepare download"""

    try:
        result = await service.finalize_and_download_session(
            session_id, request.output_path
        )
        return DownloadResponse(**result)
    except Exception as e:
        return DownloadResponse(
            success=False,
            error=str(e),
            session_id=session_id
        )


@router.get(
    "/{session_id}/download-file",
    summary="Download translated file",
    description="Download the finalized translated document",
)
async def download_file(
    session_id: str,
    service: EnhancedTranslationService = Depends(get_translation_service),
):
    """Download the translated file"""

    try:
        # Get session to find the output file
        session_result = service.get_session_content(session_id)
        
        if not session_result["success"]:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if not session_result["is_finalized"]:
            raise HTTPException(status_code=400, detail="Session not finalized. Call prepare_download first.")
        
        # In a real implementation, you would store the output file path in the session
        # For now, we'll reconstruct it based on the session
        session = service.session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Generate expected output path
        file_path = Path(session.file_path)
        output_path = file_path.parent / f"{file_path.stem}_{session.target_lang}{file_path.suffix}"
        
        if not output_path.exists():
            # Try to finalize if not done yet
            download_result = await service.finalize_and_download_session(session_id)
            if not download_result["success"]:
                raise HTTPException(status_code=500, detail=f"Could not create download file: {download_result['error']}")
            output_path = Path(download_result["output_file"])
        
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Translated file not found")
        
        return FileResponse(
            path=str(output_path),
            filename=output_path.name,
            media_type='application/octet-stream'
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "",
    response_model=SessionListResponse,
    summary="List all sessions",
    description="Get a list of all translation sessions",
)
async def list_sessions(
    service: EnhancedTranslationService = Depends(get_translation_service),
) -> SessionListResponse:
    """List all translation sessions"""

    try:
        result = service.list_sessions()
        return SessionListResponse(**result)
    except Exception as e:
        return SessionListResponse(
            success=False,
            error=str(e)
        )


@router.delete(
    "/{session_id}",
    response_model=SessionDeleteResponse,
    summary="Delete session",
    description="Delete a translation session",
)
async def delete_session(
    session_id: str,
    service: EnhancedTranslationService = Depends(get_translation_service),
) -> SessionDeleteResponse:
    """Delete a translation session"""

    try:
        result = service.delete_session(session_id)
        return SessionDeleteResponse(**result)
    except Exception as e:
        return SessionDeleteResponse(
            success=False,
            error=str(e),
            session_id=session_id
        )
