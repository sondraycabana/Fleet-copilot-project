import uuid
from typing import Dict, Any, List

class ConversationStore:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConversationStore, cls).__new__(cls, *args, **kwargs)
            cls._instance._storage = {}
        return cls._instance

    def save_session(self, session_id: str, state_snapshot: Dict[str, Any]):
        """Persists the serialized agent state snapshot indexed by a session key."""
        if not session_id:
            session_id = str(uuid.uuid4())
        self._storage[session_id] = state_snapshot
        return session_id

    def load_session(self, session_id: str) -> Dict[str, Any]:
        """Retrieves session context history or returns an empty state dict."""
        return self._storage.get(session_id, {
            "messages": [],
            "company_context": "",
            "operator_context": "",
            "gathered_evidence": [],
            "staged_proposals": [],
            "requires_approval": False,
            "security_violation": False
        })

    def clear_session(self, session_id: str):
        """Evicts a session from memory storage."""
        if session_id in self._storage:
            del self._storage[session_id]
