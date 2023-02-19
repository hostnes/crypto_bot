import requests
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext

from aiogram.types import KeyboardButton

from crypto_bot.handlers.default_buttons import global_menu_reply, global_menu
from crypto_bot.services.event_playground import event_service
from crypto_bot.states.tier_state import AddOrderState, EnterOrderState
from aiogram import Dispatcher, types

global_currency ={
    'USD': 1,
    'BTC': 22842,
    'ETH': 1615,
    'BNB': 314,
    'XRP': 0.42,
    'DOGE': 0.08,
    'ADA': 0.37,
}

async def market(callback: types.CallbackQuery):
    await callback.message.delete()
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    inline_kb.add(types.InlineKeyboardButton("Мои ордера", callback_data="myorders_1"))
    inline_kb.add(types.InlineKeyboardButton("Осмотр ордеров", callback_data="allorders"))
    inline_kb.add(types.InlineKeyboardButton("В меню пользователя", callback_data="return_user"))
    await callback.message.answer("Что вас интнрсует?", reply_markup=inline_kb)


async def my_orders(callback: types.CallbackQuery):
    user_data = {'tg_id': callback.from_user.id}
    response = event_service.get_user_data_from_user_id(user_data)
    user = response[0]['id']
    page = int(callback.data.split("_")[-1])
    orders_data = {'user': user, 'page': page}
    response = event_service.get_user_orders(orders_data)

    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    for orders in response['results']:
        inline_kb.add(
            types.InlineKeyboardButton(f'{orders["id"]}. {orders["currency"]} - price: {orders["price"]} - amount: {orders["amount"]}', callback_data=f'display_orders_:{orders["id"]}')
        )

    pagination_buttons = []

    if response["previous"]:
        pagination_buttons.append(types.InlineKeyboardButton("⬅️", callback_data=f"myorders_{page - 1}"))
    if response["next"]:
        pagination_buttons.append(types.InlineKeyboardButton("➡️", callback_data=f"myorders_{page + 1}"))
    inline_kb.row(*pagination_buttons)
    inline_kb.add(types.InlineKeyboardButton("Добавить ордер", callback_data='add_order'))
    inline_kb.add(types.InlineKeyboardButton("В меню пользователя", callback_data="return_user"))
    await callback.message.delete()
    await callback.message.answer('Ваши ордера:', reply_markup=inline_kb)


async def display_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    orders_id = int(callback.data.split(":")[-1])
    response = event_service.get_order(orders_id)
    order_id = response['user']
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    date = str(response['date']).split("T")
    user_data = {'tg_id': callback.from_user.id}
    users_response = event_service.get_user_data_from_user_id(user_data)
    user_id = users_response[0]['id']
    if order_id == user_id:
        inline_kb.add(types.InlineKeyboardButton("Удалить ордер", callback_data=f"delete_order:{orders_id}"))
    else:
        inline_kb.add(types.InlineKeyboardButton("Вступить в сделку", callback_data=f"enter_to_order:{response['currency']}:{orders_id}"))
    inline_kb.add(types.InlineKeyboardButton("В меню пользователя", callback_data="return_user"))
    await callback.message.answer(f"Валюта: {response['currency']}\nЦена: {response['price']}\nКоличество: {response['amount']}\nДата создание ордера: {date[0]}  {date[1].split('.')[0]}\n", reply_markup=inline_kb)

async def delete_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    orders_id = int(callback.data.split(":")[-1])
    response = event_service.get_order(orders_id)
    amount = response['amount']
    wallet_id = response['wallet']
    response = requests.get(f"http://localhost:8000/api/walletid/{wallet_id}")
    wallet_data = {'id': wallet_id, 'amount': float("{0:.3f}".format(float(response.json()["amount"]) + amount))}
    response = event_service.delete_order(orders_id, wallet_data)
    await callback.message.answer("Ваш ордер удален!")
    await callback.message.answer("Меню пользователя: ", reply_markup=global_menu())


async def enter_to_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    order_id = callback.data.split(":")[-1]
    order_currency = callback.data.split(":")[-2]
    recipient_data = {'tg_id': callback.from_user.id}
    response = event_service.get_user_data_from_user_id(recipient_data)
    recipient_user_id = response[0]['id']
    query_params = dict(currency=order_currency, users=recipient_user_id)
    recipient_order_response = requests.get(f'http://localhost:8000/api/walletid/', query_params)
    if len(recipient_order_response.json()) > 0:
        query_params = dict(currency="USD", users=recipient_user_id)
        recipient_usd_wallet = requests.get(f'http://localhost:8000/api/walletid/', query_params)
        recipient_order_wallet = recipient_order_response.json()
        sender_order_wallet = requests.get(f'http://localhost:8000/api/order/{order_id}/')
        query_params = dict(currency="USD", users=sender_order_wallet.json()['user'])
        sender_usd_wallet = requests.get(f'http://localhost:8000/api/walletid/', query_params)
        await state.set_state(EnterOrderState.get_amount.state)
        await state.update_data(recipient_order_wallet=recipient_order_wallet[0])
        await state.update_data(recipient_usd_wallet=recipient_usd_wallet.json()[0])
        await state.update_data(sender_order_wallet=sender_order_wallet.json())
        await state.update_data(sender_usd_wallet=sender_usd_wallet.json()[0])
        await callback.message.answer(f"Сколько вы хотите приобрести {order_currency}?", reply_markup=global_menu_reply())
    else:
        await callback.message.answer(f"У вас нету кошелька {order_currency} для проведения данной транзакции: ")
        await callback.message.answer(f"Меню пользователя: ", reply_markup=global_menu())


async def get_amount_to_enter_order(message: types.Message, state: FSMContext):
    if message.text == 'В меню пользователя':
        await message.answer('Транзакция отменена', reply_markup=types.ReplyKeyboardRemove())
        await message.answer("Меню пользователя: ", reply_markup=global_menu())
        await state.finish()
    else:
        recipient_pay_amount = float(message.text)
        await state.set_state(EnterOrderState.enter_order.state)
        get_data = await state.get_data()
        if recipient_pay_amount <= float(get_data['sender_order_wallet']['amount']):
            if float(recipient_pay_amount) * get_data['sender_order_wallet']['price'] <= float(get_data['recipient_usd_wallet']['amount']):

                new_recipient_usd_wallet = {'amount': get_data['recipient_usd_wallet']['amount'] - float(recipient_pay_amount) * get_data['sender_order_wallet']['price']}
                response = requests.patch(f"http://localhost:8000/api/walletid/{get_data['recipient_usd_wallet']['id']}", json=new_recipient_usd_wallet)

                new_recipient_order_wallet = {'amount': get_data['recipient_order_wallet']['amount'] + recipient_pay_amount}
                response = requests.patch(f"http://localhost:8000/api/walletid/{get_data['recipient_order_wallet']['id']}", json=new_recipient_order_wallet)

                new_sender_order = {'amount': get_data['sender_order_wallet']['amount'] - recipient_pay_amount}
                response = requests.patch(f"http://localhost:8000/api/order/{get_data['sender_order_wallet']['id']}/", json=new_sender_order)

                new_sender_usd_wallet = {'amount': get_data['sender_usd_wallet']['amount'] + float(recipient_pay_amount) * get_data['sender_order_wallet']['price']}
                response = requests.patch(f"http://localhost:8000/api/walletid/{get_data['sender_usd_wallet']['id']}", json=new_sender_usd_wallet)

                await state.finish()
                await message.answer("Транзакция провизведенна успешно!", reply_markup=types.ReplyKeyboardRemove())
                await message.answer(f"Меню пользователя: ", reply_markup=global_menu())
            else:
                await message.answer("У вас недостаточно USD для покупки такого количества криптовалюты. Повторите попытку: ")
        else:
            await message.answer("Введите коректные данные")


async def add_order(callback: types.CallbackQuery):
    await callback.message.delete()
    user_data = {'tg_id': callback.from_user.id}
    users_response = event_service.get_user_data_from_user_id(user_data)
    for i in users_response:
        user_data = {'users': i['id']}
    users_response = event_service.find_wallet_currency(user_data)

    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    for i in users_response:
        if i['currency'] == 'USD':
            pass
        else:
            inline_kb.add(
                types.InlineKeyboardButton(f"{i['currency']} - {i['amount']}", callback_data=f'add_my_order_{i["id"]}_{i["amount"]}_{i["currency"]}')
            )
    inline_kb.add(types.InlineKeyboardButton("В меня пользователя", callback_data='return_user'))
    await callback.message.answer("Выберите криптовалюту которую хотите продать: ", reply_markup=inline_kb)


async def get_amount_to_add_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(AddOrderState.get_amount.state)
    await state.update_data(order_currency=callback.data.split("_")[-1])
    await state.update_data(total_amount=callback.data.split("_")[-2])
    await state.update_data(wallet_id=callback.data.split("_")[-3])
    reply_kb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    reply_kb.add(KeyboardButton('Все'))
    reply_kb.add(KeyboardButton('В меню пользователя'))
    await callback.message.answer(f"У вас есть {callback.data.split('_')[-2]} {callback.data.split('_')[-1]}. Введите количество {callback.data.split('_')[-1]} которое хотите продать: ", reply_markup=reply_kb)


async def get_price_to_add_order(message: types.Message, state: FSMContext):
    if message.text == 'В меню пользователя':
        await message.answer("Меню пользователя: ", reply_markup=global_menu())
        await state.finish()
    elif message.text == "Все":
        get_data = await state.get_data()
        amount = get_data['total_amount']
        await state.update_data(amount=amount)
        order_currency = get_data['order_currency']
        await state.set_state(AddOrderState.get_price.state)
        await message.answer(
            f"По какой цене вы хотите продать {get_data['order_currency']}? \nПримечание: цена должна указываться по отношению к USD. Октуальная цена {order_currency} = {global_currency[order_currency]} USDT",
            reply_markup=global_menu_reply()
        )
    else:
        try:
            amount = float(message.text)
            get_data = await state.get_data()
            if amount <= float(get_data['total_amount']):
                await state.update_data(amount=amount)
                order_currency = get_data['order_currency']
                await state.set_state(AddOrderState.get_price.state)
                await message.answer(
                    f"По какой цене вы хотите продать {get_data['order_currency']}? \nПримечание: цена должна указываться по отношению USD. Октуальная цена {order_currency} = {global_currency[order_currency]} USDT",
                    reply_markup=global_menu_reply()
                )
            else:
                await message.answer("Введите коректные данные: ")
        except:
            await message.answer("Введите коректные данные: ")


async def post_order(message: types.Message, state: FSMContext):
    if message.text == 'В меню пользователя':
        await message.answer("Создание ордера прерванно")
        await message.answer("Меню пользователя: ", reply_markup=global_menu())
        await state.finish()
    else:
        try:
            price = float(message.text)
            user_data = {'tg_id': message.from_user.id}
            users_response = event_service.get_user_data_from_user_id(user_data)
            user_id = users_response[0]['id']
            get_data = await state.get_data()
            order_data = {'user': user_id, 'currency': get_data['order_currency'], 'price': price, 'amount': get_data['amount'], 'wallet': get_data['wallet_id']}
            new_wallet_ampunt = float("{0:.3f}".format(float(get_data['total_amount']) - float(get_data['amount'])))

            wallet_data = {'id': get_data['wallet_id'], 'amount': new_wallet_ampunt}
            response = event_service.post_order(order_data, wallet_data)
            await state.finish()
            await message.answer("Ваш ордер успешно создан!")
            await message.answer("Меню пользователя: ", reply_markup=global_menu())
        except:
            await message.answer("Введите коректные данные: ")


async def orders_currency(callback: types.CallbackQuery):
    await callback.message.delete()
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    currency = ["BTC", "ETH", "ADA", "BNB", "XRP", "DOGE"]

    for cur in currency:
        inline_kb.add(
            types.InlineKeyboardButton(f'{cur}', callback_data=f'showorders_{cur}_1'))

    inline_kb.add(types.InlineKeyboardButton("Общий осмотр ордеров", callback_data="show_all_orders_1"))
    inline_kb.add(types.InlineKeyboardButton("В меню пользователя", callback_data="return_user"))

    await callback.message.answer('Выберите что хотите купить: ', reply_markup=inline_kb)


async def show_all_orders(callback: types.CallbackQuery):
    await callback.message.delete()
    page = int(callback.data.split("_")[-1])
    orders_data = {'page': page}
    query_params = dict(limit=5, offset=(page - 1) * 5)
    response = response = requests.get(f"http://localhost:8000/api/orders/", query_params)

    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    for orders in response.json()['results']:
        inline_kb.add(
            types.InlineKeyboardButton(
                f'{orders["id"]}. {orders["currency"]} - price: {orders["price"]} - amount: {orders["amount"]}',
                callback_data=f'display_orders_:{orders["id"]}')
        )

        pagination_buttons = []

        if response.json()["previous"]:
            pagination_buttons.append(types.InlineKeyboardButton("⬅️", callback_data=f"orders_{page - 1}"))
        if response.json()["next"]:
            pagination_buttons.append(types.InlineKeyboardButton("➡️", callback_data=f"orders_{page + 1}"))
    inline_kb.row(*pagination_buttons)
    inline_kb.add(types.InlineKeyboardButton("В меню пользователя", callback_data="return_user"))
    await callback.message.answer("Выберите событие", reply_markup=inline_kb)

async def orders(callback: types.CallbackQuery):
    await callback.message.delete()
    page = int(callback.data.split("_")[-1])
    user_currency = callback.data.split("_")[-2]
    orders_data = {'page': page, 'currency': user_currency}
    response = event_service.get_orders(orders_data)

    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    if len(response['results']) == 0:
        inline_kb = types.InlineKeyboardMarkup(row_width=1)
        currency = ["BTC", "ETH", "ADA", "BNB", "XRP", "DOGE"]
        for cur in currency:

            inline_kb.add(
                types.InlineKeyboardButton(f'{cur}', callback_data=f'showorders_{cur}_1'))
        inline_kb.add(types.InlineKeyboardButton("В меню пользователя", callback_data="return_user"))
        await callback.message.answer(f'На данный момент ни кто не продает {user_currency}, можете выбрать другую валюту или вернуться в меню пользователя', reply_markup=inline_kb)
    else:
        for orders in response['results']:
            inline_kb.add(
                types.InlineKeyboardButton(
                    f'{orders["id"]}. {orders["currency"]} - price: {orders["price"]} - amount: {orders["amount"]}',
                    callback_data=f'display_orders_:{orders["id"]}')
            )

        pagination_buttons = []

        if response["previous"]:
            pagination_buttons.append(types.InlineKeyboardButton("⬅️", callback_data=f"orders_{page - 1}"))
        if response["next"]:
            pagination_buttons.append(types.InlineKeyboardButton("➡️", callback_data=f"orders_{page + 1}"))
        inline_kb.row(*pagination_buttons)
        inline_kb.add(types.InlineKeyboardButton("В меню пользователя", callback_data="return_user"))
        await callback.message.answer("Выберите событие", reply_markup=inline_kb)


def setup(dp: Dispatcher):
    dp.register_callback_query_handler(market, Text(equals="market"))
    dp.register_callback_query_handler(my_orders, Text(contains="myorders"))
    dp.register_callback_query_handler(orders_currency, Text(equals="allorders"))
    dp.register_callback_query_handler(show_all_orders, Text(equals="show_all_orders_1"))

    dp.register_callback_query_handler(orders, Text(contains="showorders_"))
    dp.register_callback_query_handler(delete_order, Text(contains="delete_order"))
    dp.register_callback_query_handler(enter_to_order, Text(contains="enter_to_order"))

    dp.register_callback_query_handler(display_order, Text(contains="display_orders_"))
    dp.register_callback_query_handler(add_order, Text(equals="add_order"))
    dp.register_callback_query_handler(get_amount_to_add_order, Text(contains="add_my_order_"))
    dp.register_message_handler(get_price_to_add_order, state=AddOrderState.get_amount)
    dp.register_message_handler(post_order, state=AddOrderState.get_price)


    dp.register_message_handler(get_amount_to_enter_order, state=EnterOrderState.get_amount)



