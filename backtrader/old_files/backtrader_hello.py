import backtrader as bt

# Strategia minimale
class TestStrategy(bt.Strategy):
    def __init__(self):
        self.sma = bt.ind.SMA(period=10)

    def next(self):
        if not self.position:
            if self.data.close[0] > self.sma[0]:
                self.buy()
        else:
            if self.data.close[0] < self.sma[0]:
                self.sell()

# Crea Cerebro
cerebro = bt.Cerebro()
cerebro.addstrategy(TestStrategy)

# Dati fittizi in pandas
import pandas as pd
import numpy as np
dates = pd.date_range('2024-01-01', periods=100)
prices = 100 + np.random.randn(100).cumsum()
df = pd.DataFrame({
    'close': prices,
    'open': prices,
    'high': prices + 1,
    'low': prices - 1,
    'volume': 1000  # volume fittizio costante
}, index=dates)


data = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data)

# Avvia e mostra il risultato
cerebro.run()
cerebro.plot()
