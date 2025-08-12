import logging
from typing import Dict, Any, Optional

class RiskManager:
    """Advanced risk management for trading bot."""
    
    def __init__(self, 
                 max_position_size_pct: float = 2.0,  # % of account balance
                 stop_loss_pct: float = 1.0,          # % stop loss
                 take_profit_pct: float = 2.0,        # % take profit
                 max_daily_loss_pct: float = 5.0):    # % max daily loss
        
        self.max_position_size_pct = max_position_size_pct
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        
        self.daily_pnl = 0.0
        self.trades_today = 0
    
    def calculate_position_size(self, account_balance: float, current_price: float) -> float:
        """Calculate position size based on risk management rules."""
        max_usd_risk = account_balance * (self.max_position_size_pct / 100)
        max_quantity = max_usd_risk / current_price
        
        logging.info(f"Risk-adjusted position size: {max_quantity:.6f} (${max_usd_risk:.2f} max risk)")
        return max_quantity
    
    def check_stop_loss(self, entry_price: float, current_price: float, side: str) -> bool:
        """Check if stop loss should be triggered."""
        if side.upper() == 'LONG':
            loss_pct = ((entry_price - current_price) / entry_price) * 100
        else:
            loss_pct = ((current_price - entry_price) / entry_price) * 100
        
        if loss_pct >= self.stop_loss_pct:
            logging.warning(f"STOP LOSS TRIGGERED! Loss: {loss_pct:.2f}%")
            return True
        return False
    
    def check_take_profit(self, entry_price: float, current_price: float, side: str) -> bool:
        """Check if take profit should be triggered."""
        if side.upper() == 'LONG':
            profit_pct = ((current_price - entry_price) / entry_price) * 100
        else:
            profit_pct = ((entry_price - current_price) / entry_price) * 100
        
        if profit_pct >= self.take_profit_pct:
            logging.info(f"TAKE PROFIT TRIGGERED! Profit: {profit_pct:.2f}%")
            return True
        return False
    
    def can_trade(self) -> bool:
        """Check if trading is allowed based on daily loss limits."""
        if abs(self.daily_pnl) >= self.max_daily_loss_pct:
            logging.warning(f"Daily loss limit reached: {self.daily_pnl:.2f}%")
            return False
        return True
    
    def record_trade(self, pnl_pct: float):
        """Record a completed trade."""
        self.daily_pnl += pnl_pct
        self.trades_today += 1
        logging.info(f"Trade recorded. Daily P&L: {self.daily_pnl:.2f}% | Trades today: {self.trades_today}")
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics."""
        return {
            "daily_pnl_pct": self.daily_pnl,
            "trades_today": self.trades_today,
            "can_trade": self.can_trade(),
            "stop_loss_pct": self.stop_loss_pct,
            "take_profit_pct": self.take_profit_pct
        }