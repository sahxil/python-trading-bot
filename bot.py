# bot.py
from binance import Client

class BasicBot:
    def __init__(self, api_key, api_secret, base_url):
        """Initializes the BasicBot."""
        self.client = Client(api_key, api_secret, base_url=base_url)

    def get_account_info(self):
        """Gets account information to verify connection."""
        try:
            account_info = self.client.futures_account()
            return account_info
        except Exception as e:
            print(f"[ERROR] Could not connect to Binance API: {e}")
            return None