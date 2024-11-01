from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, FSInputFile, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from pathlib import Path
import os
from app.database import requests as rq
from app.keyboards import admin_menu, edit_teacher_keyboard, edit_greeting_keyboard, \
    teacher_selection_keyboard_for_greeting, greeting_selection_keyboard, teacher_selection_keyboard_for_question

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
async def choose_teacher(callback: CallbackQuery):
    teachers = await rq.get_teachers()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=teacher.full_name, callback_data=f"teacher_{teacher.id}")]
                         for teacher in teachers]
    )
    await callback.message.answer("Выберите преподавателя:", reply_markup=keyboard)


@router.callback_query(F.data == "questions")
async def choose_teacher_for_question(callback: CallbackQuery, state: FSMContext):
    teachers = await rq.get_teachers()
    await callback.message.answer("Выберите преподавателя, которому хотите задать вопрос:",
                                    reply_markup=teacher_selection_keyboard_for_question(teachers))
    await state.set_state(EditStates.choosing_teacher_for_question)


@router.callback_query(F.data.startswith("teacher_question_"))
async def send_teacher_data(callback: CallbackQuery, state: FSMContext):
    _, _, teacher_id_str = callback.data.split("_")
    try:
        teacher_id = int(teacher_id_str)
    except ValueError:
        await callback.message.answer("Ошибка: неверный ID преподавателя.")
        return
    teacher = await rq.get_teacher_by_id(teacher_id)
    await callback.message.answer(
        f"Контакты преподавателя:\n\n"
        f"Email: {teacher.email}\n"
        f"Telegram: @{teacher.telegram_username}"
    )
    await state.clear()


@router.callback_query(F.data.startswith("teacher_"))
async def send_greeting(callback: CallbackQuery, state: FSMContext):
    _, teacher_id_str = callback.data.split("_")
    try:
        teacher_id = int(teacher_id_str)
    except ValueError:
        await callback.message.answer("Ошибка: неверный ID преподавателя.")
        return
    await callback.message.answer("Отправьте текст поздравления:")
    await state.update_data(teacher_id=teacher_id)
    await state.set_state(Form.waiting_for_greeting_text)


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
    try:
        if message.document:
            file_extension = Path(message.document.file_name).suffix or '.bin'
            media_path = Path(media_folder) / "documents" / f"{message.document.file_id}{file_extension}"
            await save_file(message.document, media_path, bot)
        elif message.photo:
            media_path = Path(media_folder) / "photos" / f"{message.photo[-1].file_id}.jpg"
            await save_file(message.photo[-1], media_path, bot)
        elif message.video:
            file_extension = Path(message.video.file_name).suffix or '.mp4'
            media_path = Path(media_folder) / "videos" / f"{message.video.file_id}{file_extension}"
            await save_file(message.video, media_path, bot)
        elif message.audio:
            media_path = Path(media_folder) / "audios" / f"{message.audio.file_id}.mp3"
            await save_file(message.audio, media_path, bot)
        elif message.voice:
            media_path = Path(media_folder) / "voices" / f"{message.voice.file_id}.ogg"
            await save_file(message.voice, media_path, bot)
    except Exception as e:
        await message.reply(f"Ошибка при сохранении файла: {e}. Отправьте поздравление заново.")
        return

    # Если медиа отсутствует и текст тоже пустой, отправляем предупреждение
    if not greeting_text and not media_path:
        await message.reply("Формат файла не поддерживается. Пожалуйста, отправьте файл в подходящем формате.")
        await state.clear()
        return

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


class EditStates(StatesGroup):
    # ... (your existing states)
    adding_teacher = State()  # New state for adding teachers
    adding_greeting = State()  # New state for adding greetings
    editing_teacher = State()  # New state for editing teachers
    editing_greeting = State()  # New state for editing greetings
    choosing_teacher_for_question = State() # New state for editing greetings


@router.message(Command("admin"))
async def admin_menu_command(message: Message):
    user = await rq.get_user(message.from_user.id)
    if user and user.rights:
        await message.answer("Выберите действие:", reply_markup=admin_menu())
    else:
        await message.reply("У вас нет прав для выполнения этой команды.")


@router.callback_query(lambda c: c.data == "edit_teacher")
async def edit_teacher_list(callback: CallbackQuery, state: FSMContext):
    teachers = await rq.get_teachers()
    await callback.message.answer("Выберите преподавателя для редактирования:",
                                 reply_markup=edit_teacher_keyboard(teachers))
    await state.set_state(EditStates.editing_teacher)


@router.callback_query(lambda c: c.data.startswith("edit_teacher_"))
async def start_edit_teacher(callback: CallbackQuery, state: FSMContext):
    teacher_id = int(callback.data.split("_")[2])
    await callback.message.answer("Введите новые данные для преподавателя (Имя, E-mail, Telegram):")
    await state.update_data(teacher_id=teacher_id)


@router.message(EditStates.editing_teacher)
async def save_teacher_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    teacher_id = data['teacher_id']
    teacher_data = message.text.split(",")
    if len(teacher_data) == 3:
        await rq.update_teacher(teacher_id, teacher_data[0], teacher_data[1], teacher_data[2])
        await message.reply("Данные преподавателя успешно обновлены!")
    else:
        await message.reply("Неверный формат данных. Попробуйте снова.")
    await state.clear()


@router.callback_query(lambda c: c.data == "add_teacher")
async def add_teacher(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите данные для нового преподавателя (Имя, E-mail, Telegram):")
    await state.set_state(EditStates.adding_teacher)


@router.message(EditStates.adding_teacher)
async def save_new_teacher(message: Message, state: FSMContext):
    teacher_data = message.text.split(",")
    if len(teacher_data) == 3:
        await rq.add_teacher(teacher_data[0], teacher_data[1], teacher_data[2])
        await message.reply("Преподаватель успешно добавлен!")
    else:
        await message.reply("Неверный формат данных. Попробуйте снова.")
    await state.clear()


@router.callback_query(lambda c: c.data == "edit_greeting")
async def edit_greeting_list(callback: CallbackQuery, state: FSMContext):
    greetings = await rq.get_all_greetings()  # Получаем список поздравлений
    await callback.message.answer("Выберите поздравление для редактирования:",
                                 reply_markup=edit_greeting_keyboard(greetings))
    await state.set_state(EditStates.editing_greeting)


@router.callback_query(lambda c: c.data.startswith("edit_greeting_"))
async def start_edit_greeting(callback: CallbackQuery, state: FSMContext):
    greeting_id = int(callback.data.split("_")[2])
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Удалить медиа", callback_data=f"remove_media_{greeting_id}")]
        ]
    )
    await callback.message.answer("Введите новый текст для поздравления или нажмите \"Удалить медиа\" чтобы удалить медиа:", reply_markup=keyboard)
    await state.update_data(greeting_id=greeting_id)


@router.message(EditStates.editing_greeting)
async def save_greeting_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    greeting_id = data['greeting_id']
    new_text = message.text
    await rq.update_greeting_text(greeting_id, new_text)
    await message.reply("Текст поздравления успешно обновлен!")
    await state.clear()


@router.callback_query(lambda c: c.data == "add_greeting")
async def add_admin_greeting(callback: CallbackQuery, state: FSMContext):
    teachers = await rq.get_teachers()  # Получаем список преподавателей
    await callback.message.answer("Выберите преподавателя, для которого добавить поздравление:",
                                 reply_markup=teacher_selection_keyboard_for_greeting(teachers))  # Передаем teachers
    await state.set_state(EditStates.adding_greeting)


@router.callback_query(lambda c: c.data.startswith("teacher_greeting_"))
async def choose_teacher_for_greeting(callback: CallbackQuery, state: FSMContext):
    teacher_id = int(callback.data.split("_")[1])
    await state.update_data(teacher_id=teacher_id)
    await callback.message.answer("Введите текст поздравления:")
    await state.set_state(EditStates.adding_greeting)


@router.message(EditStates.adding_greeting)
async def save_new_admin_greeting(message: Message, state: FSMContext):
    data = await state.get_data()
    teacher_id = data['teacher_id']
    user_id = message.from_user.id
    new_text = message.text
    await rq.add_admin_greeting(teacher_id, new_text, user_id)  # Add new greeting to the database
    await message.reply("Поздравление успешно добавлено!")
    await state.clear()


@router.callback_query(lambda c: c.data.startswith("remove_media_"))
async def remove_media_from_greeting(callback: CallbackQuery, state: FSMContext):
    greeting_id = int(callback.data.split("_")[2])
    await rq.update_greeting_media(greeting_id, None)  # Set media to None
    await callback.message.answer("Медиа удалено из поздравления.")
    await state.clear()



