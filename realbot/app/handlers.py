from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from pathlib import Path
import os
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


@router.message(Form.waiting_for_greeting_text,
                F.content_type.in_(['text', 'document', 'photo', 'video', 'audio', 'voice']))
async def receive_greeting(message: types.Message, state: FSMContext):
    bot = message.bot
    users_id = message.from_user.id
    greeting_text = message.text or message.caption or "Без текста"
    media_path = None
    media_folder = "media"

    # Получаем teacher_id из состояния
    data = await state.get_data()
    teacher_id = data.get("teacher_id")

    # Проверка на тип контента и установка пути для медиа с сохранением формата
    if message.document:
        file_extension = Path(
            message.document.file_name).suffix if message.document.file_name else '.bin'
        media_path = Path(media_folder) / "documents" / f"{message.document.file_id}{file_extension}"
        try:
            await save_file(message.document, media_path, bot)
        except Exception as e:
            await message.reply(f"Ошибка при сохранении файла: {e}\n Отправьте поздравление заново")
            return
    elif message.photo:
        media_path = Path(media_folder) / "photos" / f"{message.photo[-1].file_id}.jpg"  # Сохраняем как .jpg
        try:
            await save_file(message.photo[-1], media_path, bot)
        except Exception as e:
            await message.reply(f"Ошибка при сохранении файла: {e}\n Отправьте поздравление заново")
            return
    elif message.video:
        file_extension = Path(
            message.video.file_name).suffix if message.video.file_name else '.mp4'
        media_path = Path(media_folder) / "videos" / f"{message.video.file_id}{file_extension}"
        try:
            await save_file(message.video, media_path, bot)
        except Exception as e:
            await message.reply(f"Ошибка при сохранении файла: {e}\n Отправьте поздравление заново")
            return
    elif message.audio:
        media_path = Path(media_folder) / "audios" / f"{message.audio.file_id}.mp3"  # Сохраняем как .mp3
        try:
            await save_file(message.audio, media_path, bot)
        except Exception as e:
            await message.reply(f"Ошибка при сохранении файла: {e}\n Отправьте поздравление заново")
            return
    elif message.voice:
        media_path = Path(media_folder) / "voices" / f"{message.voice.file_id}.ogg"  # Сохраняем как .ogg
        try:
            await save_file(message.voice, media_path, bot)
        except Exception as e:
            await message.reply(f"Ошибка при сохранении файла: {e}\n Отправьте поздравление заново")
            return
    else:
        # Если тип контента не распознан
        if message.text is None:
            await message.reply("Формат файла не поддерживается. Пожалуйста, отправьте файл в подходящем формате.")
            await state.clear()
            pass

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
        else:
            pass


@router.message(Command('all_greetings'))
async def show_all_greetings(message: types.Message):
    user = await rq.get_user(message.from_user.id)
    if not user or user.rights != 1:
        await message.reply("У вас нет прав для выполнения этой команды.")
        return

    greetings = await rq.get_all_greetings()
    for greeting in greetings:
        sender_name = greeting.sender.username if greeting.sender else "Неизвестный отправитель"
        recipient_name = greeting.teacher.full_name if greeting.teacher else "Неизвестный учитель"
        text = greeting.message_text
        media = greeting.media

        # Отправка информации о поздравлении
        await message.answer(
            f"Поздравление от {sender_name} для {recipient_name}:\n\n{text}"
        )

        # Отправка файла, если он существует и путь не пустой
        if media and os.path.isfile(media):  # Убедитесь, что путь существует
            await message.answer_document(FSInputFile(media))
        else:
            await message.answer("Файл не найден или отсутствует.")




