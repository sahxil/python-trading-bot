# main.py
"""
This module serves as the main entry point for the trading bot.
It handles command-line argument parsing and orchestrates the bot's operations.
"""

import argparse
import logging
import config
from bot import BasicBot

def setup_logging():
    """Configures logging to output to both console and a file."""
    # Get the root logger.
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Prevent adding duplicate handlers if this function is called multiple times.
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create file handler to log messages to a file.
    fh = logging.FileHandler('trading_bot.log', mode='a') # 'a' for append mode
    fh.setLevel(logging.INFO)

    # Create console handler to log messages to the console.
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Define the format for the log messages.
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add the handlers to the logger.
    logger.addHandler(fh)
    logger.addHandler(ch)

def main():
    """Parses command-line arguments and executes the trading logic."""
    setup_logging()
    
    # Initialize the argument parser with a description.
    parser = argparse.ArgumentParser(description='A simple Binance Futures trading bot.')

    # Define the command-line arguments the bot will accept.
    parser.add_argument('symbol', help='The trading symbol (e.g., BTCUSDT)')
    parser.add_argument('side', choices=['BUY', 'SELL'], help='The order side')
    parser.add_argument('type', choices=['MARKET', 'LIMIT'], help='The order type')
    parser.add_argument('quantity', type=float, help='The order quantity')
    parser.add_argument('--price', type=float, default=None, help='The order price (required for LIMIT orders)')

    # Parse the arguments provided by the user.
    args = parser.parse_args()

    # Validate that a price is provided for LIMIT orders.
    if args.type == 'LIMIT' and args.price is None:
        parser.error('The --price argument is required for LIMIT orders.')

    try:
        # Initialize the bot with API credentials from the config file.
        bot = BasicBot(api_key=config.API_KEY, api_secret=config.API_SECRET)
        
        # Place the order using the parsed arguments.
        order_result = bot.place_order(
            symbol=args.symbol.upper(),
            side=args.side,
            order_type=args.type,
            quantity=args.quantity,
            price=args.price
        )

        if order_result:
            logging.info("--- Order Result ---")
            logging.info(f"Full response: {order_result}")
            logging.info("--------------------")

    except Exception as e:
        # Log any critical error that stops the bot from running.
        logging.error(f"Bot failed to run: {e}", exc_info=True)


if __name__ == "__main__":
    # This ensures the main() function is called only when the script is executed directly.
    main()