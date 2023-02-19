import hashlib
import re

from aiogram.dispatcher.filters import Text
from crypto_bot.handlers.default_buttons import first_menu, global_menu, global_menu_reply
from aiogram.dispatcher import FSMContext

from crypto_bot.services.event_playground import event_service
from aiogram import types, Dispatcher

from crypto_bot.states.tier_state import OutState


async def basic(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    id = callback.from_user.id
    user_data = {'tg_id': id}
    users_response = event_service.get_user_data_from_user_id(user_data)
    for i in users_response:
        clan = i['clan']
        # if clan == None:
        #     clan = "Вы не состоите в клане"
        date = i['data']
        date = date.split("T")
        tier = i['tier']
        if tier == "U":
            tier = "User"
        elif tier == "B":
            tier = "Bronze"
        elif tier == "S":
            tier = "Silver"
        elif tier == "G":
            tier = "Gold"
        elif tier == "A":
            tier = "Admin"
        menu_kb = types.InlineKeyboardMarkup(row_width=1)
        menu_kb.add(types.InlineKeyboardButton("Измененить никнэйм", callback_data="сhange_nickname"))
        menu_kb.add(types.InlineKeyboardButton("Измененить пароля", callback_data="сhange_password"))
        menu_kb.add(types.InlineKeyboardButton("Выход", callback_data="out"))
        menu_kb.add(types.InlineKeyboardButton("В меня пользователя", callback_data='return_user'))
        await callback.message.answer(f"Ваш айди - {i['tg_id']}\n"
                                      f"Ваш nickname - {i['name']}\n"
                                      f"Ваш статус - {tier}\n"
                                      f"Дата регистрации - {date[0]}  {date[1].split('.')[0]}\n",
                                      reply_markup=menu_kb
                                      )


async def out(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(OutState.out.state)
    await callback.message.answer("Для выхода из учетной записи вам требуется ввести пароль.\nВведите пароль: ", reply_markup=global_menu_reply())


async def out_password(message: types.Message, state: FSMContext):
    if message.text == 'В меню пользователя':
        await message.answer("Choose admin action", reply_markup=first_menu())
        await state.finish()
    else:
        await message.delete()
        password = hashlib.sha256(message.text.encode())
        user_data = {'tg_id': message.from_user.id}
        users_response = event_service.get_user_data_from_user_id(user_data)
        for i in users_response:
            correct_password = i['password']
        if password.hexdigest() == correct_password:
            await message.answer("Вы вышли из учетной записи. До скорых встреч")
            await state.finish()
            await message.answer("Choose admin action", reply_markup=first_menu())
        else:
            await message.answer("Не верный пароль. \nПожалуйста введите коректный пароль:")


async def return_user(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.delete()
    await callback.message.answer("Главное меню: ", reply_markup=global_menu())


async def сhange_password(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(OutState.niew_password.state)
    inline_kb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    inline_kb.add(types.KeyboardButton("В меню пользователя"))
    await callback.message.answer("Введите новый пароль: ", reply_markup=inline_kb)


async def сhange_password_encode(message: types.Message, state: FSMContext):
    if message.text == 'В меню пользователя':
        await message.answer("Меню пользователя", reply_markup=global_menu())
        await state.finish()
    else:
        await message.delete()
        password = hashlib.sha256(message.text.encode())
        await state.update_data(niew_password= password.hexdigest())
        await state.set_state(OutState.password.state)
        await message.answer("Введите старый пароль: ")

async def niew_password(message: types.Message, state: FSMContext):
    if message.text == 'В меню пользователя':
        await message.answer("Меню пользователя", reply_markup=global_menu())
        await state.finish()
    else:
        await message.delete()
        password_hash = hashlib.sha256(message.text.encode())
        user_data = {'tg_id': message.from_user.id}
        users_response = event_service.get_user_data_from_user_id(user_data)
        for i in users_response:
            user_id = i['id']
            correct_password = i['password']
        if password_hash.hexdigest() == correct_password:
            get_data = await state.get_data()
            user_data = {'password': f"{get_data['niew_password']}", 'user_id': user_id}
            response = event_service.patch_user(user_data)
            await state.finish()
            await message.answer("Пароль изменен!", reply_markup=types.ReplyKeyboardRemove())
            await message.answer("Меню пользователя", reply_markup=global_menu())
        else:
            await message.answer("Не верный пароль. \nПожалуйста введите коректный пароль:")


async def сhange_nickname(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(OutState.niew_nickname.state)
    inline_kb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True,  one_time_keyboard=True)
    inline_kb.add(types.KeyboardButton("В меню пользователя"))
    await callback.message.answer("Введите новый никнэйм: ", reply_markup=global_menu_reply())


async def сhange_nickname_add(message: types.Message, state: FSMContext):
    if message.text == 'В меню пользователя':
        await message.answer("Меню пользователя", reply_markup=global_menu())
        await state.finish()
    else:
        nickname = message.text
        message
        result = re.match(r'[a-z0-9](?:[_.]?[a-z0-9]){3,11}$', nickname)
        if bool(result) == True:
            name_data = {'name': nickname}
            user = event_service.check_register_name(name_data)
            if len(user) == 0:
                await state.update_data(niew_nickname=nickname)
                await message.answer("Введите пароль: ")
                await state.set_state(OutState.password_nickname.state)
            else:
                await message.answer("Этот никнэйм уже занят. Введите другой никнэйм: ")
        else:
            await message.answer("Введите коректные данные: ")


async def niew_nickname(message: types.Message, state: FSMContext):
    if message.text == 'В меню пользователя':
        await message.answer("Меню пользователя", reply_markup=global_menu())
        await state.finish()
    else:
        await message.delete()
        password_hash = hashlib.sha256(message.text.encode())
        user_data = {'tg_id': message.from_user.id}
        users_response = event_service.get_user_data_from_user_id(user_data)
        for i in users_response:
            user_id = i['id']
            correct_password = i['password']
        if password_hash.hexdigest() == correct_password:
            get_data = await state.get_data()
            user_data = {'name': f"{get_data['niew_nickname']}", 'user_id': user_id}
            response = event_service.patch_user(user_data)
            await state.finish()
            await message.answer("Никнэйм изменен!", reply_markup=types.ReplyKeyboardRemove())
            await message.answer("Меню пользователя", reply_markup=global_menu())
        else:
            await message.answer("Не верный пароль. \nПожалуйста введите коректный пароль:")


def setup(dp: Dispatcher):
    """
    ОСНОВНЫЕ
    """
    dp.register_message_handler(out_password, state=OutState.out)

    dp.register_callback_query_handler(return_user, Text(equals="return_user"))

    dp.register_callback_query_handler(basic, Text(equals="main"))
    dp.register_callback_query_handler(out, Text(equals="out"))

    dp.register_callback_query_handler(сhange_password, Text(equals="сhange_password"))
    dp.register_message_handler(сhange_password_encode, state=OutState.niew_password)
    dp.register_message_handler(niew_password, state=OutState.password)

    dp.register_callback_query_handler(сhange_nickname, Text(equals="сhange_nickname"))
    dp.register_message_handler(сhange_nickname_add, state=OutState.niew_nickname)
    dp.register_message_handler(niew_nickname, state=OutState.password_nickname)


