from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


# Клавиатура для главного меню
def main_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Поздравления", callback_data="congratulations"))
    keyboard.add(InlineKeyboardButton("Задать вопрос", callback_data="ask_question"))
    return keyboard


# Клавиатура для выбора преподавателя
def teacher_selection(teachers):
    keyboard = InlineKeyboardMarkup()
    for teacher in teachers:
        keyboard.add(InlineKeyboardButton(teacher.full_name, callback_data=f"teacher_{teacher.id}"))
    return keyboard


# Клавиатура для выбора адресата
def recipient_selection(recipients):
    keyboard = InlineKeyboardMarkup()
    for recipient in recipients:
        keyboard.add(InlineKeyboardButton(recipient.name, callback_data=f"recipient_{recipient.id}"))
    return keyboard


# Главное меню администратора
def admin_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Редактировать преподавателя", callback_data="edit_teacher"),
            InlineKeyboardButton(text="Добавить преподавателя", callback_data="add_teacher")
        ],
        [
            InlineKeyboardButton(text="Редактировать поздравление", callback_data="edit_greeting"),
            InlineKeyboardButton(text="Добавить поздравление", callback_data="add_greeting")
        ]
    ])
    return keyboard


# Клавиатура для выбора преподавателя
def edit_teacher_keyboard(teachers):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=teacher.full_name, callback_data=f"edit_teacher_{teacher.id}")]
            for teacher in teachers
        ]
    )
    return keyboard


# Клавиатура для выбора поздравления
def edit_greeting_keyboard(greetings):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{greeting.teacher.full_name} от {greeting.sender.username}",
                callback_data=f"edit_greeting_{greeting.id}"
            )]
            for greeting in greetings
        ]
    )
    return keyboard


# Keyboard for adding a new teacher
def add_teacher_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Добавить преподавателя", callback_data="add_teacher")]
        ]
    )
    return keyboard


# Keyboard for adding a new greeting
def add_greeting_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Добавить поздравление", callback_data="add_greeting")]
        ]
    )
    return keyboard


def teacher_selection_keyboard_for_greeting(teachers):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{teacher.full_name} (teacher_{teacher.id})",
                callback_data=f"teacher_greeting_{teacher.id}"
            )]
            for teacher in teachers
        ]
    )
    return keyboard


def greeting_selection_keyboard(greetings):
    keyboard = InlineKeyboardMarkup()
    for greeting in greetings:
        keyboard.add(InlineKeyboardButton(f"{greeting.teacher.full_name} от {greeting.sender.username}",
                                        callback_data=f"greeting_{greeting.id}"))
    return keyboard


def teacher_selection_keyboard_for_question(teachers):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{teacher.full_name} (teacher_{teacher.id})",
                callback_data=f"teacher_question_{teacher.id}"  # Using "question" here
            )]
            for teacher in teachers
        ]
    )
    return keyboard
