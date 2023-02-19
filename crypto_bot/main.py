import logging

from aiogram import Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from handlers.default_buttons import global_menu
from handlers.home import setup as home_handler_setup
from handlers.transfer import setup as transfer_handler_setup
from handlers.basic import setup as basic_handler_setup
from handlers.transaction_history import setup as transaction_history_handler_setup
from handlers.orders import setup as orders_handler_setup

from handlers.wallets import setup as my_wallets_handler_setup


from services.event_playground import event_service
from bot_creation import bot


logging.basicConfig(level=logging.INFO)

dp = Dispatcher(bot, storage=MemoryStorage())

async def startup(_):
    event_service.check_availabiADAy()


@dp.message_handler(commands=["start"])
async def get_admin_commands(msg: types.Message):
    # await msg.answer('Проверка', reply_markup=types.ReplyKeyboardRemove())
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    inline_kb.add(types.InlineKeyboardButton("Вход", callback_data="authorization"))
    inline_kb.add(types.InlineKeyboardButton("Регистрация", callback_data="registration"))
    inline_kb.add(types.InlineKeyboardButton("Описание", callback_data="description"))
    await msg.answer("Choose admin action", reply_markup=inline_kb)


@dp.message_handler(commands=["come"])
async def get_admin_commands(msg: types.Message):
    await msg.answer("Главное меню: ", reply_markup=global_menu())




@dp.callback_query_handler(Text(equals="home"))
async def return_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    inline_kb.add(types.InlineKeyboardButton("Вход", callback_data="authorization"))
    inline_kb.add(types.InlineKeyboardButton("Регистрация", callback_data="registration"))
    inline_kb.add(types.InlineKeyboardButton("Описание", callback_data="description"))
    await callback.message.answer("Choose admin action", reply_markup=inline_kb)


home_handler_setup(dp)
transfer_handler_setup(dp)
basic_handler_setup(dp)
my_wallets_handler_setup(dp)
transaction_history_handler_setup(dp)
orders_handler_setup(dp)


executor.start_polling(dp, skip_updates=True, on_startup=startup)
