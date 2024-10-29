import asyncio
from aiogram import Bot, Dispatcher
# импорт из других файлов
from app.handlers import router
from config import BOT_TOKEN
from app.database.models import async_main


async def main():
    await async_main()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    dp['bot'] = bot

    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program has stopped")

