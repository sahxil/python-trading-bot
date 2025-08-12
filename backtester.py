import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from dataclasses import dataclass

@dataclass
class BacktestTrade:
    """Represents a single trade in backtesting."""
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    side: str
    quantity: float
    pnl: float
    pnl_pct: float
    duration_minutes: int

class AdvancedBacktester:
    """Comprehensive backtesting framework with detailed analytics."""
    
    def __init__(self, initial_balance: float = 10000):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.trades: List[BacktestTrade] = []
        self.equity_curve: List[Tuple[datetime, float]] = []
        
    def run_backtest(self, 
                     df: pd.DataFrame, 
                     strategy_class,
                     strategy_params: Dict[str, Any] = None,
                     commission_rate: float = 0.001,
                     slippage_pct: float = 0.01) -> Dict[str, Any]:
        """Run comprehensive backtest with detailed metrics."""
        
        if strategy_params is None:
            strategy_params = {}
        
        strategy = strategy_class(**strategy_params)
        
        self.trades = []
        self.equity_curve = [(df.iloc[0]['Open_Time'], self.initial_balance)]
        self.current_balance = self.initial_balance
        
        position = None
        
        logging.info(f"Starting backtest with {len(df)} data points")
        
        for i in range(30, len(df)):  # Start after enough data for indicators
            current_data = df.iloc[:i+1]
            current_row = df.iloc[i]
            
            signal = strategy.generate_signal(current_data)
            current_price = current_row['Close']
            
            # Apply slippage
            if signal == 'BUY':
                execution_price = current_price * (1 + slippage_pct / 100)
            elif signal == 'SELL':
                execution_price = current_price * (1 - slippage_pct / 100)
            else:
                execution_price = current_price
            
            # Execute trades
            if signal == 'BUY' and position is None:
                # Open long position
                quantity = (self.current_balance * 0.98) / execution_price  # Use 98% of balance
                commission = quantity * execution_price * commission_rate
                
                position = {
                    'side': 'LONG',
                    'entry_time': current_row['Open_Time'],
                    'entry_price': execution_price,
                    'quantity': quantity,
                    'commission': commission
                }
                
                self.current_balance -= commission
                
            elif signal == 'SELL' and position is not None:
                # Close long position
                pnl_gross = (execution_price - position['entry_price']) * position['quantity']
                commission = position['quantity'] * execution_price * commission_rate
                pnl_net = pnl_gross - commission - position['commission']
                
                self.current_balance += position['quantity'] * execution_price - commission
                
                # Record trade
                duration = (current_row['Open_Time'] - position['entry_time']).total_seconds() / 60
                pnl_pct = (pnl_net / (position['entry_price'] * position['quantity'])) * 100
                
                trade = BacktestTrade(
                    entry_time=position['entry_time'],
                    exit_time=current_row['Open_Time'],
                    entry_price=position['entry_price'],
                    exit_price=execution_price,
                    side=position['side'],
                    quantity=position['quantity'],
                    pnl=pnl_net,
                    pnl_pct=pnl_pct,
                    duration_minutes=int(duration)
                )
                
                self.trades.append(trade)
                position = None
            
            # Record equity curve
            portfolio_value = self.current_balance
            if position:
                unrealized_pnl = (current_price - position['entry_price']) * position['quantity']
                portfolio_value += position['entry_price'] * position['quantity'] + unrealized_pnl
            
            self.equity_curve.append((current_row['Open_Time'], portfolio_value))
        
        return self._calculate_metrics()
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""
        if not self.trades:
            return {"error": "No trades executed"}
        
        # Basic metrics
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl <= 0]
        
        win_rate = len(winning_trades) / total_trades * 100
        
        total_pnl = sum(t.pnl for t in self.trades)
        total_return_pct = (self.current_balance / self.initial_balance - 1) * 100
        
        # Risk metrics
        returns = [t.pnl_pct for t in self.trades]
        avg_return = np.mean(returns)
        return_std = np.std(returns)
        
        sharpe_ratio = avg_return / return_std if return_std > 0 else 0
        
        # Drawdown calculation
        equity_values = [eq[1] for eq in self.equity_curve]
        peak = equity_values[0]
        max_drawdown = 0
        
        for value in equity_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Average trade metrics
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        # Trade duration
        avg_duration = np.mean([t.duration_minutes for t in self.trades])
        
        return {
            "summary": {
                "total_trades": total_trades,
                "win_rate": round(win_rate, 2),
                "total_pnl": round(total_pnl, 2),
                "total_return_pct": round(total_return_pct, 2),
                "final_balance": round(self.current_balance, 2)
            },
            "risk_metrics": {
                "sharpe_ratio": round(sharpe_ratio, 3),
                "max_drawdown_pct": round(max_drawdown, 2),
                "volatility": round(return_std, 2)
            },
            "trade_analysis": {
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "profit_factor": round(profit_factor, 2),
                "avg_duration_minutes": round(avg_duration, 1),
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades)
            },
            "equity_curve": self.equity_curve,
            "all_trades": self.trades
        }
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive text report."""
        report = f"""
BACKTESTING REPORT
{'='*50}

SUMMARY METRICS:
• Total Trades: {results['summary']['total_trades']}
• Win Rate: {results['summary']['win_rate']}%
• Total P&L: ${results['summary']['total_pnl']}
• Total Return: {results['summary']['total_return_pct']}%
• Final Balance: ${results['summary']['final_balance']}

RISK METRICS:
• Sharpe Ratio: {results['risk_metrics']['sharpe_ratio']}
• Max Drawdown: {results['risk_metrics']['max_drawdown_pct']}%
• Volatility: {results['risk_metrics']['volatility']}%

TRADE ANALYSIS:
• Average Win: ${results['trade_analysis']['avg_win']}
• Average Loss: ${results['trade_analysis']['avg_loss']}
• Profit Factor: {results['trade_analysis']['profit_factor']}
• Average Duration: {results['trade_analysis']['avg_duration_minutes']} minutes
• Winning Trades: {results['trade_analysis']['winning_trades']}
• Losing Trades: {results['trade_analysis']['losing_trades']}

RECENT TRADES:
"""
        
        # Add last 5 trades
        for trade in self.trades[-5:]:
            pnl_sign = "+" if trade.pnl >= 0 else ""
            report += f"• {trade.side} @ ${trade.entry_price:.2f} → ${trade.exit_price:.2f} | "
            report += f"P&L: {pnl_sign}${trade.pnl:.2f} ({pnl_sign}{trade.pnl_pct:.2f}%)\n"
        
        return report