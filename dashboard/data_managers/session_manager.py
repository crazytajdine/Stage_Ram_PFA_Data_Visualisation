# dashboard/data_managers/session_manager.py
from __future__ import annotations

import os
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Iterable
from collections import defaultdict

import redis
from schemas.auth import UserSession


# ---------- Pydantic v1/v2 compatibility helpers ----------
def _session_dump(s: UserSession) -> str:
    # pydantic v2
    if hasattr(s, "model_dump_json"):
        return s.model_dump_json()
    # pydantic v1
    return s.json()

def _session_load(data: str) -> UserSession:
    # pydantic v2
    if hasattr(UserSession, "model_validate_json"):
        return UserSession.model_validate_json(data)
    # pydantic v1
    return UserSession.parse_raw(data)


class SessionManager:
    """
    Stores short-lived sessions in Redis (preferred) with in-memory fallback.
    A session includes: email, role, login_time, session_id, and optional
    `permissions` (list of page slugs). `permissions=None` means "all pages".
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        session_timeout_hours: int = 8,
    ) -> None:
        self.sessions: Dict[str, UserSession] = {}  # in-memory fallback
        self.session_timeout = timedelta(hours=session_timeout_hours)

        # Create/verify a Redis client if not provided
        self.redis_client = redis_client
        if not self.redis_client:
            url = os.getenv("REDIS_URL")
            try:
                if url:
                    self.redis_client = redis.from_url(url, decode_responses=True)
                else:
                    self.redis_client = redis.Redis(
                        host=os.getenv("REDIS_HOST", "localhost"),
                        port=int(os.getenv("REDIS_PORT", "6379")),
                        db=int(os.getenv("REDIS_DB", "0")),
                        decode_responses=True,
                    )
                self.redis_client.ping()
                logging.info("Connected to Redis for session management")
            except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
                logging.warning("Redis not available, using in-memory session storage")
                self.redis_client = None

    # ---------- Core API ----------

    def create_session(
        self,
        email: str,
        role: str,
        permissions: Optional[List[str]] = None,
    ) -> str:
        """
        Create a new session. `permissions` are page slugs the user can access.
        None => all pages allowed.
        """
        session_id = secrets.token_urlsafe(32)
        session = UserSession(
            email=email,
            role=role,
            login_time=datetime.now(),
            session_id=session_id,
            permissions=permissions,
        )

        if self.redis_client:
            try:
                key = f"session:{session_id}"
                ttl = int(self.session_timeout.total_seconds())
                self.redis_client.setex(key, ttl, _session_dump(session))

                # Track user's active sessions for quick logout-everywhere
                user_key = f"user_sessions:{email.lower().strip()}"
                self.redis_client.sadd(user_key, session_id)
                self.redis_client.expire(user_key, ttl)
            except redis.exceptions.RedisError as e:
                logging.error(f"Redis error creating session: {e}")
                self.sessions[session_id] = session
        else:
            self.sessions[session_id] = session

        logging.info(f"Session created for user='{email}', role='{role}'")
        return session_id

    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Fetch session by ID, extending TTL on access (sliding window)."""
        if not session_id:
            return None

        if self.redis_client:
            try:
                key = f"session:{session_id}"
                data = self.redis_client.get(key)
                if data:
                    # extend TTL
                    self.redis_client.expire(key, int(self.session_timeout.total_seconds()))
                    return _session_load(data)
            except redis.exceptions.RedisError as e:
                logging.error(f"Redis error retrieving session: {e}")
                # fall through to memory fallback
                return self._get_memory_session(session_id)
            return None

        return self._get_memory_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        """Delete a single session (logout)."""
        deleted = False

        if self.redis_client:
            try:
                key = f"session:{session_id}"
                data = self.redis_client.get(key)
                if data:
                    s = _session_load(data)
                    self.redis_client.srem(f"user_sessions:{s.email.lower().strip()}", session_id)
                deleted = bool(self.redis_client.delete(key))
            except redis.exceptions.RedisError as e:
                logging.error(f"Redis error deleting session: {e}")

        if session_id in self.sessions:
            del self.sessions[session_id]
            deleted = True

        if deleted:
            logging.info(f"Session '{session_id}' deleted")
        return deleted

    def get_user_sessions(self, email: str) -> List[UserSession]:
        """List active sessions for a given email."""
        out: List[UserSession] = []
        email_key = email.lower().strip()

        if self.redis_client:
            try:
                user_key = f"user_sessions:{email_key}"
                for sid in self.redis_client.smembers(user_key) or []:
                    s = self.get_session(sid)
                    if s:
                        out.append(s)
            except redis.exceptions.RedisError as e:
                logging.error(f"Redis error getting user sessions: {e}")
        else:
            now = datetime.now()
            for sid, s in list(self.sessions.items()):
                if s.email.lower().strip() == email_key and (now - s.login_time) < self.session_timeout:
                    out.append(s)

        return out

    def delete_user_sessions(self, email: str) -> int:
        """Force logout on all sessions for a user."""
        email_key = email.lower().strip()
        count = 0

        if self.redis_client:
            try:
                user_key = f"user_sessions:{email_key}"
                for sid in list(self.redis_client.smembers(user_key) or []):
                    if self.delete_session(sid):
                        count += 1
                self.redis_client.delete(user_key)
            except redis.exceptions.RedisError as e:
                logging.error(f"Redis error deleting user sessions: {e}")
        else:
            now = datetime.now()
            for sid, s in list(self.sessions.items()):
                if s.email.lower().strip() == email_key and (now - s.login_time) < self.session_timeout:
                    del self.sessions[sid]
                    count += 1

        if count:
            logging.info(f"Deleted {count} session(s) for user='{email_key}'")
        return count

    # ---------- Analytics / Maintenance ----------

    def get_active_sessions_count(self) -> Dict[str, int]:
        """
        Return counts by role plus 'total'. Roles are dynamic (no fixed keys).
        Example: {'total': 3, 'admin': 1, 'ops': 2}
        """
        counts: Dict[str, int] = defaultdict(int)

        if self.redis_client:
            try:
                for key in self._scan_keys("session:*"):
                    data = self.redis_client.get(key)
                    if not data:
                        continue
                    s = _session_load(data)
                    counts[s.role] += 1
                    counts["total"] += 1
                return dict(counts)
            except redis.exceptions.RedisError as e:
                logging.error(f"Redis error counting sessions: {e}")
                # fall back to memory

        # memory fallback
        now = datetime.now()
        for s in list(self.sessions.values()):
            if now - s.login_time < self.session_timeout:
                counts[s.role] += 1
                counts["total"] += 1
        return dict(counts)

    def cleanup_expired_sessions(self) -> None:
        """Remove expired sessions in memory fallback."""
        if self.redis_client:
            return  # Redis handles expiration
        now = datetime.now()
        expired = [sid for sid, s in self.sessions.items() if now - s.login_time >= self.session_timeout]
        for sid in expired:
            del self.sessions[sid]
        if expired:
            logging.info(f"Cleaned up {len(expired)} expired sessions (memory)")

    # ---------- Internals ----------

    def _get_memory_session(self, session_id: str) -> Optional[UserSession]:
        s = self.sessions.get(session_id)
        if not s:
            return None
        if (datetime.now() - s.login_time) < self.session_timeout:
            return s
        # expired
        try:
            del self.sessions[session_id]
        except KeyError:
            pass
        logging.info(f"Session '{session_id}' expired (memory)")
        return None

    def _scan_keys(self, pattern: str, count: int = 200) -> Iterable[str]:
        """
        Safer alternative to KEYS: iterate using SCAN to avoid blocking Redis.
        """
        if not self.redis_client:
            return []
        cursor = 0
        while True:
            cursor, batch = self.redis_client.scan(cursor=cursor, match=pattern, count=count)
            for k in batch:
                yield k
            if cursor == 0:
                break
