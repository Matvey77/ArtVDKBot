from app.database.models import async_session, Greeting, User
from sqlalchemy import select


# Получение всех поздравлений с прикреплёнными файлами
async def get_all_greetings_with_media():
    async with async_session() as session:
        # Выполняем запрос, чтобы получить поздравления с прикреплёнными файлами (media не является NULL)
        result = await session.execute(
            select(Greeting).where(Greeting.media.isnot(None))
        )
        greetings = result.scalars().all()
        return greetings


# Проверка, имеет ли пользователь права администратора
async def is_admin(users_id: int) -> bool:
    async with async_session() as session:
        result = await session.scalar(
            select(User.rights).where(User.id == users_id)
        )
        return bool(result)
