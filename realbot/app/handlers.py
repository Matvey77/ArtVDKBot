from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from pathlib import Path
from app.database import requests as rq


router = Router()


class Form(StatesGroup):
    waiting_for_greeting_text = State()


@router.message(Command("start"))
async def start_command(message: types.Message):
    await rq.set_user(message.from_user.id, message.from_user.username)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Поздравления", callback_data="greetings")],
            [InlineKeyboardButton(text="Задать вопрос", callback_data="questions")]
        ]
    )
    await message.answer("Добро пожаловать! Что вы хотите сделать?", reply_markup=keyboard)


@router.callback_query(F.data == "greetings")
async def choose_teacher(callback: types.CallbackQuery):
    teachers = await rq.get_teachers()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=teacher.full_name, callback_data=f"teacher_{teacher.id}")]
                         for teacher in teachers]
    )
    await callback.message.answer("Выберите преподавателя:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("teacher_"))
async def send_greeting(callback: types.CallbackQuery, state: FSMContext):
    teacher_id = int(callback.data.split("_")[1])
    await callback.message.answer("Отправьте текст поздравления:")

    # Сохраняем teacher_id в состоянии и устанавливаем новое состояние
    await state.update_data(teacher_id=teacher_id)  # Сохраняем teacher_id в состоянии
    await state.set_state(Form.waiting_for_greeting_text)  # Устанавливаем новое состояние


@router.message(Form.waiting_for_greeting_text, F.content_type.in_(['text', 'document', 'photo', 'video']))
async def receive_greeting(message: types.Message, state: FSMContext):
    bot = message.bot
    users_id = message.from_user.id
    greeting_text = message.text or "Без текста"
    media_path = None

    # Получаем teacher_id из состояния
    data = await state.get_data()
    teacher_id = data.get("teacher_id")  # Извлечение teacher_id

    # Путь для хранения медиа
    media_folder = "media"

    # Проверка на тип контента и установка пути для медиа
    if message.document:
        media_path = Path(media_folder) / "documents" / message.document.file_id
        await save_file(message.document, media_path, bot)
    elif message.photo:
        media_path = Path(media_folder) / "photos" / message.photo[-1].file_id
        await save_file(message.photo[-1], media_path, bot)
    elif message.video:
        media_path = Path(media_folder) / "videos" / message.video.file_id
        await save_file(message.video, media_path, bot)

    # Сохраняем данные в базе
    await rq.save_greeting(teacher_id=teacher_id, users_id=users_id, text=greeting_text, media=str(media_path))
    await message.reply("Ваше поздравление отправлено!")
    await state.clear()



async def save_file(file, destination: Path, bot):
    # Создаем папку, если её нет
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Скачиваем файл на указанный путь
    await bot.download(file, destination)


@router.message(Command("getroot"))
async def get_admin(message: Message):

    @router.message()
    async def receive_greeting(message: types.Message):
        if message.text == "iwanttobetheverybest":
            await rq.update_rights(message.from_user.id)
            print(message)
        else:
            print(message)
            pass


@router.message(Command('all_greetings'))
async def show_all_greetings(message: types.Message):
    user = await rq.get_user(message.from_user.id)
    if not user or user.rights != 1:
        await message.reply("У вас нет прав для выполнения этой команды.")
        return

    greetings = await rq.get_all_greetings()
    for greeting in greetings:
        text = greeting.message_text
        media = greeting.media

        # Отправка текста поздравления
        await message.answer(f"Поздравление: {text}")

        # Отправка файла, если он есть
        if media:
            await message.answer_document(FSInputFile(media))
