# main.py
import time
import logging
from dotenv import load_dotenv
from config import Config
from bot import BasicBot
from strategies.strategy_framework import EnsembleStrategy
from management.position_manager import PositionManager
from management.risk_manager import RiskManager

# Load environment variables from .env file at the very start
load_dotenv()

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
    """The main automation loop for the advanced trading bot."""
    setup_logging()

    try:
        config = Config()
        bot = BasicBot(api_key=config.API_KEY, api_secret=config.API_SECRET, symbol=config.SYMBOL)
        
        # Initialize all managers
        strategy = EnsembleStrategy()
        pos_manager = PositionManager()
        risk_manager = RiskManager()
        
        logging.info(f"Bot started. Trading {config.SYMBOL} using Ensemble Strategy.")

        while True:
            try:
                # 1. Check Risk and Position Status
                if not risk_manager.can_trade():
                    logging.critical("DAILY LOSS LIMIT REACHED. TRADING HALTED.")
                    break

                current_price = bot.get_current_price()
                position = pos_manager.current_position

                # 2. Stop-Loss / Take-Profit Check (if in position)
                if position:
                    pnl_percent = position.pnl_percentage(current_price)
                    logging.info(f"In position. Current P&L: {pnl_percent:.2f}%")
                    
                    sl_triggered = risk_manager.check_stop_loss(position.entry_price, current_price, position.side)
                    tp_triggered = risk_manager.check_take_profit(position.entry_price, current_price, position.side)

                    if sl_triggered or tp_triggered:
                        logging.info(">>> SL/TP Triggered. Closing position. <<<")
                        order = bot.place_order(side='SELL' if position.side == 'LONG' else 'BUY', 
                                                order_type='MARKET', 
                                                quantity=position.size)
                        if order:
                            pos_manager.close_position(current_price)
                            risk_manager.record_trade(pnl_percent)
                        time.sleep(config.SLEEP_INTERVAL)
                        continue

                # 3. Strategy Analysis for New Trades
                df = bot.get_historical_data(interval=config.INTERVAL)
                if df is None:
                    logging.warning(f"Could not fetch data. Retrying in {config.SLEEP_INTERVAL} seconds.")
                    time.sleep(config.SLEEP_INTERVAL)
                    continue

                signal, analysis = strategy.analyze_and_get_signal(df)
                
                # 4. Entry and Exit Logic
                if signal == 'BUY' and not position:
                    logging.info(">>> BUY Signal Detected. Entering position. <<<")
                    account_balance = bot.get_account_balance()
                    quantity = risk_manager.calculate_position_size(account_balance, current_price)
                    
                    order = bot.place_order(side='BUY', order_type='MARKET', quantity=quantity)
                    if order:
                        executed_quantity = float(order['origQty'])
                        pos_manager.open_position(config.SYMBOL, executed_quantity, current_price, 'LONG')

                elif signal == 'SELL' and position and position.side == 'LONG':
                    logging.info(">>> SELL Signal Detected. Closing LONG position. <<<")
                    order = bot.place_order(side='SELL', order_type='MARKET', quantity=position.size)
                    if order:
                        pnl_percent = position.pnl_percentage(current_price)
                        pos_manager.close_position(current_price)
                        risk_manager.record_trade(pnl_percent)
                
                logging.info("-------------------- Waiting for next cycle --------------------")
                time.sleep(config.SLEEP_INTERVAL)

            except Exception as e:
                logging.error(f"An error occurred in the main loop: {e}", exc_info=True)
                time.sleep(config.SLEEP_INTERVAL) # Wait before retrying

    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
    except Exception as e:
        logging.error(f"A critical error occurred, shutting down: {e}", exc_info=True)

if __name__ == "__main__":
    main()