import backtrader as bt
import random

class RandomEntryTPSL(bt.Strategy):
    params = (
        ('entry_period', 10),   # Bars between entries
        ('size_pct', 0.001),    # Fraction of capital to use
        ('tp', 0.01),           # Take profit percent
        ('sl', 0.01),           # Stop loss percent
        ('max_hold', 30),       # Max bars in position
    )

    def __init__(self):
        self.last_entry = -self.p.entry_period
        self.order = None
        self.entry_price = None
        self.trade_count = 0
        self.bar_in_trade = 0
        self.position_type = None  # 'long' or 'short'
        # Exit counters
        self.exit_tp = 0
        self.exit_sl = 0
        self.exit_time = 0

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.trade_count += 1
            elif order.issell():
                pass

    def next(self):
        price = self.data.close[0]
        pos = self.position.size
        if not self.position and (len(self) - self.last_entry) >= self.p.entry_period:
            cash = self.broker.getvalue() * self.p.size_pct
            size = int(cash / price)
            if size > 0:
                # Trade type logic
                if hasattr(self, 'trade_type'):
                    ttype = self.trade_type.upper()
                else:
                    ttype = 'LONG'
                if ttype == 'LONG':
                    self.order = self.buy(size=size)
                    self.position_type = 'long'
                elif ttype == 'SHORT':
                    self.order = self.sell(size=size)
                    self.position_type = 'short'
                elif ttype == 'BOTH':
                    # Randomly choose long or short
                    if random.choice([True, False]):
                        self.order = self.buy(size=size)
                        self.position_type = 'long'
                    else:
                        self.order = self.sell(size=size)
                        self.position_type = 'short'
                self.entry_price = price
                self.last_entry = len(self)
                self.bar_in_trade = 0
        elif self.position:
            self.bar_in_trade += 1
            tp_hit = sl_hit = False
            if self.entry_price:
                if self.position_type == 'long':
                    tp_hit = price >= self.entry_price * (1 + self.p.tp)
                    sl_hit = price <= self.entry_price * (1 - self.p.sl)
                elif self.position_type == 'short':
                    tp_hit = price <= self.entry_price * (1 - self.p.tp)
                    sl_hit = price >= self.entry_price * (1 + self.p.sl)
                if tp_hit:
                    self.exit_tp += 1
                    self.close()
                    self.position_type = None
                elif sl_hit:
                    self.exit_sl += 1
                    self.close()
                    self.position_type = None
                elif self.bar_in_trade >= self.p.max_hold:
                    self.exit_time += 1
                    self.close()
                    self.position_type = None 