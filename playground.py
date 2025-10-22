from app.bot.flow import Bot

# crear instancia del bot
b = Bot()

# crear una sesión
sid = b.repo.create_session()

# mandar mensajes al bot
print(b.reply("hola", sid))
print(b.reply("qué hora es?", sid))
print(b.reply("no entiendo nada", sid))

# ver qué guardó RepoMock
cid = b.repo.get_or_create_conversation(sid)
print(b.repo.get_messages(cid))
