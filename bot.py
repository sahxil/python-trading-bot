# bot.py
"""
This module contains the BasicBot class, which handles all interactions
with the Binance Futures API and contains the trading strategy logic.
"""
from binance import Client
from binance.exceptions import BinanceAPIException
import logging
import pandas as pd
import pandas_ta as ta # Import the technical analysis library

class BasicBot:
    """A trading bot that includes an RSI strategy."""

    def __init__(self, api_key: str, api_secret: str):
        # ... (The __init__ method remains the same)
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
    
    def get_historical_data(self, symbol: str, interval: str = '1m', limit: int = 100) -> pd.DataFrame | None:
        # ... (The get_historical_data method remains the same)
        """
        Fetches historical k-line (candlestick) data from Binance.

        Args:
            symbol (str): The trading symbol (e.g., 'BTCUSDT').
            interval (str, optional): The candle interval. Defaults to '1m'.
            limit (int, optional): The number of candles to retrieve. Defaults to 100.

        Returns:
            pd.DataFrame | None: A pandas DataFrame with the historical data,
                                 or None if the API call fails.
        """
        try:
            # Fetch raw k-line data from the API
            klines = self.client.futures_klines(symbol=symbol, interval=interval, limit=limit)
            
            # Define the column names for the DataFrame
            columns = [
                'Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_Time',
                'Quote_Asset_Volume', 'Number_of_Trades', 'Taker_Buy_Base_Asset_Volume',
                'Taker_Buy_Quote_Asset_Volume', 'Ignore'
            ]
            
            # Create the DataFrame
            df = pd.DataFrame(klines, columns=columns)
            
            # Convert timestamp columns to datetime objects
            df['Open_Time'] = pd.to_datetime(df['Open_Time'], unit='ms')
            df['Close_Time'] = pd.to_datetime(df['Close_Time'], unit='ms')
            
            # Convert price and volume columns to numeric types
            numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, axis=1)
            
            # We only need a few key columns for analysis
            return df[['Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume']]
            
        except Exception as e:
            logging.error(f"Failed to fetch historical data for {symbol}: {e}")
            return None

    # --- NEW METHOD ---
    def analyze_and_get_signal(self, df: pd.DataFrame) -> str:
        """
        Analyzes the historical data to generate a trading signal based on RSI.

        Args:
            df (pd.DataFrame): DataFrame containing historical candle data.

        Returns:
            str: 'BUY', 'SELL', or 'HOLD'.
        """
        if df is None or len(df) == 0:
            return 'HOLD'

        # --- RSI Strategy ---
        RSI_PERIOD = 14
        RSI_OVERBOUGHT = 70
        RSI_OVERSOLD = 30
        
        # Calculate RSI using the pandas-ta library. The 'append=True' argument
        # automatically adds the RSI values as a new column in the DataFrame.
        df.ta.rsi(length=RSI_PERIOD, append=True)
        
        # Get the most recent RSI value
        latest_rsi = df[f'RSI_{RSI_PERIOD}'].iloc[-1]
        
        logging.info(f"Latest RSI value: {latest_rsi:.2f}")

        if latest_rsi > RSI_OVERBOUGHT:
            return 'SELL'  # Signal to sell (short) when overbought
        elif latest_rsi < RSI_OVERSOLD:
            return 'BUY'   # Signal to buy (long) when oversold
        else:
            return 'HOLD'

    def place_order(self, symbol: str, side: str, order_type: str, 
                    quantity: float, price: float = None) -> dict | None:
        # ... (The place_order method remains the same)
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