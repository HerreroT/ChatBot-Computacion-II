import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Session as ChatSession, User


@pytest.mark.anyio(backend="asyncio")
async def test_create_user_and_session(session_factory):
    async with session_factory() as s:  # type: AsyncSession
        user = User(email="test@example.com", hashed_password="x")
        s.add(user)
        await s.flush()
        assert user.id is not None

        sess = ChatSession(user_id=user.id)
        s.add(sess)
        await s.flush()
        assert sess.id is not None

        # Load back
        result = await s.execute(sa.select(User).where(User.id == user.id))
        loaded_user = result.scalar_one()
        assert loaded_user.email == "test@example.com"
