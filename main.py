# main.py
"""
This is the main engine for the autonomous RSI trading bot.
It runs in a continuous loop to fetch data, analyze it, and place trades.
"""
import time
import logging
import config
from bot import BasicBot

# --- Configuration ---
SYMBOL = 'BTCUSDT'
QUANTITY = 0.001  # The amount of BTC to trade
INTERVAL = '1m'  # The timeframe to analyze (1 minute)

def setup_logging():
    """Configures logging to output to both console and a file."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    fh = logging.FileHandler('trading_bot.log', mode='a')
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)

def main():
    """The main automation loop."""
    setup_logging()
    
    # --- State Variable ---
    # This tracks whether we are currently in a position.
    in_position = False

    try:
        bot = BasicBot(api_key=config.API_KEY, api_secret=config.API_SECRET)
        logging.info(f"Bot started. Trading {SYMBOL} with a quantity of {QUANTITY}.")

        while True:
            # 1. Fetch Data
            df = bot.get_historical_data(symbol=SYMBOL, interval=INTERVAL)
            if df is None:
                logging.warning("Could not fetch data. Retrying in 60 seconds.")
                time.sleep(60)
                continue

            # 2. Analyze and Get Signal
            signal = bot.analyze_and_get_signal(df)
            logging.info(f"Current Signal: {signal} | In Position: {in_position}")

            # 3. Execute Trades Based on Signal and State
            if signal == 'BUY' and not in_position:
                logging.info(">>> BUY Signal Detected. Placing MARKET BUY order. <<<")
                order = bot.place_order(SYMBOL, 'BUY', 'MARKET', QUANTITY)
                if order:
                    logging.info(f"BUY order placed successfully: {order}")
                    in_position = True  # Update state
                else:
                    logging.error("BUY order failed to place.")

            elif signal == 'SELL' and in_position:
                logging.info(">>> SELL Signal Detected. Placing MARKET SELL order. <<<")
                order = bot.place_order(SYMBOL, 'SELL', 'MARKET', QUANTITY)
                if order:
                    logging.info(f"SELL order placed successfully: {order}")
                    in_position = False  # Update state
                else:
                    logging.error("SELL order failed to place.")
            
            # Wait for the next cycle
            logging.info("-------------------- Waiting for next cycle --------------------")
            time.sleep(60)

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        logging.info("Bot stopped by user.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)


if __name__ == "__main__":
    main()