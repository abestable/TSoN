import backtrader as bt
import random
import numpy as np
import csv
import os
try:
    from numba import jit
    numba_available = True
except ImportError:
    numba_available = False

def calculate_exit_prices_py(entry_price, tp, sl, position_type):
    if position_type == 'long':
        tp_price = entry_price * (1 + tp)
        sl_price = entry_price * (1 - sl)
    else:  # short
        tp_price = entry_price * (1 - tp)
        sl_price = entry_price * (1 + sl)
    return tp_price, sl_price

if numba_available:
    @jit(nopython=True)
    def calculate_exit_prices_numba(entry_price, tp, sl, position_type):
        if position_type == 'long':
            tp_price = entry_price * (1 + tp)
            sl_price = entry_price * (1 - sl)
        else:  # short
            tp_price = entry_price * (1 - tp)
            sl_price = entry_price * (1 + sl)
        return tp_price, sl_price
else:
    calculate_exit_prices_numba = calculate_exit_prices_py

class RandomEntryTPSL(bt.Strategy):
    params = (
        ('entry_period', 10),   # Bars between entries
        ('size_pct', 0.001),    # Fraction of capital to use
        ('tp', 0.01),           # Take profit percent
        ('sl', 0.01),           # Stop loss percent
        ('max_hold', 30),       # Max bars in position
        ('trade_type', 'LONG'), # Tipo di trade (LONG, SHORT, BOTH)
        ('use_numba', True),
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
        # Pre-allocate arrays for price history
        self.price_history = np.zeros(self.p.max_hold)
        self.price_idx = 0
        # Scegli la funzione di calcolo in base a use_numba
        if hasattr(self.p, 'use_numba') and self.p.use_numba and numba_available:
            self.calculate_exit_prices = calculate_exit_prices_numba
        else:
            self.calculate_exit_prices = calculate_exit_prices_py
        # Apri il file di log
        self.log_file = open("trade_log_py.csv", "w", newline='')
        self.log_writer = csv.writer(self.log_file)
        self.log_writer.writerow(["bar_index", "datetime", "event", "price", "size", "side", "exit_reason", "pnl"])

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
        
        # Update price history efficiently
        self.price_history = np.roll(self.price_history, -1)
        self.price_history[-1] = price
        
        if not self.position and (len(self) - self.last_entry) >= self.p.entry_period:
            cash = self.broker.getvalue() * self.p.size_pct
            size = cash / price  # Usa posizioni frazionarie
            if size >= 0.001:
                ttype = self.trade_type.upper() if hasattr(self, 'trade_type') else 'LONG'
                if ttype == 'LONG':
                    self.order = self.buy(size=size)
                    self.position_type = 'long'
                elif ttype == 'SHORT':
                    self.order = self.sell(size=size)
                    self.position_type = 'short'
                elif ttype == 'BOTH':
                    if random.choice([True, False]):
                        self.order = self.buy(size=size)
                        self.position_type = 'long'
                    else:
                        self.order = self.sell(size=size)
                        self.position_type = 'short'
                self.entry_price = price
                self.last_entry = len(self)
                self.bar_in_trade = 0
                # Log dell'apertura
                self.log_writer.writerow([len(self), self.data.datetime.datetime(0), "open", price, size, self.position_type, "-", 0])
        elif self.position:
            self.bar_in_trade += 1
            
            # Calculate exit prices using Numba-optimized function
            tp_price, sl_price = self.calculate_exit_prices(
                self.entry_price, 
                self.p.tp, 
                self.p.sl, 
                self.position_type
            )
            
            tp_hit = sl_hit = False
            if self.position_type == 'long':
                tp_hit = price >= tp_price
                sl_hit = price <= sl_price
            elif self.position_type == 'short':
                tp_hit = price <= tp_price
                sl_hit = price >= sl_price
                
            if tp_hit:
                self.exit_tp += 1
                self.close()
                self.position_type = None
                # Log della chiusura
                self.log_writer.writerow([len(self), self.data.datetime.datetime(0), "close", price, self.position.size, self.position_type, "TP", self.position.size * (price - self.entry_price)])
            elif sl_hit:
                self.exit_sl += 1
                self.close()
                self.position_type = None
                # Log della chiusura
                self.log_writer.writerow([len(self), self.data.datetime.datetime(0), "close", price, self.position.size, self.position_type, "SL", self.position.size * (price - self.entry_price)])
            elif self.bar_in_trade >= self.p.max_hold:
                self.exit_time += 1
                self.close()
                self.position_type = None
                # Log della chiusura
                self.log_writer.writerow([len(self), self.data.datetime.datetime(0), "close", price, self.position.size, self.position_type, "Time", self.position.size * (price - self.entry_price)])

    def __del__(self):
        if hasattr(self, 'log_file'):
            self.log_file.close() 