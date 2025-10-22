import datetime
from app.bot.repo_mock import RepoMock

class IBot:
    def reply(self, message: str, session_id: str) -> str: ...

class Bot(IBot):
    def __init__(self, repo: RepoMock | None = None):
        self.repo = repo or RepoMock()

    def reply(self, message: str, session_id: str) -> str:
        
        if session_id not in self.repo.sessions:
            session_id = self.repo.create_session()

        conv_id = self.repo.get_or_create_conversation(session_id)

        self.repo.append_message(conv_id, "user", message)

        text = message.lower()
        if "hola" in text:
            reply = "¡Hola! ¿Cómo estás?"
        elif "hora" in text:
            reply = f"Son las {datetime.datetime.now().strftime('%H:%M:%S')}"
        elif "ayuda" in text:
            reply = "Puedo responder 'hola', 'hora' o repetir tu mensaje."
        else:
            reply = f"Echo: {message}"

        # guardar respuesta del bot
        self.repo.append_message(conv_id, "bot", reply)
        return reply
