from aiogram.dispatcher.filters.state import State, StatesGroup


class RegistrationState(StatesGroup):
    name = State()
    phone = State()
    password = State()


class AuthorizationState(StatesGroup):
    name = State()
    number = State()
    password = State()


class OutState(StatesGroup):
    out = State()
    password_nickname = State()
    password = State()
    niew_password = State()
    niew_nickname = State()


class TransferState(StatesGroup):
    transfer = State()
    sender_currency = State()
    amount = State()
    password = State()
    tg_id = State()
    choose_wallet = State()
    choose_amount = State()

    sender_currency_wallet = State()
    sender_amount_wallet = State()
    wallet_number = State()


class WalletState(StatesGroup):
    amount_wallets = State()
    add_wallet = State()
    get_password = State()
    inf_wallet = State()
    get_password_delete = State()


class TransactionHistory(StatesGroup):
    update_list = State()


class AddOrderState(StatesGroup):
    get_amount = State()
    get_price = State()


class EnterOrderState(StatesGroup):
    get_amount = State()
    enter_order = State()

