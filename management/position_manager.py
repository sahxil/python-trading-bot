# management/position_manager.py
import logging
from dataclasses import dataclass, asdict
from typing import Optional, List
from datetime import datetime

@dataclass
class Trade:
    """Represents a single completed trade with its outcome."""
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    size: float
    entry_time: str
    exit_time: str
    pnl: float

@dataclass
class Position:
    """Represents a trading position."""
    symbol: str
    size: float
    entry_price: float
    entry_time: datetime
    side: str  # 'LONG' or 'SHORT'
    
    def unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L."""
        if self.side == 'LONG':
            return (current_price - self.entry_price) * self.size
        else:
            return (self.entry_price - current_price) * self.size
    
    def pnl_percentage(self, current_price: float) -> float:
        """Calculate P&L as percentage."""
        return (self.unrealized_pnl(current_price) / (self.entry_price * self.size)) * 100

class PositionManager:
    """Enhanced position management with P&L and trade history tracking."""
    
    def __init__(self):
        self.current_position: Optional[Position] = None
        self.total_pnl = 0.0
        self.trade_count = 0
        self.trade_history: List[Trade] = [] # New: To store completed trades

    def open_position(self, symbol: str, size: float, price: float, side: str):
        """Open a new position."""
        if self.current_position:
            logging.warning("Attempting to open position while one exists!")
            return False
        
        self.current_position = Position(
            symbol=symbol,
            size=abs(size),
            entry_price=price,
            entry_time=datetime.now(),
            side=side.upper()
        )
        
        logging.info(f"Position opened: {side} {size} {symbol} at {price}")
        return True
    
    def close_position(self, exit_price: float) -> float:
        """Closes a position and records it to trade history."""
        if not self.current_position:
            logging.warning("Attempting to close position when none exists!")
            return 0.0
        
        realized_pnl = self.current_position.unrealized_pnl(exit_price)
        self.total_pnl += realized_pnl
        self.trade_count += 1
        
        # Create a new Trade record and add it to our history
        trade = Trade(
            symbol=self.current_position.symbol,
            side=self.current_position.side,
            entry_price=self.current_position.entry_price,
            exit_price=exit_price,
            size=self.current_position.size,
            entry_time=self.current_position.entry_time.isoformat(),
            exit_time=datetime.now().isoformat(),
            pnl=realized_pnl
        )
        self.trade_history.append(trade)

        logging.info(f"Position closed. Realized P&L: {realized_pnl:.4f} USDT")
        logging.info(f"Total P&L: {self.total_pnl:.4f} USDT | Trades: {self.trade_count}")
        
        self.current_position = None
        return realized_pnl
    
    def get_status(self, current_price: float = None) -> dict:
        """Get current position status including full trade history."""
        if not self.current_position:
            return {
                "in_position": False,
                "total_pnl": self.total_pnl,
                "trade_history": [asdict(t) for t in self.trade_history] # Convert trades to dicts
            }
        
        status = {
            "in_position": True,
            "symbol": self.current_position.symbol,
            "side": self.current_position.side,
            "size": self.current_position.size,
            "entry_price": self.current_position.entry_price,
            "total_pnl": self.total_pnl,
            "trade_history": [asdict(t) for t in self.trade_history]
        }
        
        if current_price:
            status.update({
                "current_price": current_price,
                "unrealized_pnl": self.current_position.unrealized_pnl(current_price),
                "pnl_percentage": self.current_position.pnl_percentage(current_price)
            })
        
        return status