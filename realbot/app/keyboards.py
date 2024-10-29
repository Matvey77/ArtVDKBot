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
        keyboard.add(InlineKeyboardButton(teacher.name, callback_data=f"teacher_{teacher.id}"))
    return keyboard


# Клавиатура для выбора адресата
def recipient_selection(recipients):
    keyboard = InlineKeyboardMarkup()
    for recipient in recipients:
        keyboard.add(InlineKeyboardButton(recipient.name, callback_data=f"recipient_{recipient.id}"))
    return keyboard
