# bot.py
"""
This module contains the BasicBot class, which handles all interactions
with the Binance Futures API.
"""

from binance import Client
from binance.exceptions import BinanceAPIException
import logging

class BasicBot:
    """A basic trading bot for placing orders on Binance Futures."""

    def __init__(self, api_key: str, api_secret: str):
        """
        Initializes the BasicBot and establishes a connection to the Binance API.

        Args:
            api_key (str): Your Binance API key.
            api_secret (str): Your Binance API secret.
        """
        try:
            # Initialize the client, setting testnet=True for the test environment.
            self.client = Client(api_key, api_secret, testnet=True)
            
            # Manually override the futures URL to the required testnet endpoint.
            self.client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'

            # Ping the server to verify the connection and API keys are valid.
            self.client.futures_ping()
            logging.info("Binance client initialized and connection successful.")
        except Exception as e:
            logging.error(f"Failed to initialize Binance Client: {e}")
            # Re-raise the exception to stop the bot if initialization fails.
            raise

    def place_order(self, symbol: str, side: str, order_type: str, 
                    quantity: float, price: float = None) -> dict | None:
        """
        Places an order on Binance Futures.

        Args:
            symbol (str): The trading symbol (e.g., 'BTCUSDT').
            side (str): The order side ('BUY' or 'SELL').
            order_type (str): The order type ('MARKET' or 'LIMIT').
            quantity (float): The amount to trade.
            price (float, optional): The price for LIMIT orders. Defaults to None.

        Returns:
            dict | None: A dictionary containing the order response from Binance
                         if successful, otherwise None.
        """
        try:
            # Prepare the parameters for the API call.
            params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity,
            }
            # LIMIT orders require a price and a timeInForce of 'GTC'.
            if order_type == 'LIMIT':
                if price is None:
                    raise ValueError("Price is required for LIMIT orders")
                params['price'] = price
                params['timeInForce'] = 'GTC' # Good 'Til Canceled

            logging.info(f"Placing {order_type} order with params: {params}")
            order = self.client.futures_create_order(**params)
            logging.info("Order placed successfully.")
            return order
        except BinanceAPIException as e:
            # Handle specific API errors from Binance.
            logging.error(f"Failed to place order. API Error: {e}")
            return None
        except Exception as e:
            # Handle other unexpected errors.
            logging.error(f"An unexpected error occurred: {e}")
            return None