# main.py
import time
import logging
import threading
from dotenv import load_dotenv
from config import Config
from bot import BasicBot
from strategies.strategy_framework import EnsembleStrategy
from management.position_manager import PositionManager
from management.risk_manager import RiskManager
from app import app, socketio

# Load environment variables from .env file at the very start
load_dotenv()

# --- Shared State and Thread Lock ---
shared_state = {
    "bot_status": "INITIALIZING",
    "position": None,
    "analysis": None,
    "pnl_history": [{"time": time.time() * 1000, "pnl": 0.0}],
}
lock = threading.Lock()

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

def bot_thread_func():
    """The main trading bot logic, designed to run in a separate thread."""
    global shared_state

    try:
        config = Config()
        bot = BasicBot(api_key=config.API_KEY, api_secret=config.API_SECRET, symbol=config.SYMBOL)
        strategy = EnsembleStrategy()
        pos_manager = PositionManager()
        risk_manager = RiskManager()
        
        with lock:
            shared_state["bot_status"] = "RUNNING"
        logging.info(f"Bot thread started. Trading {config.SYMBOL}.")

        while True:
            try:
                if not risk_manager.can_trade():
                    logging.critical("DAILY LOSS LIMIT REACHED. TRADING HALTED.")
                    with lock:
                        shared_state["bot_status"] = "HALTED"
                    break

                current_price = bot.get_current_price()
                position = pos_manager.current_position

                if position:
                    pnl_percent = position.pnl_percentage(current_price)
                    
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
                            with lock:
                                shared_state["pnl_history"].append({"time": time.time() * 1000, "pnl": pos_manager.total_pnl})
                        time.sleep(config.SLEEP_INTERVAL)
                        continue

                df = bot.get_historical_data(interval=config.INTERVAL)
                if df is None:
                    time.sleep(config.SLEEP_INTERVAL)
                    continue

                signal, analysis = strategy.analyze_and_get_signal(df)
                
                with lock:
                    shared_state["position"] = pos_manager.get_status(current_price)
                    shared_state["analysis"] = analysis
                    if 'RSI_14' in df.columns:
                        shared_state["analysis"]["rsi_value"] = df['RSI_14'].iloc[-1]
                
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
                        with lock:
                            shared_state["pnl_history"].append({"time": time.time() * 1000, "pnl": pos_manager.total_pnl})

                time.sleep(config.SLEEP_INTERVAL)

            except Exception as e:
                logging.error(f"Error in bot loop: {e}", exc_info=True)
                with lock:
                    shared_state["bot_status"] = "ERROR"
                time.sleep(config.SLEEP_INTERVAL)
                
    except Exception as e:
        logging.error(f"Critical error in bot thread: {e}", exc_info=True)
        with lock:
            shared_state["bot_status"] = "CRASHED"

def data_emitter_thread_func():
    """Periodically emits the shared state to connected dashboard clients."""
    global shared_state
    while True:
        with lock:
            socketio.emit('update', shared_state)
        socketio.sleep(2)

if __name__ == "__main__":
    setup_logging()
    logging.info("Starting bot and web server...")

    bot_thread = threading.Thread(target=bot_thread_func, daemon=True)
    bot_thread.start()

    emitter_thread = threading.Thread(target=data_emitter_thread_func, daemon=True)
    emitter_thread.start()

    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)