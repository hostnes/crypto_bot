import datetime
import hashlib
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
import re
from crypto_bot.handlers.default_buttons import first_menu, global_menu_reply, global_menu
from crypto_bot.services.event_playground import event_service
from crypto_bot.states.tier_state import RegistrationState, AuthorizationState
from aiogram import Dispatcher, types

"""
ВХОД
"""

async def authorization(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(AuthorizationState.number.state)
    await callback.message.answer("Введите номер телефона: ", reply_markup=global_menu_reply())


async def get_number(msg: types.Message, state: FSMContext):
    if msg.text == 'В меню пользователя':
        await msg.answer("Choose admin action", reply_markup=first_menu())
        await state.finish()
    else:
        phone_test = msg.text
        result = re.match(r'^(\+375|80|375)(29|25|44|33)(\d{3})(\d{2})(\d{2})$', phone_test)
        if bool(result) == True:
            await state.update_data(phone_number=msg.text)
            await state.set_state(AuthorizationState.password.state)
            await msg.answer("Введите свой пароль: ")
        else:
            await msg.answer("Введите коректные данные: ")


async def get_password(msg: types.Message, state: FSMContext):
    if msg.text == 'В меню пользователя':
        await msg.answer("Choose admin action", reply_markup=first_menu())
        await state.finish()
    else:
        password = hashlib.sha256(msg.text.encode())
        await msg.delete()
        await state.update_data(password=password.hexdigest())
        authorization_data = await state.get_data()
        user = event_service.authorization(authorization_data)
        if len(user) >= 1:
            await msg.answer('Проверка', reply_markup=types.ReplyKeyboardRemove())
            await msg.answer("Главное меню", reply_markup=global_menu())
            await state.finish()
        else:
            await msg.answer("Неверно введен пароль, повторите попытку: ")


"""
РЕГИСТРАЦИЯ
"""


async def registration(callback: types.CallbackQuery, state: FSMContext):
    user_data = {'tg_id': callback.from_user.id}
    user_response = event_service.get_user_data_from_user_id(user_data)
    if len(user_response) == 0:
        await state.set_state(RegistrationState.name.state)
        await callback.message.delete()
        await callback.message.answer("Введите никнэйм: ", reply_markup=global_menu_reply())
    else:
        await callback.message.delete()
        await callback.message.answer("На этот телеграмм аккаунт уже зарегестрирован пользователь, пожалуйста войдите в свою учетную запись", reply_markup=first_menu())


async def get_name(msg: types.Message, state: FSMContext):
    if msg.text == 'В меню пользователя':
        await msg.answer("Choose admin action", reply_markup=first_menu())
        await state.finish()
    else:
        name_test = msg.text
        result = re.match(r'[a-z0-9](?:[_.]?[a-z0-9]){3,11}$', name_test)
        if bool(result) == True:
            name_data = {'name': name_test}
            user = event_service.check_register_name(name_data)
            if len(user) == 0:
                await state.update_data(name=name_test)
                await state.set_state(RegistrationState.phone.state)
                await msg.answer("Введите номер телефона: ")
            else:
                await msg.answer("Такой пользователь уже существует, введите другий никнэйм")
        else:
            await msg.answer("Введите коректные данные: ")


async def get_phone(msg: types.Message, state: FSMContext):
    if msg.text == 'В меню пользователя':
        await msg.answer("Choose admin action", reply_markup=first_menu())
        await state.finish()
    else:
        phone_test = msg.text
        result = re.match(r'^(\+375|80|375)(29|25|44|33)(\d{3})(\d{2})(\d{2})$', phone_test) # get_aut_password
        if bool(result) == True:
            phone_data = {'phone_number': phone_test}
            user = event_service.check_register_register_name(phone_data)
            if len(user) == 0:
                await state.update_data(phone_number=msg.text)
                await state.set_state(RegistrationState.password.state)
                await msg.answer("Введите пароль: ")
            else:
                await msg.answer("Такой номер телефона уже зарегестрирован")
        else:
            await msg.answer("Введите коректные данные: ")

async def get_aut_password(msg: types.Message, state: FSMContext):
    if msg.text == 'В меню пользователя':
        await msg.answer("Choose admin action", reply_markup=first_menu())
        await state.finish()
    else:
        password = hashlib.sha256(msg.text.encode())
        await msg.delete()
        await state.update_data(password=password.hexdigest())
        await state.update_data(tg_id=msg.from_user.id)
        user_data = await state.get_data()
        user = event_service.create_user(user_data)
        wallet_data = {
            "currency": "USD",
            "amount": 100000,
            "users": user['id'],
            'wallet_number': hashlib.md5(str(datetime.datetime.now()).encode()).hexdigest()
        }
        wallet = event_service.add_wallet(wallet_data)
        await msg.answer('Проверка', reply_markup=types.ReplyKeyboardRemove())
        await msg.answer("Рады приветствовать вас в этой поеботине вот наше меню:", reply_markup=global_menu())
        await state.finish()


"""
РАССЦЕНКИ
"""

async def description(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    inline_kb.add(types.InlineKeyboardButton("Return", callback_data="return"))
    await callback.message.answer(
        """
        Рады приветствовать вас в нашем Telegram боте. 
        Бот является симулятором криптобиржы, с многочисленными функциями.
        При регистрации вам даеться 10000 USD.
        Ваша задача путем перепродажи криптовалют, заработать как можно больше денег и войти в топы игроков на сервере!
        Так же вы можете отбмениваться маржой с друзьями.
        Приглашай друзей и сражайтесь вместе за величие на крипто бирже!
        Удачи!!!
        Связь: tg: @manera_a
        """, reply_markup=inline_kb)
async def return_on_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("Choose admin action", reply_markup=first_menu())
    await state.finish()
"""
ГЛАВНОЕ МЕНЮ
"""


def setup(dp: Dispatcher):
    """
    ВХОД
    """
    dp.register_message_handler(get_number, state=AuthorizationState.number)
    dp.register_message_handler(get_password, state=AuthorizationState.password)

    """
    РЕГИСТРАЦИЯ
    """
    dp.register_message_handler(get_name, state=RegistrationState.name)
    dp.register_message_handler(get_phone, state=RegistrationState.phone)
    dp.register_message_handler(get_aut_password, state=RegistrationState.password)

    """
    НАЧАЛЬНОЕ МЕНЮ
    """
    dp.register_callback_query_handler(return_on_main_menu, Text(equals="return"))
    dp.register_callback_query_handler(authorization, Text(equals="authorization"))
    dp.register_callback_query_handler(registration, Text(equals="registration"))
    dp.register_callback_query_handler(description, Text(equals="description"))
