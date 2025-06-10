import backtrader as bt
import numpy as np

class VolatilityBreakoutStrategy(bt.Strategy):
    """
    Strategy that trades breakouts from volatility bands with dynamic position sizing
    """
    params = dict(
        atr_period=14,
        atr_multiplier=2.0,
        min_volume=100,
        risk_per_trade=0.02,  # 2% risk per trade
        trailing_stop=0.03,   # 3% trailing stop
        profit_target=0.06    # 6% profit target
    )

    def __init__(self):
        # Volatility indicators
        self.atr = bt.indicators.ATR(period=self.p.atr_period)
        self.upper_band = bt.indicators.BollingerBands(period=20, devfactor=2.0).top
        self.lower_band = bt.indicators.BollingerBands(period=20, devfactor=2.0).bot
        
        # Volume filter
        self.volume_ma = bt.indicators.SMA(self.data.volume, period=20)
        self.volume_ratio = self.data.volume / self.volume_ma
        
        # Trend filter
        self.ema_fast = bt.indicators.EMA(period=10)
        self.ema_slow = bt.indicators.EMA(period=30)
        
        # For position tracking
        self.entry_price = None
        self.stop_price = None
        self.trailing_stop_price = None

    def next(self):
        if self.position:
            # Update trailing stop
            if self.position.size > 0:  # Long position
                if self.data.close[0] > self.trailing_stop_price:
                    self.trailing_stop_price = self.data.close[0] * (1 - self.p.trailing_stop)
                elif self.data.close[0] < self.trailing_stop_price:
                    self.close()
            else:  # Short position
                if self.data.close[0] < self.trailing_stop_price:
                    self.trailing_stop_price = self.data.close[0] * (1 + self.p.trailing_stop)
                elif self.data.close[0] > self.trailing_stop_price:
                    self.close()
            
            # Check profit target
            if self.position.size > 0:  # Long position
                if self.data.close[0] > self.entry_price * (1 + self.p.profit_target):
                    self.close()
            else:  # Short position
                if self.data.close[0] < self.entry_price * (1 - self.p.profit_target):
                    self.close()
        else:
            # Check volume
            if self.volume_ratio[0] < 0.5:
                return
                
            # Check trend
            trend_up = self.ema_fast[0] > self.ema_slow[0]
            trend_down = self.ema_fast[0] < self.ema_slow[0]
            
            # Calculate position size based on ATR
            risk_amount = self.broker.getvalue() * self.p.risk_per_trade
            position_size = risk_amount / (self.atr[0] * self.p.atr_multiplier)
            
            # Entry conditions
            if trend_up and self.data.close[0] > self.upper_band[0]:
                self.buy(size=position_size)
                self.entry_price = self.data.close[0]
                self.stop_price = self.entry_price - (self.atr[0] * self.p.atr_multiplier)
                self.trailing_stop_price = self.entry_price * (1 - self.p.trailing_stop)
            elif trend_down and self.data.close[0] < self.lower_band[0]:
                self.sell(size=position_size)
                self.entry_price = self.data.close[0]
                self.stop_price = self.entry_price + (self.atr[0] * self.p.atr_multiplier)
                self.trailing_stop_price = self.entry_price * (1 + self.p.trailing_stop)

class MeanReversionWithMomentum(bt.Strategy):
    """
    Combines mean reversion with momentum indicators and adaptive position sizing
    """
    params = dict(
        period=20,
        zentry=2.0,
        zexit=0.5,
        rsi_period=14,
        rsi_threshold=30,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
        vol_period=20,
        vol_threshold=0.02,
        risk_per_trade=0.02
    )

    def __init__(self):
        # Mean reversion indicators
        self.ma = bt.indicators.EMA(self.data.close, period=self.p.period)
        self.std = bt.indicators.StandardDeviation(self.data.close, period=self.p.period)
        
        # Momentum indicators
        self.rsi = bt.indicators.RSI(period=self.p.rsi_period)
        self.macd = bt.indicators.MACD(
            period_me1=self.p.macd_fast,
            period_me2=self.p.macd_slow,
            period_signal=self.p.macd_signal
        )
        
        # Volatility filter
        self.volatility = bt.indicators.StandardDeviation(self.data.close, period=self.p.vol_period)
        self.vol_ratio = self.volatility / self.ma
        
        # For position tracking
        self.entry_price = None
        self.stop_price = None

    def next(self):
        # Calculate z-score
        std = self.std[0] if self.std[0] != 0 else 1e-8
        zscore = (self.data.close[0] - self.ma[0]) / std
        
        # Calculate position size based on volatility
        risk_amount = self.broker.getvalue() * self.p.risk_per_trade
        position_size = risk_amount / (self.volatility[0] * 2)
        
        if self.position:
            # Exit conditions
            if abs(zscore) < self.p.zexit:
                self.close()
            elif self.position.size > 0:  # Long position
                if self.macd.macd[0] < self.macd.signal[0]:
                    self.close()
            else:  # Short position
                if self.macd.macd[0] > self.macd.signal[0]:
                    self.close()
        else:
            # Entry conditions
            if self.vol_ratio[0] < self.p.vol_threshold:
                if (zscore < -self.p.zentry and 
                    self.rsi[0] < self.p.rsi_threshold and 
                    self.macd.macd[0] > self.macd.signal[0]):
                    self.buy(size=position_size)
                    self.entry_price = self.data.close[0]
                    self.stop_price = self.entry_price * 0.95  # 5% stop loss
                elif (zscore > self.p.zentry and 
                      self.rsi[0] > (100 - self.p.rsi_threshold) and 
                      self.macd.macd[0] < self.macd.signal[0]):
                    self.sell(size=position_size)
                    self.entry_price = self.data.close[0]
                    self.stop_price = self.entry_price * 1.05  # 5% stop loss

class AdaptiveTrendFollowing(bt.Strategy):
    """
    Adaptive trend following strategy using multiple timeframes and dynamic position sizing
    """
    params = dict(
        fast_period=10,
        slow_period=30,
        signal_period=5,
        atr_period=14,
        atr_multiplier=2.0,
        risk_per_trade=0.02,
        trailing_stop=0.03,
        profit_target=0.06
    )

    def __init__(self):
        # Trend indicators
        self.fast_ema = bt.indicators.EMA(period=self.p.fast_period)
        self.slow_ema = bt.indicators.EMA(period=self.p.slow_period)
        self.signal = bt.indicators.EMA(self.fast_ema, period=self.p.signal_period)
        
        # Volatility indicator
        self.atr = bt.indicators.ATR(period=self.p.atr_period)
        
        # Volume filter
        self.volume_ma = bt.indicators.SMA(self.data.volume, period=20)
        self.volume_ratio = self.data.volume / self.volume_ma
        
        # For position tracking
        self.entry_price = None
        self.stop_price = None
        self.trailing_stop_price = None

    def next(self):
        if self.position:
            # Update trailing stop
            if self.position.size > 0:  # Long position
                if self.data.close[0] > self.trailing_stop_price:
                    self.trailing_stop_price = self.data.close[0] * (1 - self.p.trailing_stop)
                elif self.data.close[0] < self.trailing_stop_price:
                    self.close()
            else:  # Short position
                if self.data.close[0] < self.trailing_stop_price:
                    self.trailing_stop_price = self.data.close[0] * (1 + self.p.trailing_stop)
                elif self.data.close[0] > self.trailing_stop_price:
                    self.close()
            
            # Check profit target
            if self.position.size > 0:  # Long position
                if self.data.close[0] > self.entry_price * (1 + self.p.profit_target):
                    self.close()
            else:  # Short position
                if self.data.close[0] < self.entry_price * (1 - self.p.profit_target):
                    self.close()
        else:
            # Check volume
            if self.volume_ratio[0] < 0.5:
                return
            
            # Calculate position size based on ATR
            risk_amount = self.broker.getvalue() * self.p.risk_per_trade
            position_size = risk_amount / (self.atr[0] * self.p.atr_multiplier)
            
            # Entry conditions
            if (self.fast_ema[0] > self.slow_ema[0] and 
                self.fast_ema[0] > self.signal[0] and 
                self.data.close[0] > self.fast_ema[0]):
                self.buy(size=position_size)
                self.entry_price = self.data.close[0]
                self.stop_price = self.entry_price - (self.atr[0] * self.p.atr_multiplier)
                self.trailing_stop_price = self.entry_price * (1 - self.p.trailing_stop)
            elif (self.fast_ema[0] < self.slow_ema[0] and 
                  self.fast_ema[0] < self.signal[0] and 
                  self.data.close[0] < self.fast_ema[0]):
                self.sell(size=position_size)
                self.entry_price = self.data.close[0]
                self.stop_price = self.entry_price + (self.atr[0] * self.p.atr_multiplier)
                self.trailing_stop_price = self.entry_price * (1 + self.p.trailing_stop) 