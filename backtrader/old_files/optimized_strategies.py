import backtrader as bt
import numpy as np
from numba import jit

@jit(nopython=True)
def calculate_stats(window):
    mean = np.mean(window)
    std = np.std(window)
    return mean, std

class SimpleMeanReversion(bt.Strategy):
    params = (
        ('period', 50),      # Lookback period for mean and std
        ('zentry', 2.0),     # Z-score entry threshold
        ('zexit', 0.5),      # Z-score exit threshold
        ('size', 1.0),       # Position size (fraction of portfolio)
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.returns = bt.indicators.PercentChange(self.dataclose, period=1)
        self.order = None
        self.window = np.zeros(self.p.period)

    def next(self):
        if len(self.dataclose) < self.p.period:
            return
            
        # Update window with new data
        for i in range(self.p.period):
            self.window[i] = self.dataclose[-i-1]
            
        # Calculate statistics using Numba-optimized function
        mean, std = calculate_stats(self.window)
        
        price = self.dataclose[0]
        zscore = (price - mean) / (std if std > 0 else 1e-8)

        # Entry/exit logic
        if not self.position:
            if zscore < -self.p.zentry:
                # Price much lower than mean: buy
                size = int(self.broker.getvalue() * self.p.size / price)
                if size > 0:
                    self.order = self.buy(size=size)
            elif zscore > self.p.zentry:
                # Price much higher than mean: sell/short
                size = int(self.broker.getvalue() * self.p.size / price)
                if size > 0:
                    self.order = self.sell(size=size)
        else:
            if abs(zscore) < self.p.zexit:
                self.close() 