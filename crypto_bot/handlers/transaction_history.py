from crypto_bot.handlers.home import *
from aiogram.dispatcher import FSMContext

from crypto_bot.services.event_playground import event_service
from aiogram import types


async def transaction_history(callback: types.CallbackQuery, state: FSMContext):
    start = 0
    finish = 5
    await callback.message.delete()
    user_data = {'tg_id': callback.from_user.id}
    user_response = event_service.get_user_data_from_user_id(user_data)

    for i in user_response:
        name = i['name']
    transaction_data = {'sender': name, 'recipient': name}
    transaction_response = event_service.find_transaction(transaction_data)
    transaction_history = []
    for i in transaction_response:
        if i not in transaction_history:
            transaction_history.append(i)
    transaction_history.reverse()
    await state.update_data(transaction_history=transaction_history)
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    await state.update_data(start=start)
    await state.update_data(finish=finish)
    normal_history = transaction_history[start:finish]
    for i in normal_history:
        inline_kb.add(
            types.InlineKeyboardButton(f'{i["id"]}. {i["sender_currency"]} - {i["sender"]} - {i["recipient_currency"]} - {i["recipient"]} ', callback_data=f'get_transaction:{i["id"]}'))
    pagination_buttons = []
    test = transaction_response[start+6:finish+2]
    if len(test) >= 1:
        pagination_buttons.append(types.InlineKeyboardButton("➡️", callback_data=f"next"))
    inline_kb.row(*pagination_buttons)
    inline_kb.add(types.InlineKeyboardButton("В меня пользователя", callback_data='return_user'))
    await callback.message.answer('Последние ваши транзакции', reply_markup=inline_kb)


async def transaction_pagination(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    get_data = await state.get_data()
    start = get_data['start']
    finish = get_data['finish']
    transaction_history = get_data['transaction_history']
    if callback.data == "next":
        start = start + 5
        finish = finish + 5
        test = transaction_history[start+5:finish+1]
        normal_history = transaction_history[start:finish]
        for i in normal_history:
            inline_kb.add(
                types.InlineKeyboardButton(f'{i["id"]}. {i["sender_currency"]} - {i["sender"]} - {i["recipient_currency"]} - {i["recipient"]} ', callback_data=f'get_transaction:{i["id"]}'))
        pagination_buttons = []
        pagination_buttons.append(types.InlineKeyboardButton("⬅️️", callback_data=f"previous"))
        if len(test) >= 1:
            pagination_buttons.append(types.InlineKeyboardButton("➡️", callback_data=f"next"))
        inline_kb.row(*pagination_buttons)
        await state.update_data(transaction_history=transaction_history)
        await state.update_data(start=start)
        await state.update_data(finish=finish)
        inline_kb.add(types.InlineKeyboardButton("В меня пользователя", callback_data='return_user'))
        await callback.message.answer('Последние ваши транзакции', reply_markup=inline_kb)
    elif callback.data == "previous":
        start = start - 5
        finish = finish - 5
        test = transaction_history[start + 5:finish + 1]
        normal_history = transaction_history[start:finish]
        for i in normal_history:
            inline_kb.add(
                types.InlineKeyboardButton(
                    f'{i["id"]}. {i["sender_currency"]} - {i["sender"]} - {i["recipient_currency"]} - {i["recipient"]} ',
                    callback_data=f'get_transaction:{i["id"]}'))
        pagination_buttons = []
        if start != 0:
            pagination_buttons.append(types.InlineKeyboardButton("⬅️️", callback_data=f"previous"))
        if len(test) >= 1:
            pagination_buttons.append(types.InlineKeyboardButton("➡️", callback_data=f"next"))
        inline_kb.row(*pagination_buttons)
        inline_kb.add(types.InlineKeyboardButton("В меня пользователя", callback_data='return_user'))
        await state.update_data(transaction_history=transaction_history)
        await state.update_data(start=start)
        await state.update_data(finish=finish)
        await callback.message.answer('Последние ваши транзакции', reply_markup=inline_kb)


async def display_transaction(callback: types.CallbackQuery):
    await callback.message.delete()
    pk = int(callback.data.split(":")[-1])
    transaction_data = {'id': pk}
    response = event_service.get_transaction_data(transaction_data)
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    inline_kb.add(types.InlineKeyboardButton("В меня пользователя", callback_data='return_user'))
    data = response.json()
    date = str(data['date']).split("T")
    await callback.message.answer(f"Получатель - {data['recipient']}\nВалюта получателя - {data['recipient_currency']}\nИтоговая сумма получателя - {data['received_amount']}\n"
                                  f"Отправитель - {data['sender']}\nВалюта отправителя - {data['sender_currency']}\nИтоговая сумма отправителя - {data['send_amount']}\n"
                                  f"Комиссия - {data['commission']}\nДата проведения пранзакции - {date[0]}  {date[1].split('.')[0]}", reply_markup=inline_kb)


async def return_user(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.delete()
    await callback.message.answer("Главное меню: ", reply_markup=global_menu())

def setup(dp: Dispatcher):
    """
    История транзакций
    """
    dp.register_callback_query_handler(return_user, Text(equals="return_user"))
    dp.register_callback_query_handler(display_transaction, Text(contains="get_transaction"))
    dp.register_callback_query_handler(transaction_history, Text(equals="transaction_history"))
    dp.register_callback_query_handler(transaction_pagination, Text(equals="next"))
    dp.register_callback_query_handler(transaction_pagination, Text(equals="previous"))


