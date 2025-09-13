"""
Session management for slot machine game.
Handles creating, updating, and tracking game sessions.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
from collections import defaultdict

from app.models.slot_machine import GameSession
from app.core.config import SESSION_TIMEOUT_HOURS, MAX_SESSIONS_PER_USER, logger


class SessionManager:
    """
    Manages game sessions in memory.

    In a production environment, this would use a database
    or Redis for persistent storage.
    """

    def __init__(self):
        """Initialize the session manager."""
        self._sessions: Dict[str, GameSession] = {}
        self._user_sessions: Dict[str, List[str]] = defaultdict(list)
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()

        logger.info("Session manager initialized")

    def _start_cleanup_task(self):
        """Start the background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())

    async def _cleanup_expired_sessions(self):
        """
        Background task to clean up expired sessions.
        Runs every hour to remove inactive sessions.
        """
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self._remove_expired_sessions()
            except asyncio.CancelledError:
                logger.info("Session cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in session cleanup task: {e}")

    async def _remove_expired_sessions(self):
        """Remove sessions that have exceeded the timeout period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=SESSION_TIMEOUT_HOURS)
        expired_sessions = [
            session_id for session_id, session in self._sessions.items()
            if session.last_activity < cutoff_time
        ]

        for session_id in expired_sessions:
            await self._remove_session(session_id)

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

    async def _remove_session(self, session_id: str):
        """
        Remove a session from storage.

        Args:
            session_id: Session identifier to remove
        """
        if session_id in self._sessions:
            # Remove from user sessions tracking
            for user_id, sessions in self._user_sessions.items():
                if session_id in sessions:
                    sessions.remove(session_id)
                    break

            # Remove from main sessions storage
            del self._sessions[session_id]

    async def create_session(self, initial_credits: int, user_id: str = None) -> GameSession:
        """
        Create a new game session.

        Args:
            initial_credits: Starting credits for the session
            user_id: Optional user identifier for session tracking

        Returns:
            GameSession: Newly created session
        """
        # Generate unique session ID
        session_id = str(uuid.uuid4())

        # Create session object
        session = GameSession(
            session_id=session_id,
            credits=initial_credits,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )

        # Store session
        self._sessions[session_id] = session

        # Track by user if provided
        if user_id:
            # Enforce session limit per user
            user_sessions = self._user_sessions[user_id]
            if len(user_sessions) >= MAX_SESSIONS_PER_USER:
                # Remove oldest session
                oldest_session_id = user_sessions.pop(0)
                await self._remove_session(oldest_session_id)
                logger.info(f"Removed oldest session for user {user_id}")

            user_sessions.append(session_id)

        logger.info(f"Created session {session_id} with {initial_credits} credits")
        return session

    async def get_session(self, session_id: str) -> Optional[GameSession]:
        """
        Retrieve a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            GameSession if found, None otherwise
        """
        session = self._sessions.get(session_id)

        if session:
            # Update last activity
            session.update_activity()

        return session

    async def update_session(
        self,
        session_id: str,
        credits: int = None,
        total_spins: int = None,
        total_winnings: int = None
    ) -> Optional[GameSession]:
        """
        Update session data.

        Args:
            session_id: Session identifier
            credits: New credits amount
            total_spins: New total spins count
            total_winnings: New total winnings amount

        Returns:
            Updated GameSession if found, None otherwise
        """
        session = self._sessions.get(session_id)

        if not session:
            return None

        # Update fields if provided
        if credits is not None:
            session.credits = credits

        if total_spins is not None:
            session.total_spins = total_spins

        if total_winnings is not None:
            session.total_winnings = total_winnings

        # Update activity timestamp
        session.update_activity()

        # Check if session should be marked inactive
        if session.credits <= 0:
            session.is_active = False

        logger.debug(f"Updated session {session_id}")
        return session

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier to delete

        Returns:
            True if session was deleted, False if not found
        """
        if session_id in self._sessions:
            await self._remove_session(session_id)
            logger.info(f"Deleted session {session_id}")
            return True

        return False

    async def get_recent_sessions(
        self,
        since: datetime = None,
        limit: int = 100
    ) -> List[GameSession]:
        """
        Get recent sessions for analytics.

        Args:
            since: Only return sessions created after this time
            limit: Maximum number of sessions to return

        Returns:
            List of recent GameSession objects
        """
        if since is None:
            since = datetime.utcnow() - timedelta(hours=24)

        recent_sessions = [
            session for session in self._sessions.values()
            if session.created_at >= since
        ]

        # Sort by creation time, newest first
        recent_sessions.sort(key=lambda x: x.created_at, reverse=True)

        return recent_sessions[:limit]

    async def get_active_sessions(self) -> List[GameSession]:
        """
        Get all currently active sessions.

        Returns:
            List of active GameSession objects
        """
        active_sessions = [
            session for session in self._sessions.values()
            if session.is_active and session.credits > 0
        ]

        return active_sessions

    async def get_session_statistics(self) -> Dict[str, any]:
        """
        Get overall session statistics.

        Returns:
            Dictionary with session statistics
        """
        all_sessions = list(self._sessions.values())
        active_sessions = await self.get_active_sessions()

        if not all_sessions:
            return {
                "total_sessions": 0,
                "active_sessions": 0,
                "average_spins": 0,
                "average_winnings": 0,
                "total_spins": 0,
                "total_winnings": 0
            }

        total_spins = sum(session.total_spins for session in all_sessions)
        total_winnings = sum(session.total_winnings for session in all_sessions)

        return {
            "total_sessions": len(all_sessions),
            "active_sessions": len(active_sessions),
            "average_spins": total_spins / len(all_sessions),
            "average_winnings": total_winnings / len(all_sessions),
            "total_spins": total_spins,
            "total_winnings": total_winnings,
            "oldest_session": min(s.created_at for s in all_sessions),
            "newest_session": max(s.created_at for s in all_sessions)
        }

    async def get_user_sessions(self, user_id: str) -> List[GameSession]:
        """
        Get all sessions for a specific user.

        Args:
            user_id: User identifier

        Returns:
            List of GameSession objects for the user
        """
        session_ids = self._user_sessions.get(user_id, [])
        return [
            self._sessions[session_id]
            for session_id in session_ids
            if session_id in self._sessions
        ]

    def get_session_count(self) -> int:
        """
        Get total number of active sessions.

        Returns:
            Number of sessions currently stored
        """
        return len(self._sessions)

    async def shutdown(self):
        """
        Shutdown the session manager and cleanup resources.
        """
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("Session manager shutdown complete")