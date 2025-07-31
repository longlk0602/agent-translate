"""
Translation session service for managing user sessions
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict

from core.agent import TranslationAgent
from core.chatbot import TranslationChatbot


@dataclass
class TranslationSession:
    """Translation session data structure"""
    session_id: str
    file_name: str
    file_path: str
    file_type: str
    original_content: Dict[str, Any]
    translated_content: Dict[str, Any]
    source_lang: str
    target_lang: str
    model_provider: str
    model_name: str
    created_at: datetime
    updated_at: datetime
    is_finalized: bool = False
    chat_history: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.chat_history is None:
            self.chat_history = []


class SessionService:
    """Service for managing translation sessions"""
    
    def __init__(self):
        self.active_sessions: Dict[str, TranslationSession] = {}
        self.session_storage_path = Path("data/sessions")
        self.session_storage_path.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def create_session(
        self,
        file_name: str,
        file_path: str,
        file_type: str,
        original_content: Dict[str, Any],
        translated_content: Dict[str, Any],
        source_lang: str,
        target_lang: str,
        model_provider: str,
        model_name: str
    ) -> str:
        """Create a new translation session"""
        
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        session = TranslationSession(
            session_id=session_id,
            file_name=file_name,
            file_path=file_path,
            file_type=file_type,
            original_content=original_content,
            translated_content=translated_content,
            source_lang=source_lang,
            target_lang=target_lang,
            model_provider=model_provider,
            model_name=model_name,
            created_at=now,
            updated_at=now
        )
        
        self.active_sessions[session_id] = session
        self._save_session(session)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[TranslationSession]:
        """Get session by ID"""
        
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Try to load from storage
        session_file = self.session_storage_path / f"{session_id}.json"
        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                session = TranslationSession(**data)
                self.active_sessions[session_id] = session
                return session
        
        return None
    
    def update_session_content(
        self,
        session_id: str,
        translated_content: Dict[str, Any]
    ) -> bool:
        """Update session with new translated content"""
        
        self.logger.info(f"Updating session content: {session_id}")
        
        session = self.get_session(session_id)
        if not session:
            self.logger.error(f"Session not found for content update: {session_id}")
            return False
        
        session.translated_content = translated_content
        session.updated_at = datetime.now()
        
        self.logger.debug(f"Saving session with updated content: {session_id}")
        self._save_session(session)
        self.logger.info(f"Session content updated successfully: {session_id}")
        return True
    
    def update_session(
        self,
        session_id: str,
        updated_session: TranslationSession
    ) -> bool:
        """Update entire session object"""
        
        self.logger.info(f"Updating session: {session_id}")
        
        if session_id not in self.active_sessions:
            existing_session = self.get_session(session_id)
            if not existing_session:
                self.logger.error(f"Session not found for update: {session_id}")
                return False
        
        # Update the session in active sessions
        self.active_sessions[session_id] = updated_session
        updated_session.updated_at = datetime.now().isoformat()
        
        self.logger.debug(f"Saving updated session: {session_id}")
        self._save_session(updated_session)
        self.logger.info(f"Session updated successfully: {session_id}")
        return True
    
    def add_chat_message(
        self,
        session_id: str,
        user_message: str,
        bot_response: str
    ) -> bool:
        """Add chat message to session"""
        
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.chat_history.extend([
            {"role": "user", "content": user_message, "timestamp": datetime.now().isoformat()},
            {"role": "assistant", "content": bot_response, "timestamp": datetime.now().isoformat()}
        ])
        session.updated_at = datetime.now().isoformat()

        self._save_session(session)
        return True
    
    def finalize_session(self, session_id: str) -> bool:
        """Finalize session for document reconstruction"""
        
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.is_finalized = True
        session.updated_at = datetime.now().isoformat()
        
        self._save_session(session)
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        session_file = self.session_storage_path / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
            return True
        
        return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions"""
        
        sessions = []
        
        # Get from active sessions
        for session in self.active_sessions.values():
            sessions.append({
                "session_id": session.session_id,
                "file_name": session.file_name,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "is_finalized": session.is_finalized
            })
        
        # Get from storage
        for session_file in self.session_storage_path.glob("*.json"):
            session_id = session_file.stem
            if session_id not in self.active_sessions:
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        sessions.append({
                            "session_id": data["session_id"],
                            "file_name": data["file_name"],
                            "created_at": data["created_at"],
                            "updated_at": data["updated_at"],
                            "is_finalized": data.get("is_finalized", False)
                        })
                except Exception:
                    continue
        
        return sessions
    
    def _save_session(self, session: TranslationSession) -> None:
        """Save session to storage"""
        
        session_file = self.session_storage_path / f"{session.session_id}.json"
        
        # Convert to dict for JSON serialization
        session_data = asdict(session)
        session_data["created_at"] = session.created_at
        session_data["updated_at"] = session.updated_at
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
