# strategies/strategy_framework.py
from abc import ABC, abstractmethod
import pandas as pd
import logging
from typing import Tuple, Dict, Any
import pandas_ta as ta # <--- ADD THIS LINE

class TradingStrategy(ABC):
    # ... (rest of the class is unchanged)
    """Base class for all trading strategies."""
    
    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> str:
        """Generate trading signal: 'BUY', 'SELL', or 'HOLD'."""
        pass
    
    @abstractmethod
    def get_confidence(self, df: pd.DataFrame) -> float:
        """Return confidence score (0-1) for the signal."""
        pass

class RSIStrategy(TradingStrategy):
    # ... (rest of the class is unchanged)
    """RSI-based trading strategy."""
    
    def __init__(self, period: int = 14, overbought: float = 70, oversold: float = 30):
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
    
    def generate_signal(self, df: pd.DataFrame) -> str:
        if len(df) < self.period:
            return 'HOLD'
        
        df.ta.rsi(length=self.period, append=True)
        latest_rsi = df[f'RSI_{self.period}'].iloc[-1]
        
        if latest_rsi > self.overbought:
            return 'SELL'
        elif latest_rsi < self.oversold:
            return 'BUY'
        return 'HOLD'
    
    def get_confidence(self, df: pd.DataFrame) -> float:
        if len(df) < self.period:
            return 0.0
        
        df.ta.rsi(length=self.period, append=True)
        latest_rsi = df[f'RSI_{self.period}'].iloc[-1]
        
        # Higher confidence the further from neutral (50)
        return abs(latest_rsi - 50) / 50

class MACDStrategy(TradingStrategy):
    # ... (rest of the class is unchanged)
    """MACD crossover strategy."""
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal = signal
    
    def generate_signal(self, df: pd.DataFrame) -> str:
        if len(df) < max(self.fast, self.slow, self.signal) + 1:
            return 'HOLD'
        
        df.ta.macd(fast=self.fast, slow=self.slow, signal=self.signal, append=True)
        
        current_macd = df['MACD_12_26_9'].iloc[-1]
        current_signal = df['MACDs_12_26_9'].iloc[-1]
        prev_macd = df['MACD_12_26_9'].iloc[-2]
        prev_signal = df['MACDs_12_26_9'].iloc[-2]
        
        # Bullish crossover
        if prev_macd <= prev_signal and current_macd > current_signal:
            return 'BUY'
        # Bearish crossover
        elif prev_macd >= prev_signal and current_macd < current_signal:
            return 'SELL'
        
        return 'HOLD'
    
    def get_confidence(self, df: pd.DataFrame) -> float:
        if len(df) < max(self.fast, self.slow, self.signal) + 1:
            return 0.0
        
        df.ta.macd(fast=self.fast, slow=self.slow, signal=self.signal, append=True)
        
        current_macd = df['MACD_12_26_9'].iloc[-1]
        current_signal = df['MACDs_12_26_9'].iloc[-1]
        
        # Confidence based on distance between MACD and signal line
        diff = abs(current_macd - current_signal)
        return min(diff / 10, 1.0)  # Normalize to 0-1

class EnsembleStrategy:
    # ... (rest of the class is unchanged)
    """Combine multiple strategies with weighted voting."""
    
    def __init__(self):
        self.strategies = [
            ('RSI', RSIStrategy(), 0.6),
            ('MACD', MACDStrategy(), 0.4)
        ]
    
    def analyze_and_get_signal(self, df: pd.DataFrame) -> Tuple[str, Dict[str, Any]]:
        """Get ensemble signal with detailed breakdown."""
        signals = {}
        weighted_votes = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        
        for name, strategy, weight in self.strategies:
            signal = strategy.generate_signal(df)
            confidence = strategy.get_confidence(df)
            
            signals[name] = {
                'signal': signal,
                'confidence': confidence,
                'weight': weight,
                'weighted_confidence': confidence * weight
            }
            
            weighted_votes[signal] += confidence * weight
        
        # Get final signal
        final_signal = max(weighted_votes, key=weighted_votes.get)
        
        # Require minimum threshold for non-HOLD signals
        if final_signal != 'HOLD' and weighted_votes[final_signal] < 0.3:
            final_signal = 'HOLD'
        
        analysis = {
            'final_signal': final_signal,
            'strategy_breakdown': signals,
            'weighted_votes': weighted_votes,
            'total_confidence': sum(s['weighted_confidence'] for s in signals.values())
        }
        
        logging.info(f"Ensemble Analysis: {final_signal} | Confidence: {analysis['total_confidence']:.2f}")
        for name, data in signals.items():
            logging.info(f"  {name}: {data['signal']} (conf: {data['confidence']:.2f})")
        
        return final_signal, analysis