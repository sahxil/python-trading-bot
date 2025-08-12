# bot.py
"""
This module contains the BasicBot class, which handles all interactions
with the Binance Futures API. It is "rule-aware" and handles symbol precision.
"""
from binance import Client
from binance.exceptions import BinanceAPIException
import logging
import pandas as pd
from typing import List, Dict, Any
import math

class BasicBot:
    """A bot for fetching data and placing orders on Binance Futures."""

    def __init__(self, api_key: str, api_secret: str, symbol: str):
        """
        Initializes the bot and fetches symbol-specific trading rules.
        """
        self.symbol = symbol
        self.quantity_precision = 0

        try:
            self.client = Client(api_key, api_secret, testnet=True)
            self.client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'
            self.client.futures_ping()
            logging.info("Binance client initialized and connection successful.")
            
            self._get_symbol_info()

        except Exception as e:
            logging.error(f"Failed to initialize Binance Client: {e}")
            raise

    def _get_symbol_info(self):
        """Fetches and stores the quantity precision for the trading symbol."""
        try:
            exchange_info = self.client.futures_exchange_info()
            for s in exchange_info['symbols']:
                if s['symbol'] == self.symbol:
                    # --- THIS LINE IS THE FIX ---
                    self.quantity_precision = int(s['quantityPrecision'])
                    # ---------------------------
                    logging.info(f"Retrieved precision for {self.symbol}: {self.quantity_precision} decimal places.")
                    return
            raise ValueError(f"Could not find symbol info for {self.symbol}")
        except Exception as e:
            logging.error(f"Failed to get symbol info: {e}")
            raise

    def _round_quantity(self, quantity: float) -> float:
        # ... (This method remains the same)
        if self.quantity_precision == 0:
            return math.floor(quantity)
        
        factor = 10 ** self.quantity_precision
        return math.floor(quantity * factor) / factor

    def get_historical_data(self, interval: str = '1m', limit: int = 100) -> pd.DataFrame | None:
        # ... (This method remains the same)
        try:
            klines = self.client.futures_klines(symbol=self.symbol, interval=interval, limit=limit)
            columns = ['Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_Time', 'Quote_Asset_Volume', 'Number_of_Trades', 'Taker_Buy_Base_Asset_Volume', 'Taker_Buy_Quote_Asset_Volume', 'Ignore']
            df = pd.DataFrame(klines, columns=columns)
            df['Open_Time'] = pd.to_datetime(df['Open_Time'], unit='ms')
            df['Close_Time'] = pd.to_datetime(df['Close_Time'], unit='ms')
            numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, axis=1)
            return df[['Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume']]
        except Exception as e:
            logging.error(f"Failed to fetch historical data for {self.symbol}: {e}")
            return None

    def get_account_balance(self, asset: str = 'USDT') -> float:
        # ... (This method remains the same)
        try:
            balances: List[Dict[str, Any]] = self.client.futures_account_balance()
            for balance in balances:
                if balance['asset'] == asset:
                    return float(balance['balance'])
            return 0.0
        except Exception as e:
            logging.error(f"Failed to get account balance: {e}")
            return 0.0

    def get_current_price(self) -> float:
        # ... (This method remains the same)
        try:
            return float(self.client.futures_mark_price(symbol=self.symbol)['markPrice'])
        except Exception as e:
            logging.error(f"Failed to get current price for {self.symbol}: {e}")
            return 0.0

    def place_order(self, side: str, order_type: str, quantity: float, price: float = None) -> dict | None:
        # ... (This method remains the same)
        try:
            rounded_quantity = self._round_quantity(quantity)
            logging.info(f"Original quantity: {quantity}, Rounded quantity: {rounded_quantity}")
            
            if rounded_quantity <= 0:
                logging.warning("Order quantity is zero after rounding. Order not placed.")
                return None

            params = {'symbol': self.symbol, 'side': side, 'type': order_type, 'quantity': rounded_quantity}
            if order_type == 'LIMIT':
                if price is None:
                    raise ValueError("Price is required for LIMIT orders")
                params['price'] = price
                params['timeInForce'] = 'GTC'
            
            logging.info(f"Placing {order_type} order with params: {params}")
            order = self.client.futures_create_order(**params)
            logging.info(f"Order placed successfully: {order['orderId']}")
            return order
        except BinanceAPIException as e:
            logging.error(f"Failed to place order. API Error: {e}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None