from aiogram import types
from aiogram.types import KeyboardButton


def global_menu():
    menu_kb = types.InlineKeyboardMarkup(row_width=1)
    menu_kb.add(types.InlineKeyboardButton("Рынок", callback_data="market"))
    menu_kb.add(types.InlineKeyboardButton("Перевод", callback_data="translation"))
    menu_kb.add(types.InlineKeyboardButton("Kошельки", callback_data="wallets"))
    menu_kb.add(types.InlineKeyboardButton("История транзакций", callback_data="transaction_history"))
    menu_kb.add(types.InlineKeyboardButton("Основные", callback_data="main"))
    # menu_kb.add(types.InlineKeyboardButton("Вопросы и пожелания", callback_data="questions"))
    return menu_kb


def global_menu_reply():
    reply_kb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    reply_kb.add(KeyboardButton('В меню пользователя'))
    return reply_kb


def first_menu():
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    inline_kb.add(types.InlineKeyboardButton("Вход", callback_data="authorization"))
    inline_kb.add(types.InlineKeyboardButton("Регистрация", callback_data="registration"))
    inline_kb.add(types.InlineKeyboardButton("Описание", callback_data="description"))
    return inline_kb


def amount_reply():
    reply_kb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    reply_kb.add(KeyboardButton('Всё'))
    reply_kb.add(KeyboardButton('25%'))
    reply_kb.add(KeyboardButton('50%'))
    reply_kb.add(KeyboardButton('75%'))
    reply_kb.add(KeyboardButton('В меню пользователя'))


    return reply_kb
