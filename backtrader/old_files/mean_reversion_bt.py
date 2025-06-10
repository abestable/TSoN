import backtrader as bt

class MeanReversionStrategy(bt.Strategy):
    params = dict(
        period=50,    # Periodo per MA e deviazione standard
        zentry=2.0,   # Z-score soglia per entrare
        zexit=0.5     # Z-score soglia per uscire
    )

    def __init__(self):
        self.ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.period)
        self.std = bt.indicators.StandardDeviation(self.data.close, period=self.p.period)
        self.zscore = (self.data.close - self.ma) / self.std

    def next(self):
        if self.position:
            if abs(self.zscore[0]) < self.p.zexit:
                self.close()
        else:
            if self.zscore[0] > self.p.zentry:
                self.sell()
            elif self.zscore[0] < -self.p.zentry:
                self.buy()
