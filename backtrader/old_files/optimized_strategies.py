import backtrader as bt
import numpy as np

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

    def next(self):
        if len(self.dataclose) < self.p.period:
            return
        # Calculate rolling mean and std
        window = np.array([self.dataclose[-i] for i in range(self.p.period, 0, -1)])
        mean = np.mean(window)
        std = np.std(window)
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