import requests

global_currency ={
    'USD': 1,
    'BTC': 22842,
    'ETH': 1615,
    'BNB': 314,
    'XRP': 0.42,
    'DOGE': 0.08,
    'ADA': 0.37,
}

class EventPlaygroundService:
    limit = 5
    base_url = "http://localhost:8000/api/"

    def check_availabiADAy(self):
        response = requests.get(f"{self.base_url}ping/")
        response.raise_for_status()

    def authorization(self, authorization_data: dict):
        query_params = dict(phone_number=authorization_data['phone_number'], password=authorization_data['password'])
        response = requests.get(f"{self.base_url}authorization/", query_params)
        response.raise_for_status()
        return response.json()

    def check_register_name(self, name_data: dict):
        query_params = dict(name=name_data['name'])
        response = requests.get(f"{self.base_url}name/", query_params)
        response.raise_for_status()
        return response.json()

    def check_register_register_name(self, phone_number_data: dict):
        query_params = dict(phone_number=phone_number_data['phone_number'])
        response = requests.get(f"{self.base_url}phone_number/", query_params)
        response.raise_for_status()
        return response.json()

    def get_user_data_from_user_id(self, user_data):
        query_params = dict(tg_id=user_data['tg_id'])
        response = requests.get(f"{self.base_url}tg_id/", params=query_params)
        response.raise_for_status()
        return response.json()

    def get_user_data_from_user_wallet(self, user_data):
        query_params = dict(currency=user_data['currency'], users=user_data['users'])
        response = requests.get(f"{self.base_url}walletid/", params=query_params)
        response.raise_for_status()
        return response.json()

    def check_transaction_password(self, user_data):
        query_params = dict(tg_id=user_data['tg_id'])
        response = requests.get(f"{self.base_url}password/", params=query_params)
        response.raise_for_status()
        return response.json()

    def find_wallet(self, wallet_data):
        query_params = dict(currency=wallet_data['currency'], users=wallet_data['users'])
        response = requests.get(f"{self.base_url}walletid/", params=query_params)
        response.raise_for_status()
        return response.json()

    def create_user(self, user_data: dict):
        response = requests.post(f"{self.base_url}users/", json=user_data)
        response.raise_for_status()
        return response.json()
    def patch_wallet(self, wallet_data):
        validate_wallet_data = {'amount': wallet_data['new_sender_amount']}
        response = requests.patch(f"{self.base_url}walletid/{wallet_data['sender_wallet_id']}", json=validate_wallet_data)
        validate_wallet_data = {'amount': wallet_data['new_recipient_amount']}
        response = requests.patch(f"{self.base_url}walletid/{wallet_data['recipient_wallet_id']}", json=validate_wallet_data)
        return response.json()

    def patch_user(self, user_data):
        response = requests.patch(f"{self.base_url}user/{user_data['user_id']}", json=user_data)
        return response.json()          # http://127.0.0.1:8000/api/user/5

    def post_transactions(self, wallet_data):
        validate_wallet_data = {
            'sender': wallet_data['sender'],
            'sender_currency': wallet_data['sender_currency'],
            'send_amount': wallet_data['send_amount'],
            'recipient': wallet_data['recipient'],
            'recipient_currency': wallet_data['recipient_currency'],
            'received_amount': wallet_data['received_amount'],
            'commission': wallet_data['commission'],
            'wallet': wallet_data['sender_wallet_id']}
        response = requests.post(f"{self.base_url}transactions/", json=validate_wallet_data)
        return response.json()


    def find_wallet_currency(self, user_data):
        currency = ["USD", "BTC", "ETH", "ADA", "BNB", "XRP", "DOGE"]
        valid_currency = []
        query_params = dict(users=user_data['users'])
        response = requests.get(f"{self.base_url}walletid/", params=query_params)
        for i in response.json():
            valid_currency.append({'id': i['id'], 'currency': i['currency'], 'amount': i['amount']})
        return valid_currency

    def add_wallet(self, wallet_data):
        validate_wallet_data = {
            'currency': wallet_data['currency'],
            'users': wallet_data['users'],
            'amount': wallet_data['amount'],
            'wallet_number': wallet_data['wallet_number'],

        }
        response = requests.post(f"{self.base_url}wallets/", json=validate_wallet_data)
        return response.json()

    def delete_wallet(self, wallet_data):
        response = requests.delete(f"{self.base_url}walletid/{wallet_data['wallet_id']}", )

    def find_transaction(self, transaction_data):
        query_params = dict(sender=transaction_data['sender'])
        response_1 = requests.get(f"{self.base_url}findtransaction/", params=query_params)
        query_params = dict(recipient=transaction_data['recipient'])
        response_2 = requests.get(f"{self.base_url}findtransaction/", params=query_params)
        response = response_2.json() + response_1.json()
        return response

    def get_transaction_data(self, transaction_data):
        response = requests.get(f"{self.base_url}transaction/{transaction_data['id']}")
        return response

    def get_user_orders(self, orders_data):
        query_params = dict(limit=self.limit, offset=(orders_data["page"] - 1) * self.limit, user=orders_data['user'])
        response = requests.get(f"{self.base_url}orders/", params=query_params)
        response.raise_for_status()
        return response.json()

    def get_order(self, orders_id: int) -> None:
        response = requests.get(f"{self.base_url}order/{orders_id}/")
        response.raise_for_status()
        return response.json()

    def get_orders(self, orders_data):
        query_params = dict(currency=orders_data['currency'], limit=self.limit, offset=(orders_data["page"] - 1) * self.limit)
        response = requests.get(f"{self.base_url}orders/", params=query_params)
        response.raise_for_status()
        return response.json()

    def post_order(self, orders_data, wallet_data):
        response = requests.post(f"{self.base_url}orders/", json=orders_data)
        response = requests.patch(f"{self.base_url}walletid/{wallet_data['id']}", json=wallet_data)
        response.raise_for_status()
        return response.json()

    def delete_order(self, order_data, wallet_data):
        response = requests.delete(f"{self.base_url}order/{order_data}")
        response = requests.patch(f"{self.base_url}walletid/{wallet_data['id']}", json=wallet_data)


event_service = EventPlaygroundService()