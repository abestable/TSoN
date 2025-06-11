import backtrader as bt
import numpy as np

class MeanReversionEMA(bt.Strategy):
    params = dict(
        period=50,
        zentry=2.0,
        zexit=0.5
    )

    def __init__(self):
        # Pre-allocate arrays for better performance
        self.prices = np.zeros(self.p.period)
        self.ma = bt.indicators.EMA(self.data.close, period=self.p.period)
        self.std = bt.indicators.StandardDeviation(self.data.close, period=self.p.period)
        self.zscore = (self.data.close - self.ma) / self.std
        
        # Cache for position management
        self.position_size = 0
        self.entry_price = 0

    def next(self):
        # Update price array efficiently
        self.prices = np.roll(self.prices, -1)
        self.prices[-1] = self.data.close[0]
        
        if self.position:
            if abs(self.zscore[0]) < self.p.zexit:
                self.close()
        else:
            if self.zscore[0] > self.p.zentry:
                self.position_size = int(self.broker.getvalue() * 0.95 / self.data.close[0])
                self.entry_price = self.data.close[0]
                self.sell(size=self.position_size)
            elif self.zscore[0] < -self.p.zentry:
                self.position_size = int(self.broker.getvalue() * 0.95 / self.data.close[0])
                self.entry_price = self.data.close[0]
                self.buy(size=self.position_size)

class MeanReversionWithVolatility(bt.Strategy):
    params = dict(
        period=50,
        zentry=2.0,
        zexit=0.5,
        vol_period=20,
        vol_threshold=0.02,
        stop_loss=0.05,        # 5% stop loss
        take_profit=0.08,      # 8% take profit
        trailing_stop=0.03,    # 3% trailing stop
        min_volume=100,        # Lower volume threshold
        rsi_period=14,         # RSI period
        rsi_threshold=40,      # Less restrictive RSI threshold
        trend_period=200       # Long-term trend period
    )

    def __init__(self):
        # Mean Reversion indicators
        self.ma = bt.indicators.EMA(self.data.close, period=self.p.period)
        self.std = bt.indicators.StandardDeviation(self.data.close, period=self.p.period)
        self.volatility = bt.indicators.StandardDeviation(self.data.close, period=self.p.vol_period)
        self.vol_ratio = self.volatility / self.ma
        
        # Trend filter
        self.trend_ma = bt.indicators.EMA(self.data.close, period=self.p.trend_period)
        
        # RSI for trend filter
        self.rsi = bt.indicators.RSI(period=self.p.rsi_period)
        
        # Volume filter (using relative volume)
        self.volume_ma = bt.indicators.SMA(self.data.volume, period=20)
        self.volume_ratio = self.data.volume / self.volume_ma
        
        # For trailing stop
        self.highest = bt.indicators.Highest(self.data.high, period=20)
        self.lowest = bt.indicators.Lowest(self.data.low, period=20)
        
        # Track entry price for stop loss and take profit
        self.entry_price = None
        self.stop_price = None
        self.trailing_stop_price = None

    def next(self):
        # Prevent division by zero
        std = self.std[0] if self.std[0] != 0 else 1e-8
        zscore = (self.data.close[0] - self.ma[0]) / std
        
        # Check if we have a position
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
            
            # Check stop loss and take profit
            if self.position.size > 0:  # Long position
                if self.data.close[0] < self.stop_price:
                    self.close()
                elif self.data.close[0] > self.entry_price * (1 + self.p.take_profit):
                    self.close()
            else:  # Short position
                if self.data.close[0] > self.stop_price:
                    self.close()
                elif self.data.close[0] < self.entry_price * (1 - self.p.take_profit):
                    self.close()
            
            # Check zscore exit
            if abs(zscore) < self.p.zexit:
                self.close()
                
        else:
            # Check volume filter (relative volume)
            if self.volume_ratio[0] < 0.5:  # Volume at least 50% of average
                return
                
            # Check volatility filter
            if self.vol_ratio[0] < self.p.vol_threshold:
                # Check trend direction
                trend_up = self.data.close[0] > self.trend_ma[0]
                trend_down = self.data.close[0] < self.trend_ma[0]
                
                # Check RSI conditions (less restrictive)
                if zscore > self.p.zentry and self.rsi[0] > (100 - self.p.rsi_threshold) and trend_down:
                    self.sell()
                    self.entry_price = self.data.close[0]
                    self.stop_price = self.entry_price * (1 + self.p.stop_loss)
                    self.trailing_stop_price = self.entry_price * (1 + self.p.trailing_stop)
                elif zscore < -self.p.zentry and self.rsi[0] < self.p.rsi_threshold and trend_up:
                    self.buy()
                    self.entry_price = self.data.close[0]
                    self.stop_price = self.entry_price * (1 - self.p.stop_loss)
                    self.trailing_stop_price = self.entry_price * (1 - self.p.trailing_stop)

class MeanReversionWithTrend(bt.Strategy):
    params = dict(
        period=50,
        zentry=2.0,
        zexit=0.5,
        trend_period=200
    )

    def __init__(self):
        self.ma = bt.indicators.EMA(self.data.close, period=self.p.period)
        self.std = bt.indicators.StandardDeviation(self.data.close, period=self.p.period)
        self.zscore = (self.data.close - self.ma) / self.std
        self.trend_ma = bt.indicators.EMA(self.data.close, period=self.p.trend_period)

    def next(self):
        if self.position:
            if abs(self.zscore[0]) < self.p.zexit:
                self.close()
        else:
            # Only take long trades in uptrend, short trades in downtrend
            if self.data.close[0] > self.trend_ma[0]:  # Uptrend
                if self.zscore[0] < -self.p.zentry:
                    self.buy()
            else:  # Downtrend
                if self.zscore[0] > self.p.zentry:
                    self.sell()

class MeanReversionWithRSI(bt.Strategy):
    params = dict(
        period=50,
        zentry=2.0,
        zexit=0.5,
        rsi_period=14,
        rsi_oversold=30,
        rsi_overbought=70
    )

    def __init__(self):
        self.ma = bt.indicators.EMA(self.data.close, period=self.p.period)
        self.std = bt.indicators.StandardDeviation(self.data.close, period=self.p.period)
        self.zscore = (self.data.close - self.ma) / self.std
        self.rsi = bt.indicators.RSI(period=self.p.rsi_period)

    def next(self):
        if self.position:
            if abs(self.zscore[0]) < self.p.zexit:
                self.close()
        else:
            if self.zscore[0] > self.p.zentry and self.rsi[0] > self.p.rsi_overbought:
                self.sell()
            elif self.zscore[0] < -self.p.zentry and self.rsi[0] < self.p.rsi_oversold:
                self.buy()

class MeanReversionWithVolume(bt.Strategy):
    params = dict(
        period=50,
        zentry=2.0,
        zexit=0.5,
        volume_period=20
    )

    def __init__(self):
        self.ma = bt.indicators.EMA(self.data.close, period=self.p.period)
        self.std = bt.indicators.StandardDeviation(self.data.close, period=self.p.period)
        self.zscore = (self.data.close - self.ma) / self.std
        self.volume_ma = bt.indicators.SMA(self.data.volume, period=self.p.volume_period)

    def next(self):
        if self.position:
            if abs(self.zscore[0]) < self.p.zexit:
                self.close()
        else:
            # Only trade when volume is above average
            if self.data.volume[0] > self.volume_ma[0]:
                if self.zscore[0] > self.p.zentry:
                    self.sell()
                elif self.zscore[0] < -self.p.zentry:
                    self.buy() 