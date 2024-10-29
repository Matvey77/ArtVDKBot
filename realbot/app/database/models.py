from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncAttrs, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column, relationship
from sqlalchemy import Column, Integer, String, Text, BigInteger, ForeignKey, Boolean


DATABASE_URL = "sqlite+aiosqlite:///bot_database.db"

engine = create_async_engine(url=DATABASE_URL)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(AsyncAttrs, DeclarativeBase):
    pass


# Модель преподавателей
class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    telegram_username = Column(String, nullable=True)


# Модель поздравлений
class Greeting(Base):
    __tablename__ = "greetings"

    id = Column(Integer, primary_key=True, autoincrement=True) #
    teacher_id = Column(Integer, nullable=False)
    message_text = Column(Text, nullable=False)
    media = Column(String, nullable=True)
    users_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    sender = relationship("User", backref="greetings") #


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    username: Mapped[str] = mapped_column(String(100))
    rights: Mapped[bool] = mapped_column(Boolean, default=False)  # Указан Boolean вместо String



async def async_main():
    async with engine.begin() as conn:
        # Создание таблиц
        await conn.run_sync(Base.metadata.create_all)
