"""Session management for conversation history and context."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages conversation sessions with history and context.

    Features:
    - In-memory session storage
    - Conversation history (configurable length, default 5 for memory optimization)
    - Session expiration (1 hour)
    - Topic tracking
    """

    SESSION_EXPIRY_HOURS = 1

    def __init__(self, max_history_length: int = None):
        """Initialize the session manager."""
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.max_history_length = max_history_length or settings.max_history_length

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get or create a session.

        Args:
            session_id: Unique session identifier

        Returns:
            Session data dictionary
        """
        # Clean expired sessions
        self._cleanup_expired_sessions()

        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "history": [],
                "current_topic": None,
                "context": {},
                "created_at": datetime.now(),
                "last_active": datetime.now(),
            }
            logger.debug(f"Created new session: {session_id}")

        session = self.sessions[session_id]
        session["last_active"] = datetime.now()

        return session

    def update_session(
        self,
        session_id: str,
        message: str,
        response: str,
        intent: Optional[str] = None,
    ) -> None:
        """
        Update session with new exchange.

        Args:
            session_id: Session identifier
            message: User's message
            response: Bot's response
            intent: Detected intent (optional)
        """
        session = self.get_session(session_id)

        # Add to history
        session["history"].append(
            {
                "user": message,
                "assistant": response,
                "intent": intent,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Trim history to max length
        if len(session["history"]) > self.max_history_length:
            session["history"] = session["history"][-self.max_history_length :]

        # Update current topic
        if intent and intent != "general":
            session["current_topic"] = intent

        logger.debug(f"Updated session {session_id}, history length: {len(session['history'])}")

    def get_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of exchanges to return

        Returns:
            List of message/response pairs
        """
        session = self.get_session(session_id)
        history = session.get("history", [])

        if limit:
            return history[-limit:]
        return history

    def get_current_topic(self, session_id: str) -> Optional[str]:
        """Get the current topic for a session."""
        session = self.get_session(session_id)
        return session.get("current_topic")

    def set_context(
        self,
        session_id: str,
        key: str,
        value: Any,
    ) -> None:
        """Set a context value for a session."""
        session = self.get_session(session_id)
        session["context"][key] = value

    def get_context(
        self,
        session_id: str,
        key: str,
        default: Any = None,
    ) -> Any:
        """Get a context value from a session."""
        session = self.get_session(session_id)
        return session.get("context", {}).get(key, default)

    def clear_session(self, session_id: str) -> None:
        """Clear a session's data."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.debug(f"Cleared session: {session_id}")

    def _cleanup_expired_sessions(self) -> None:
        """Remove expired sessions."""
        now = datetime.now()
        expiry_threshold = timedelta(hours=self.SESSION_EXPIRY_HOURS)

        expired = [
            sid
            for sid, session in self.sessions.items()
            if now - session.get("last_active", now) > expiry_threshold
        ]

        for sid in expired:
            del self.sessions[sid]
            logger.debug(f"Expired session removed: {sid}")

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
