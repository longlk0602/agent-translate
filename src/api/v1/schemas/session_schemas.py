"""
Session-based translation schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    """Request to create a translation session"""
    target_lang: str = Field(default="vi", description="Target language")
    source_lang: Optional[str] = Field(default=None, description="Source language")
    model_provider: str = Field(default="openai", description="Model provider")
    model_name: str = Field(default="gpt-4o-mini", description="Model name")
    temperature: float = Field(default=0.1, description="Model temperature")
    context: Optional[str] = Field(default=None, description="Translation context")
    glossary: Optional[Dict[str, str]] = Field(default=None, description="Custom glossary")


class SessionResponse(BaseModel):
    """Response for session operations"""
    success: bool
    session_id: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    original_content: Optional[Dict[str, Any]] = None
    translated_content: Optional[Dict[str, Any]] = None
    source_lang: Optional[str] = None
    target_lang: Optional[str] = None
    model_used: Optional[str] = None
    text_count: Optional[int] = None
    translation_count: Optional[int] = None
    processing_time: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_finalized: Optional[bool] = None
    chat_history: Optional[List[Dict[str, str]]] = None
    error: Optional[str] = None


class ChatRequest(BaseModel):
    """Request to chat about translation"""
    message: str = Field(..., description="Chat message")


class ChatResponse(BaseModel):
    """Response from chat"""
    success: bool
    response: Optional[str] = None
    pending_changes: Optional[int] = None
    session_id: Optional[str] = None
    error: Optional[str] = None


class DownloadRequest(BaseModel):
    """Request to finalize and download session"""
    output_path: Optional[str] = Field(default=None, description="Output file path")


class DownloadResponse(BaseModel):
    """Response for download operation"""
    success: bool
    session_id: Optional[str] = None
    output_file: Optional[str] = None
    original_file: Optional[str] = None
    file_name: Optional[str] = None
    download_ready: Optional[bool] = None
    error: Optional[str] = None


class SessionListResponse(BaseModel):
    """Response for listing sessions"""
    success: bool
    sessions: Optional[List[Dict[str, Any]]] = None
    total_count: Optional[int] = None
    error: Optional[str] = None


class SessionDeleteResponse(BaseModel):
    """Response for deleting session"""
    success: bool
    session_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
