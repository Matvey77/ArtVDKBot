from app.database.models import async_session, Teacher, Greeting, User
from sqlalchemy import select, update, insert
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import NoResultFound


# Получение списка преподавателей
async def get_teachers():
    async with async_session() as session:
        result = await session.execute(select(Teacher))
        return result.scalars().all()


# Добавление поздравления
async def add_greeting(teacher_id, message_text, users_id, media=None):
    async with async_session() as session:
        new_greeting = Greeting(
            teacher_id=teacher_id,
            message_text=message_text,
            media=media,
            users_id=users_id
        )
        session.add(new_greeting)
        await session.commit()


# Получение поздравлений для преподавателя
async def get_greetings(teacher_id):
    async with async_session() as session:
        return await session.execute(select(Greeting).where(Greeting.teacher_id == teacher_id)).scalars().all()


async def set_user(tg_id: int, username: str) -> None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id = tg_id, username = username))
            await session.commit()


# Функция для сохранения поздравлений
async def save_greeting(teacher_id, users_id, text, media=None):
    async with async_session() as session:
        try:
            # Получаем объект User по Telegram ID
            user = await session.execute(select(User).where(User.tg_id == users_id))
            user_id = user.scalar_one().id  # Присваиваем правильный ID из таблицы users

            # Добавляем запись в таблицу greetings с внешним ключом users_id
            greeting = Greeting(
                teacher_id=teacher_id,
                users_id=user_id,  # Используем user_id из users
                message_text=text,
                media=media
            )
            session.add(greeting)
            await session.commit()
        except NoResultFound:
            raise ValueError("Пользователь не найден в таблице users")


# Функция для проверки прав пользователя (администратор или нет)
async def get_user(user_id):
    async with async_session() as session:
        result = await session.scalar(
            select(User).where(User.tg_id == user_id)
        )
        return result


# Получение всех поздравлений с медиа
async def get_all_greetings():
    async with async_session() as session:
        result = await session.execute(
            select(Greeting)
            .options(
                joinedload(Greeting.teacher),   # Подгружаем информацию о преподавателе
                joinedload(Greeting.sender)       # Подгружаем информацию о пользователе (отправителе)
            )
        )
        return result.scalars().all()


async def update_rights(tg_id: int):
   async with async_session() as session:
        await session.execute(
                    update(User).where(User.tg_id == tg_id).values(rights=True)
                )
        await session.commit()
        print(f"Права пользователя с tg_id {tg_id} обновлены на True.")


# Обновление информации о преподавателе
async def update_teacher(teacher_id, full_name, email, telegram_username):
    async with async_session() as session:
        await session.execute(
            update(Teacher)
            .where(Teacher.id == teacher_id)
            .values(full_name=full_name, email=email, telegram_username=telegram_username)
        )
        await session.commit()


# Обновление текста поздравления
async def update_greeting_text(greeting_id, new_text):
    async with async_session() as session:
        await session.execute(
            update(Greeting)
            .where(Greeting.id == greeting_id)
            .values(message_text=new_text)
        )
        await session.commit()


# Add a new teacher
async def add_teacher(full_name, email, telegram_username):
    async with async_session() as session:
        new_teacher = Teacher(full_name=full_name, email=email, telegram_username=telegram_username)
        session.add(new_teacher)
        await session.commit()


# Add a new greeting for admin
async def add_admin_greeting(teacher_id, message_text, users_id):
    async with async_session() as session:
        new_greeting = Greeting(
            teacher_id=teacher_id,
            message_text=message_text,
            users_id=users_id
        )
        session.add(new_greeting)
        await session.commit()


async def update_greeting_media(greeting_id, new_media):
    async with async_session() as session:
        await session.execute(
            update(Greeting)
            .where(Greeting.id == greeting_id)
            .values(media=new_media)
        )
        await session.commit()


async def get_teacher_by_id(teacher_id):
    async with async_session() as session:
        result = await session.execute(select(Teacher).where(Teacher.id == teacher_id))
        return result.scalar_one()