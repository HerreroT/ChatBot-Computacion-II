import uuid
from collections import defaultdict

class RepoMock:
    
    def __init__(self):
        self.sessions = {}                     
        self.conversations = defaultdict(list)

    def create_session(self, user_id: str | None = None) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {"user_id": user_id}
        return session_id

    def get_or_create_conversation(self, session_id: str) -> str:
        if "conversation_id" not in self.sessions[session_id]:
            self.sessions[session_id]["conversation_id"] = str(uuid.uuid4())
        return self.sessions[session_id]["conversation_id"]

    def append_message(self, conversation_id: str, sender: str, text: str) -> str:
        msg_id = str(uuid.uuid4())
        self.conversations[conversation_id].append({
            "id": msg_id, "sender": sender, "text": text
        })
        return msg_id

    def get_messages(self, conversation_id: str) -> list:
        return self.conversations[conversation_id]
