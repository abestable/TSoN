import tkinter as tk
from tkinter import ttk
from tkinter import PhotoImage
import threading
from random_entry_strategy import RandomEntryTPSL
import backtrader as bt
import pandas as pd
from datetime import datetime
import time
import os
from PIL import Image, ImageTk

class ProgressStrategy(RandomEntryTPSL):
    def __init__(self, *args, **kwargs):
        self.progress_callback = kwargs.pop('progress_callback', None)
        self.total_bars = kwargs.pop('total_bars', 0)
        self.max_hold = kwargs.pop('max_hold', 0)
        self.trade_type = kwargs.pop('trade_type', 'LONG')
        super().__init__(*args, **kwargs)
        self.current_bar = 0

    def next(self):
        self.current_bar += 1
        if self.progress_callback:
            progress = int((self.current_bar / self.total_bars) * 100)
            self.progress_callback(progress)
        super().next()

def run_backtest(tp, sl, timeframe, commission, initial_cash, size_pct, entry_period, max_hold, trade_type, progress_callback=None):
    cerebro = bt.Cerebro()
    df = pd.read_csv(f'ethbtc_{timeframe}.csv', parse_dates=[0])
    df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume'] + list(df.columns[6:])
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(ProgressStrategy, 
                       tp=tp,
                       sl=sl,
                       size_pct=size_pct,
                       entry_period=entry_period,
                       max_hold=max_hold,
                       trade_type=trade_type,
                       progress_callback=progress_callback,
                       total_bars=len(df))
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.01)
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.VWR, _name='vwr')
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='time_return')
    initial_value = cerebro.broker.getvalue()
    results = cerebro.run()
    strat = results[0]
    final_value = cerebro.broker.getvalue()
    sharpe = strat.analyzers.sharpe.get_analysis()
    returns = strat.analyzers.returns.get_analysis()
    drawdown = strat.analyzers.drawdown.get_analysis()
    trades = strat.analyzers.trades.get_analysis()
    vwr = strat.analyzers.vwr.get_analysis()
    pnl_pct = (final_value - initial_cash) / initial_cash * 100
    # Get exit counts
    exit_tp = getattr(strat, 'exit_tp', None)
    exit_sl = getattr(strat, 'exit_sl', None)
    exit_time = getattr(strat, 'exit_time', None)
    return {
        'pnl': pnl_pct,
        'sharpe': sharpe.get('sharperatio', 0),
        'annual_return': returns.get('rnorm100', 0),
        'max_drawdown': drawdown.get('max', {}).get('drawdown', 0),
        'total_trades': trades.get('total', {}).get('total', 0),
        'won_trades': trades.get('won', {}).get('total', 0),
        'lost_trades': trades.get('lost', {}).get('total', 0),
        'win_rate': (trades.get('won', {}).get('total', 0) / trades.get('total', {}).get('total', 1)) * 100 if trades.get('total', {}).get('total', 0) > 0 else 0,
        'avg_trade': trades.get('pnl', {}).get('net', {}).get('average', 0),
        'vwr': vwr.get('vwr', 0),
        'exit_tp': exit_tp,
        'exit_sl': exit_sl,
        'exit_time': exit_time,
        'cerebro': cerebro
    }

def run_test():
    test_button.config(state='disabled')
    progress_bar['value'] = 0
    progress_bar['maximum'] = 100
    tp = float(tp_entry.get()) / 100
    sl = float(sl_entry.get()) / 100
    timeframe = timeframe_var.get()
    commission = float(commission_entry.get()) / 100
    initial_cash = float(initial_cash_entry.get())
    size_pct = float(size_pct_entry.get()) / 100
    entry_period = int(entry_period_entry.get())
    max_hold = int(exit_bars_entry.get())
    plot_enabled = plot_var.get()
    trade_type = trade_type_var.get()
    def run_backtest_thread():
        try:
            def update_progress(value):
                root.after(0, lambda: progress_bar.configure(value=value))
            results = run_backtest(tp, sl, timeframe, commission, initial_cash, size_pct, entry_period, max_hold, trade_type, progress_callback=update_progress)
            root.after(0, lambda: update_result(results, plot_enabled))
        except Exception as e:
            root.after(0, lambda: update_error(str(e)))
    threading.Thread(target=run_backtest_thread, daemon=True).start()

def update_result(results, plot_enabled):
    test_button.config(state='normal')
    # Remove previous widgets in results_frame
    for widget in results_frame.winfo_children():
        widget.destroy()
    # PnL color
    pnl = results['pnl']
    if pnl > 0:
        pnl_color = 'green'
    elif pnl < 0:
        pnl_color = 'red'
    else:
        pnl_color = 'black'
    # Sharpe color
    sharpe_color = 'blue'
    # Drawdown color
    dd_color = 'orange'
    # Win rate color
    win_color = 'green'
    # Other color
    other_color = 'black'
    # Results as colored labels
    def fmt(val, percent=False):
        if val is None:
            return 'N/A'
        if percent:
            return f"{val:.2f}%"
        try:
            return f"{val:.2f}"
        except Exception:
            return str(val)
    stats = [
        (f"PnL: {fmt(pnl, percent=True)}", pnl_color),
        (f"Sharpe Ratio: {fmt(results['sharpe'])}", sharpe_color),
        (f"Annual Return: {fmt(results['annual_return'], percent=True)}", other_color),
        (f"Max Drawdown: {fmt(results['max_drawdown'], percent=True)}", dd_color),
        (f"Total Trades: {results['total_trades'] if results['total_trades'] is not None else 'N/A'}", other_color),
        (f"Winning Trades: {results['won_trades'] if results['won_trades'] is not None else 'N/A'}", win_color),
        (f"Losing Trades: {results['lost_trades'] if results['lost_trades'] is not None else 'N/A'}", 'red'),
        (f"Win Rate: {fmt(results['win_rate'], percent=True)}", win_color),
        (f"Average Trade Profit: {fmt(results['avg_trade'])}", other_color),
        (f"VWR (Variability-Weighted Return): {fmt(results['vwr'])}", other_color),
        (f"Exit by Take Profit: {results['exit_tp'] if results['exit_tp'] is not None else 'N/A'}", 'green'),
        (f"Exit by Stop Loss: {results['exit_sl'] if results['exit_sl'] is not None else 'N/A'}", 'red'),
        (f"Exit by Time Expiry: {results['exit_time'] if results['exit_time'] is not None else 'N/A'}", 'orange'),
    ]
    for i, (text, color) in enumerate(stats):
        lbl = tk.Label(results_frame, text=text, fg=color, anchor='w', font=('Arial', 12, 'bold'))
        lbl.pack(anchor='w', pady=2)
    if plot_enabled:
        results['cerebro'].plot(style='candlestick')

def update_error(error_msg):
    test_button.config(state='normal')
    for widget in results_frame.winfo_children():
        widget.destroy()
    lbl = tk.Label(results_frame, text=f"Error: {error_msg}", fg='red', anchor='w', font=('Arial', 12, 'bold'))
    lbl.pack(anchor='w', pady=2)

# --- GUI LAYOUT ---
root = tk.Tk()
root.title("Random Entry Strategy Tester")
root.attributes('-zoomed', True)  # Maximize window on Linux
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

# LEFT: Input parameters
input_frame = ttk.LabelFrame(root, text="Parameters", padding="10")
input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
input_frame.grid_rowconfigure(99, weight=1)

ttk.Label(input_frame, text="Take Profit (%):").grid(row=0, column=0, sticky="w")
tp_entry = ttk.Entry(input_frame)
tp_entry.insert(0, "0.1")
tp_entry.grid(row=0, column=1, padx=5, pady=2)

ttk.Label(input_frame, text="Stop Loss (%):").grid(row=1, column=0, sticky="w")
sl_entry = ttk.Entry(input_frame)
sl_entry.insert(0, "0.1")
sl_entry.grid(row=1, column=1, padx=5, pady=2)

ttk.Label(input_frame, text="Timeframe:").grid(row=2, column=0, sticky="w")
timeframe_var = tk.StringVar(value="1m")
timeframe_combo = ttk.Combobox(input_frame, textvariable=timeframe_var, values=["1m", "5m", "15m", "1h", "4h", "1d"])
timeframe_combo.grid(row=2, column=1, padx=5, pady=2)

ttk.Label(input_frame, text="Commission (%):").grid(row=3, column=0, sticky="w")
commission_entry = ttk.Entry(input_frame)
commission_entry.insert(0, "0.1")
commission_entry.grid(row=3, column=1, padx=5, pady=2)

ttk.Label(input_frame, text="Initial Cash:").grid(row=4, column=0, sticky="w")
initial_cash_entry = ttk.Entry(input_frame)
initial_cash_entry.insert(0, "100000")
initial_cash_entry.grid(row=4, column=1, padx=5, pady=2)

ttk.Label(input_frame, text="Position Size (%):").grid(row=5, column=0, sticky="w")
size_pct_entry = ttk.Entry(input_frame)
size_pct_entry.insert(0, "0.1")
size_pct_entry.grid(row=5, column=1, padx=5, pady=2)

ttk.Label(input_frame, text="Entry Period (bars):").grid(row=6, column=0, sticky="w")
entry_period_entry = ttk.Entry(input_frame)
entry_period_entry.insert(0, "10")
entry_period_entry.grid(row=6, column=1, padx=5, pady=2)

# Add Exit after N bars parameter
exit_bars_label = ttk.Label(input_frame, text="Exit after N bars:")
exit_bars_label.grid(row=7, column=0, sticky="w")
exit_bars_entry = ttk.Entry(input_frame)
exit_bars_entry.insert(0, "30")
exit_bars_entry.grid(row=7, column=1, padx=5, pady=2)

# Add Trade Type combobox
trade_type_label = ttk.Label(input_frame, text="Trade Type:")
trade_type_label.grid(row=8, column=0, sticky="w")
trade_type_var = tk.StringVar(value="LONG")
trade_type_combo = ttk.Combobox(input_frame, textvariable=trade_type_var, values=["LONG", "SHORT", "BOTH"])
trade_type_combo.grid(row=8, column=1, padx=5, pady=2)

# Checkbox for plot
plot_var = tk.BooleanVar(value=True)
plot_checkbox = ttk.Checkbutton(input_frame, text="Show Backtrader Plot", variable=plot_var)
plot_checkbox.grid(row=97, column=0, columnspan=2, pady=10)

test_button = ttk.Button(input_frame, text="Run Backtest", command=run_test)
test_button.grid(row=98, column=0, columnspan=2, pady=20)

# RIGHT: Results area
results_frame = ttk.LabelFrame(root, text="Results", padding="10")
results_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
results_label = ttk.Label(results_frame, text="No results yet.", justify='left', anchor='nw')
results_label.pack(fill='both', expand=True)

# BOTTOM: Progress bar (always visible)
progress_bar = ttk.Progressbar(root, mode='determinate', length=300)
progress_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=10)

root.mainloop() 