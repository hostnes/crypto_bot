import hashlib

from aiogram.dispatcher.filters import Text
from aiogram.types import KeyboardButton, ReplyKeyboardRemove
import requests

from crypto_bot.handlers.default_buttons import global_menu, global_menu_reply, amount_reply
from aiogram.dispatcher import FSMContext

from crypto_bot.services.event_playground import event_service
from crypto_bot.states.tier_state import TransferState
from aiogram import types, Dispatcher

global_currency ={
    'USD': 1,
    'BTC': 22842,
    'ETH': 1615,
    'BNB': 314,
    'XRP': 0.42,
    'DOGE': 0.08,
    'ADA': 0.37,
}

async def chose_transaction(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    menu_kb = types.InlineKeyboardMarkup(row_width=1)
    menu_kb.add(types.InlineKeyboardButton("Перевод по айди пользователя", callback_data="transfer_from_user_id"))
    menu_kb.add(types.InlineKeyboardButton("Перевод по номеру кошелька", callback_data="transfer_from_wallet_number"))
    menu_kb.add(types.InlineKeyboardButton("В меня пользователя", callback_data='return_user'))
    await callback.message.answer("Каким способом будете переводить?", reply_markup=menu_kb)


async def transfer_wallet_number(callback: types.CallbackQuery, state: FSMContext):
        id = callback.from_user.id
        user_data = {'tg_id': id}
        users_response = event_service.get_user_data_from_user_id(user_data)
        await state.update_data(sender_id=users_response[0]['id'])
        await state.update_data(sender=users_response[0]['name'])

        await state.update_data(valid_password=users_response[0]['password'])
        await state.update_data(sender_tier=users_response[0]['tier'])
        await state.update_data(sender_tg_id=id)
        for i in users_response:
            user_data = {'users': i['id']}
            await state.update_data(sender_id=i['id'])
            await state.update_data(sender=i['name'])

        users_response = event_service.find_wallet_currency(user_data)

        await callback.message.delete()
        inline_kb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)

        for i in users_response:
            inline_kb.add(
                types.KeyboardButton(f"{i['currency']} - {i['amount']}")
            )
        inline_kb.add(types.KeyboardButton("В меню пользователя"))
        await callback.message.answer("С какого кошелька будете переводить?", reply_markup=inline_kb)
        await state.set_state(TransferState.sender_currency_wallet)


async def sender_amount_wallet(message: types.Message, state: FSMContext):
    sender_currency = message.text
    currency = ["USD", "BTC", "ETH", "ADA", "BNB", "XRP", "DOGE"]
    qwe = False
    if sender_currency == "В меню пользователя":
        await state.finish()
        await message.answer("Транзакция прервана", reply_markup=types.ReplyKeyboardRemove())
        await message.answer("Меню пользователя", reply_markup=global_menu())
    else:
        sender_currency = sender_currency.split(" ")[0]
        for i in currency:
            if i == sender_currency:
                sender_amount = float(message.text.split(" ")[2])
                if sender_amount == 0:
                    await message.answer(f"У вас на балансе 0.0 {sender_currency}, выберите другой кошелек для перевода: ")
                    qwe = True

                else:
                    get_data = await state.get_data()
                    qwe = True
                    query_params = dict(currency=sender_currency, user=get_data['sender_id'])
                    response = requests.get(f"http://localhost:8000/api/walletid/", params=query_params)
                    await state.update_data(sender_wallet_id=response.json()[0]['id'])
                    await state.update_data(sender_currency=sender_currency)
                    await state.update_data(wallet_sender_amount=sender_amount)
                    await state.set_state(TransferState.sender_amount_wallet)
                    await message.answer("Сколько хотите перевести?", reply_markup=amount_reply())
            else:
                pass
        if qwe == False:
            await message.answer("Такого варианта ответа нету: ")


async def get_amount_wallet(message: types.Message, state: FSMContext):
    get_data = await state.get_data()
    interest = {'25%': 0.25, '50%': 0.5, '75%': 0.75, 'Всё': 1}
    qwe = False
    if message.text == 'В меню пользователя':
        await message.answer("Транзакция прервана", reply_markup=types.ReplyKeyboardRemove())
        await message.answer("Меню пользователя: ", reply_markup=global_menu())
        await state.finish()
    else:
        for key, value in interest.items():
            if key == message.text:
                send_amount = get_data['wallet_sender_amount'] * value
                await state.update_data(new_sender_amount=float("{0:.3f}".format(get_data['wallet_sender_amount'] - send_amount)))
                await state.update_data(send_amount=send_amount)
                await state.set_state(TransferState.wallet_number.state)
                await message.answer(f'Введите номер кошелька: ', reply_markup=types.ReplyKeyboardRemove())
                qwe = True
                break

        if qwe == False:
            try:
                send_amount = float(message.text)
                if float(message.text) <= get_data['wallet_sender_amount']:
                    await state.update_data(new_sender_amount=float("{0:.3f}".format(get_data['wallet_sender_amount'] - send_amount)))
                    await state.update_data(send_amount=send_amount)
                    await message.answer(f'Введите номер кошелька: ', reply_markup=types.ReplyKeyboardRemove())
                    await state.set_state(TransferState.wallet_number.state)
                else:
                    await message.answer('Недостаточно средств')
            except:
                await message.answer("Введите число: ")



async def get_wallet_number(message: types.Message, state: FSMContext):
    wallet_number = message.text
    query_params = dict(wallet_number=wallet_number)
    response = requests.get(f"http://localhost:8000/api/walletid/", params=query_params)

    if len(response.json()) == 1:
        await state.update_data(recipient_wallet_id=response.json()[0]['id'])
        await state.update_data(recipient_currency=response.json()[0]['currency'])
        await state.update_data(recipient_amount=response.json()[0]['amount'])
        user_response = requests.get(f"http://localhost:8000/api/user/{response.json()[0]['users']}")
        await state.update_data(recipient=user_response.json()['name'])
        await state.set_state(TransferState.password)
        await message.answer('Для подтверждения транзакции введите пароль: ')

    else:
        await message.answer('Не действительный номер кошелька, повторите попытку: ')


async def get_password_tr(message: types.Message, state: FSMContext):
    password = hashlib.sha256(message.text.encode())
    await message.delete()
    get_data = await state.get_data()
    tier_commission = {'U': 0.1, 'B': 0.07, 'S': 0.05, 'G': 0.03, 'A': 0}
    if message.text == 'В меню пользователя':
        await message.answer("Меню пользователя: ", reply_markup=global_menu())
        await state.finish()
    else:
        hash_password = hashlib.sha256(message.text.encode()).hexdigest()
        if get_data['valid_password'] == hash_password:
            usd_recipient = global_currency[f'{get_data["sender_currency"]}'] * get_data['send_amount']
            res_currency_amount = global_currency[f'{get_data["recipient_currency"]}']
            for key, value in tier_commission.items():
                if key == get_data['sender_tier']:
                    commission = usd_recipient * value / res_currency_amount
                    await state.update_data(commission=float("{0:.4f}".format(commission)))
                    usd_recipient = usd_recipient * (1 - value)

            new_recipient_amount = usd_recipient / res_currency_amount
            new_recipient_amount = new_recipient_amount + get_data['recipient_amount']
            await state.update_data(new_recipient_amount=float("{0:.4f}".format(new_recipient_amount)))
            await state.update_data(received_amount=float("{0:.4f}".format(usd_recipient / res_currency_amount)))
            wallet_data = await state.get_data()

            users_response_wallet = event_service.patch_wallet(wallet_data)
            users_response_wallet = event_service.post_transactions(wallet_data)
            await message.answer("Транзакция произошла успешно!", reply_markup=types.ReplyKeyboardRemove())
            await message.answer("Меню пользователя: ", reply_markup=global_menu())
            await state.finish()
        else:
            await message.answer('Не правильный пароль, попробуйте введите еще раз: ')




async def translation_user_id(callback: types.CallbackQuery, state: FSMContext):
    id = callback.from_user.id
    user_data = {'tg_id': id}
    users_response = event_service.get_user_data_from_user_id(user_data)
    await state.update_data(sender_tg_id=id)
    for i in users_response:
        user_data = {'users': i['id']}
        await state.update_data(sender_id=i['id'])
        await state.update_data(sender=i['name'])
        await state.update_data(sender_tg_id=callback.from_user.id)

    users_response = event_service.find_wallet_currency(user_data)

    await callback.message.delete()
    inline_kb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)

    for i in users_response:
        inline_kb.add(
            types.KeyboardButton(f"{i['currency']} - {i['amount']}")
        )
    inline_kb.add(types.KeyboardButton("В меню пользователя"))
    await callback.message.answer("С какого кошелька будете переводить?", reply_markup=inline_kb)
    await state.set_state(TransferState.sender_currency)


async def sender_currency(message: types.Message, state: FSMContext):
    sender_currency = message.text
    currency = ["USD", "BTC", "ETH", "ADA", "BNB", "XRP", "DOGE"]
    qwe = False
    if sender_currency == "В меню пользователя":
        await state.finish()
        await message.answer("Транзакция прервана", reply_markup=types.ReplyKeyboardRemove())
        await message.answer("Меню пользователя", reply_markup=global_menu())
    else:
        sender_currency = sender_currency.split(" ")[0]
        for i in currency:
            if i == sender_currency:
                sender_amount = float(message.text.split(" ")[2])
                if sender_amount == 0:
                    await message.answer(f"У вас на балансе 0.0 {sender_currency}, выберите другой кошелек для перевода: ")
                    qwe = True
                else:
                    qwe = True
                    await state.update_data(sender_currency=sender_currency)
                    await state.set_state(TransferState.tg_id.state)
                    await message.answer("Введите айди получателя:", reply_markup=global_menu_reply())
            else:
                pass
        if qwe == False:
            await message.answer("Такого варианта ответа нету: ")



async def get_transfer_id(message: types.Message, state: FSMContext):
    if message.text == 'В меню пользователя':
        await message.answer("Меню пользователя: ", reply_markup=global_menu())
        await state.finish()
    else:
        id = message.text
        await state.update_data(sender_tg_id=id)
        recipient_data = {'tg_id': id}
        users_response = event_service.get_user_data_from_user_id(recipient_data)
        for i in users_response:
            user_data = {'users': i['id']}
            await state.update_data(recipient_id=i['id'])
            await state.update_data(recipient=i['name'])
        await state.update_data(recipient_tg_id=message.from_user.id)
        if len(users_response) >= 1:
            users_response = event_service.find_wallet_currency(user_data)
            reply_kb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            for i in users_response:
                reply_kb.add(KeyboardButton(f'{i["currency"]}'))
            reply_kb.add(KeyboardButton("В меню пользователя"))
            get_data = await state.get_data()
            user_data = {'currency': get_data['sender_currency'], 'users': get_data['sender_id']}
            sender_response = event_service.find_wallet(user_data)
            for i in sender_response:
                await state.update_data(sender_wallet_id=i['id'])
                await state.update_data(sender_amount=i['amount'])
            await state.set_state(TransferState.choose_wallet.state)
            await message.answer("На какой кошелек будете переводить?", reply_markup=reply_kb)
        else:
            await message.answer("Пользователя с таким айди нету, пожалуйста введите коректный айди: ", reply_markup=global_menu_reply())


async def recipient_currency(message: types.Message, state: FSMContext):
    get_data = await state.get_data()
    recipient_currency = message.text
    currency = ["USD", "BTC", "ETH", "ADA", "BNB", "XRP", "DOGE"]
    qwe = False
    if recipient_currency == "В меню пользователя":
        await state.finish()
        await message.answer("Транзакция прервана", reply_markup=types.ReplyKeyboardRemove())
        await message.answer("Меню пользователя", reply_markup=global_menu())

    elif get_data['sender_currency'] == recipient_currency and get_data['sender_tg_id'] == str(get_data['recipient_tg_id']):
        await message.answer("Вы не можете перевести самому себе одну и ту же валюту")
        await message.answer("На какой кошелек будете переводить?")
        await state.set_state(TransferState.choose_wallet.state)

    else:
        for i in currency:
            if i == recipient_currency:
                await state.set_state(TransferState.amount.state)
                await state.update_data(recipient_currency=recipient_currency)
                get_data = await state.get_data()
                await message.answer(
                    f"Сколько вы хотите перевести?\nУ вас на балансе {get_data['sender_amount']} {get_data['sender_currency']}",
                    reply_markup=amount_reply())
                user_data = {'currency': recipient_currency, 'users': get_data['recipient_id']}
                recipient_response = event_service.find_wallet(user_data)
                for i in recipient_response:
                    await state.update_data(recipient_currency=recipient_currency)
                    await state.update_data(recipient_wallet_id=i['id'])
                    await state.update_data(recipient_amount=i['amount'])
                qwe = True

        if qwe == False:
            await message.answer("Такого варианта ответа нету")


async def get_amount(message: types.Message, state: FSMContext):
    get_data = await state.get_data()
    interest = {'25%': 0.25, '50%': 0.5, '75%': 0.75, 'Всё': 1}
    qwe = False
    if message.text == 'В меню пользователя':
        await message.answer("Меню пользователя: ", reply_markup=global_menu())
        await state.finish()
    else:
        for key, value in interest.items():
            if key == message.text:
                send_amount = get_data['sender_amount'] * value
                await state.update_data(new_recipient_amount=get_data['recipient_amount'] + send_amount)
                await state.update_data(new_sender_amount=float("{0:.3f}".format(get_data['sender_amount'] - send_amount)))
                await state.update_data(send_amount=send_amount)
                await state.set_state(TransferState.password.state)
                await message.answer('Для подтверждения транзакции введите пароль: ')
                qwe = True
                break

        if qwe == False:
            try:
                send_amount = float(message.text)
                if float(message.text) <= get_data['sender_amount']:
                    await state.update_data(new_recipient_amount=get_data['recipient_amount'] + send_amount)
                    await state.update_data(new_sender_amount=float("{0:.3f}".format(get_data['sender_amount'] - send_amount)))
                    await state.update_data(send_amount=send_amount)
                    await message.answer('Для подтверждения транзакции введите пароль: ', reply_markup=types.ReplyKeyboardRemove())
                    await state.set_state(TransferState.password.state)
                    user_data = {'tg_id': message.from_user.id}
                    users_response = event_service.check_transaction_password(user_data)
                    await state.update_data(valid_password=users_response[0]['password'])
                    await state.update_data(sender_tier=users_response[0]['tier'])
                else:
                    await message.answer('Недостаточно средств')
                    await message.answer(f'Для перевода доступно {get_data["sender_amount"]} {get_data["sender_currency"] }\nВведите сумму которую хотите переслать: ')
            except:
                await message.answer("Введите число: ")


async def return_user(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.delete()
    await callback.message.answer("Главное меню: ", reply_markup=global_menu())


def setup(dp: Dispatcher):
    """
    ПЕРЕВОД
    """
    dp.register_callback_query_handler(chose_transaction, Text(equals="translation"))
    dp.register_callback_query_handler(return_user, Text(equals="return_user"))

    dp.register_callback_query_handler(transfer_wallet_number, Text(equals="transfer_from_wallet_number"))
    dp.register_message_handler(sender_amount_wallet, state=TransferState.sender_currency_wallet)
    dp.register_message_handler(get_amount_wallet, state=TransferState.sender_amount_wallet)
    dp.register_message_handler(get_wallet_number, state=TransferState.wallet_number)



    dp.register_callback_query_handler(translation_user_id, Text(equals="transfer_from_user_id"))


    dp.register_message_handler(sender_currency, state=TransferState.sender_currency)
    dp.register_message_handler(get_transfer_id, state=TransferState.tg_id)
    dp.register_message_handler(recipient_currency, state=TransferState.choose_wallet)
    dp.register_message_handler(get_amount, state=TransferState.amount)
    dp.register_message_handler(get_password_tr, state=TransferState.password)
