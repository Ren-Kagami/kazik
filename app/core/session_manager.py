"""
Session management for slot machine game.
Handles session creation, storage, retrieval, and cleanup.
"""

import asyncio
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging

from app.models.slot_machine import GameSession
from app.core.config import logger

# Session storage configuration
SESSION_STORAGE_DIR = Path("data/sessions")
SESSION_CLEANUP_INTERVAL = 3600  # 1 hour in seconds
SESSION_MAX_AGE_HOURS = 24


class SessionManager:
    """
    Manages game sessions with file-based persistence.
    Provides CRUD operations and automatic cleanup.
    """

    def __init__(self) -> None:
        """Initialize session manager with storage setup."""
        self.sessions: Dict[str, GameSession] = {}
        self.setup_storage()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
        logger.info("Session manager initialized")

    def setup_storage(self) -> None:
        """Create storage directory if it doesn't exist."""
        SESSION_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        self._load_existing_sessions()

    def _load_existing_sessions(self) -> None:
        """Load existing sessions from storage on startup."""
        try:
            session_files = SESSION_STORAGE_DIR.glob("session_*.json")
            loaded_count = 0

            for session_file in session_files:
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)

                    # Convert timestamps
                    session_data['created_at'] = datetime.fromisoformat(
                        session_data['created_at'].replace('Z', '+00:00')
                    )
                    session_data['last_activity'] = datetime.fromisoformat(
                        session_data['last_activity'].replace('Z', '+00:00')
                    )

                    session = GameSession(**session_data)

                    # Only load recent sessions
                    if self._is_session_recent(session):
                        self.sessions[session.session_id] = session
                        loaded_count += 1
                    else:
                        # Remove old session file
                        session_file.unlink()

                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    logger.warning(f"Failed to load session from {session_file}: {e}")
                    # Remove corrupted session file
                    session_file.unlink(missing_ok=True)

            logger.info(f"Loaded {loaded_count} existing sessions")

        except Exception as e:
            logger.error(f"Error loading existing sessions: {e}")

    def _is_session_recent(self, session: GameSession) -> bool:
        """Check if session is within the maximum age limit."""
        max_age = datetime.utcnow() - timedelta(hours=SESSION_MAX_AGE_HOURS)
        return session.last_activity > max_age

    def _start_cleanup_task(self) -> None:
        """Start the background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self) -> None:
        """Background task to clean up old sessions."""
        while True:
            try:
                await asyncio.sleep(SESSION_CLEANUP_INTERVAL)
                await self.cleanup_old_sessions()
            except asyncio.CancelledError:
                logger.info("Session cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")

    async def cleanup_old_sessions(self) -> int:
        """
        Remove sessions older than maximum age.

        Returns:
            Number of sessions cleaned up
        """
        try:
            max_age = datetime.utcnow() - timedelta(hours=SESSION_MAX_AGE_HOURS)
            old_sessions = [
                session_id for session_id, session in self.sessions.items()
                if session.last_activity < max_age
            ]

            for session_id in old_sessions:
                await self._remove_session_file(session_id)
                del self.sessions[session_id]

            if old_sessions:
                logger.info(f"Cleaned up {len(old_sessions)} old sessions")

            return len(old_sessions)

        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
            return 0

    async def create_session(self, initial_credits: int = 100) -> GameSession:
        """
        Create a new game session.

        Args:
            initial_credits: Starting credits for the session

        Returns:
            GameSession: New session object
        """
        try:
            session = GameSession(credits=initial_credits)
            self.sessions[session.session_id] = session

            # Persist to storage
            await self._save_session(session)

            logger.info(f"Created session {session.session_id} with {initial_credits} credits")
            return session

        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise

    async def get_session(self, session_id: str) -> Optional[GameSession]:
        """
        Retrieve session by ID.

        Args:
            session_id: Unique session identifier

        Returns:
            GameSession if found, None otherwise
        """
        try:
            session = self.sessions.get(session_id)
            if session and self._is_session_recent(session):
                session.update_activity()
                await self._save_session(session)
                return session
            elif session:
                # Session is too old, remove it
                await self.delete_session(session_id)

            return None

        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None

    async def update_session(
            self,
            session_id: str,
            credits: int,
            total_spins: int = None,
            total_winnings: int = None
    ) -> Optional[GameSession]:
        """
        Update session data.

        Args:
            session_id: Session to update
            credits: New credit amount
            total_spins: Updated total spins (optional)
            total_winnings: Updated total winnings (optional)

        Returns:
            Updated GameSession if found, None otherwise
        """
        try:
            session = self.sessions.get(session_id)
            if not session:
                return None

            session.credits = credits
            if total_spins is not None:
                session.total_spins = total_spins
            if total_winnings is not None:
                session.total_winnings = total_winnings

            session.update_activity()

            # Check if session should be marked inactive
            if credits <= 0:
                session.is_active = False

            await self._save_session(session)

            logger.debug(f"Updated session {session_id}: credits={credits}")
            return session

        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            return None

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
                await self._remove_session_file(session_id)
                logger.info(f"Deleted session {session_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

    async def get_recent_sessions(
            self,
            since: datetime,
            limit: int = 100
    ) -> List[GameSession]:
        """
        Get sessions created since a specific time.

        Args:
            since: Only return sessions created after this time
            limit: Maximum number of sessions to return

        Returns:
            List of recent GameSession objects
        """
        try:
            recent_sessions = [
                session for session in self.sessions.values()
                if session.created_at >= since
            ]

            # Sort by creation time (newest first) and limit
            recent_sessions.sort(key=lambda s: s.created_at, reverse=True)
            return recent_sessions[:limit]

        except Exception as e:
            logger.error(f"Error retrieving recent sessions: {e}")
            return []

    async def get_active_sessions_count(self) -> int:
        """
        Get count of currently active sessions.

        Returns:
            Number of active sessions
        """
        try:
            return len([
                session for session in self.sessions.values()
                if session.is_active and self._is_session_recent(session)
            ])
        except Exception as e:
            logger.error(f"Error counting active sessions: {e}")
            return 0

    async def _save_session(self, session: GameSession) -> None:
        """
        Save session to persistent storage.

        Args:
            session: Session to save
        """
        try:
            session_file = SESSION_STORAGE_DIR / f"session_{session.session_id}.json"

            # Convert session to dict with ISO format timestamps
            session_dict = session.dict()
            session_dict['created_at'] = session.created_at.isoformat() + 'Z'
            session_dict['last_activity'] = session.last_activity.isoformat() + 'Z'

            # Write atomically by writing to temp file first
            temp_file = session_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(session_dict, f, indent=2)

            temp_file.rename(session_file)

        except Exception as e:
            logger.error(f"Error saving session {session.session_id}: {e}")
            raise

    async def _remove_session_file(self, session_id: str) -> None:
        """
        Remove session file from storage.

        Args:
            session_id: Session ID to remove
        """
        try:
            session_file = SESSION_STORAGE_DIR / f"session_{session_id}.json"
            session_file.unlink(missing_ok=True)

        except Exception as e:
            logger.warning(f"Error removing session file {session_id}: {e}")

    async def get_session_statistics(self) -> Dict[str, any]:
        """
        Get overall session statistics.

        Returns:
            Dictionary with session statistics
        """
        try:
            sessions = list(self.sessions.values())
            recent_sessions = [s for s in sessions if self._is_session_recent(s)]
            active_sessions = [s for s in recent_sessions if s.is_active]

            total_spins = sum(s.total_spins for s in sessions)
            total_winnings = sum(s.total_winnings for s in sessions)

            return {
                "total_sessions": len(sessions),
                "recent_sessions": len(recent_sessions),
                "active_sessions": len(active_sessions),
                "total_spins_all_time": total_spins,
                "total_winnings_all_time": total_winnings,
                "average_spins_per_session": total_spins / len(sessions) if sessions else 0,
                "storage_directory": str(SESSION_STORAGE_DIR.absolute())
            }

        except Exception as e:
            logger.error(f"Error getting session statistics: {e}")
            return {}

    def shutdown(self) -> None:
        """Cleanup resources on shutdown."""
        try:
            if self._cleanup_task and not self._cleanup_task.done():
                self._cleanup_task.cancel()
            logger.info("Session manager shutdown complete")
        except Exception as e:
            logger.error(f"Error during session manager shutdown: {e}")

    def __del__(self):
        """Ensure cleanup on garbage collection."""
        self.shutdown()