import tkinter as tk
from tkinter import ttk
from tkinter import PhotoImage
from tkinter import messagebox
import threading
from random_entry_strategy import RandomEntryTPSL
import backtrader as bt
import pandas as pd
from datetime import datetime, timedelta
import time
import os
from PIL import Image, ImageTk
from binance.client import Client
from tqdm import tqdm
from tkcalendar import DateEntry
import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Pool, cpu_count

class ProgressStrategy(RandomEntryTPSL):
    def __init__(self, *args, **kwargs):
        self.progress_callback = kwargs.pop('progress_callback', None)
        self.total_bars = kwargs.pop('total_bars', 0)
        # Rimuovo trade_type dai kwargs per gestirlo separatamente
        trade_type = kwargs.pop('trade_type', 'LONG')
        self.current_bar = 0
        
        # Passo tutti gli altri parametri direttamente alla strategia base
        super().__init__(*args, **kwargs)
        
        # Imposto trade_type come attributo dell'istanza
        self.trade_type = trade_type
        
        # Debug: stampa i parametri ricevuti
        print(f"Strategy initialized with:")
        print(f"  tp: {self.p.tp}")
        print(f"  sl: {self.p.sl}")
        print(f"  size_pct: {self.p.size_pct}")
        print(f"  entry_period: {self.p.entry_period}")
        print(f"  max_hold: {self.p.max_hold}")
        print(f"  trade_type: {self.trade_type}")

    def next(self):
        self.current_bar += 1
        if self.progress_callback:
            progress = int((self.current_bar / self.total_bars) * 100)
            self.progress_callback(progress)
        
        # Debug: stampa informazioni ogni 100 bar
        if self.current_bar % 100 == 0:
            print(f"Bar {self.current_bar}: Price={self.data.close[0]:.6f}, Position={self.position.size}, Cash={self.broker.getvalue():.2f}")
        
        super().next()

def get_days_for_timeframe(timeframe):
    # Scarica almeno 3 anni per ogni timeframe
    return 3 * 365

def fetch_historical_klines(symbol, interval, start_str, end_str=None, progress_callback=None):
    """Fetch historical klines/candlestick data from Binance"""
    client = Client()
    
    # Convert start_str to datetime if it's a string
    if isinstance(start_str, str):
        start_str = datetime.strptime(start_str, "%Y-%m-%d")
    
    # If end_str is not provided, use current time
    if end_str is None:
        end_str = datetime.now()
    elif isinstance(end_str, str):
        end_str = datetime.strptime(end_str, "%Y-%m-%d")
    
    # Initialize empty list to store all klines
    all_klines = []
    
    # Calculate total time range
    total_days = (end_str - start_str).days
    if progress_callback:
        progress_callback(f"Downloading {symbol} {interval} data for {total_days} days...")
    
    # Fetch data in chunks to avoid hitting rate limits
    current_start = start_str
    days_processed = 0
    
    while current_start < end_str:
        try:
            # Fetch klines
            klines = client.get_historical_klines(
                symbol,
                interval,
                current_start.strftime("%Y-%m-%d %H:%M:%S"),
                end_str.strftime("%Y-%m-%d %H:%M:%S"),
                limit=1000
            )
            
            if not klines:
                break
                
            all_klines.extend(klines)
            
            # Update progress
            days_processed = (datetime.fromtimestamp(klines[-1][0] / 1000) - start_str).days
            if progress_callback:
                progress = min(100, (days_processed / total_days) * 100)
                progress_callback(f"Downloading... {progress:.1f}%")
            
            # Update start time for next iteration
            current_start = datetime.fromtimestamp(klines[-1][0] / 1000) + timedelta(seconds=1)
            
            # Sleep to avoid hitting rate limits
            time.sleep(0.1)
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error: {e}. Retrying...")
            time.sleep(5)
            continue
    
    if not all_klines:
        raise Exception(f"No data fetched for {symbol} {interval}")
    
    # Convert to DataFrame
    df = pd.DataFrame(all_klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Convert string values to float
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
    
    # Set timestamp as index
    df.set_index('timestamp', inplace=True)
    
    return df

def ensure_data_file(symbol, timeframe, progress_callback=None):
    """Ensure that the data file exists, download if necessary"""
    filename = os.path.join('csv', f'{symbol.lower()}_{timeframe}.csv')
    
    if not os.path.exists(filename):
        if progress_callback:
            progress_callback(f"File {filename} not found. Downloading...")
        
        # Calculate start date based on timeframe
        days = get_days_for_timeframe(timeframe)
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Download data
        df = fetch_historical_klines(symbol, timeframe, start_date, progress_callback=progress_callback)
        
        # Save to CSV
        df.to_csv(filename)
        
        if progress_callback:
            progress_callback(f"Downloaded and saved {len(df)} rows to {filename}")
    
    return filename

def get_quote_currency(symbol):
    """Determina la valuta di quotazione dalla coppia di trading"""
    if symbol.endswith('USDT'):
        return 'USDT'
    elif symbol.endswith('BTC'):
        return 'BTC'
    elif symbol.endswith('ETH'):
        return 'ETH'
    elif symbol.endswith('BNB'):
        return 'BNB'
    else:
        return 'Unknown'

def update_cash_label():
    """Aggiorna la label del cash iniziale con la valuta corretta"""
    symbol = symbol_var.get()
    currency = get_quote_currency(symbol)
    cash_label.config(text=f"Initial Cash ({currency}):")
    
    # Aggiorna il valore di default basato sulla valuta
    if currency == 'USDT':
        # Per coppie USDT, usa dollari (aumentato per BTC)
        default_cash = "100000"
    elif currency == 'BTC':
        # Per coppie BTC, usa BTC (valore molto più piccolo)
        default_cash = "1.0"
    else:
        # Per altre valute, usa un valore intermedio
        default_cash = "10000"
    
    # Aggiorna solo se il campo è vuoto o ha il valore di default precedente
    current_value = initial_cash_entry.get()
    if current_value in ["100000", "10000", "1.0", "1000", ""]:
        initial_cash_entry.delete(0, tk.END)
        initial_cash_entry.insert(0, default_cash)

def get_csv_date_limits(symbol, timeframe):
    filename = os.path.join('csv', f'{symbol.lower()}_{timeframe}.csv')
    try:
        df = pd.read_csv(filename, usecols=[0], parse_dates=[0])
        min_date = df.iloc[0, 0]
        max_date = df.iloc[-1, 0]
        return pd.to_datetime(min_date), pd.to_datetime(max_date)
    except Exception:
        return None, None

def run_single_backtest(args):
    tp, sl, symbol, timeframe, commission, initial_cash, size_pct, entry_period, max_hold, trade_type, use_numba = args
    
    cerebro = bt.Cerebro()
    try:
        filename = ensure_data_file(symbol, timeframe, None)
    except Exception as e:
        raise Exception(f"Failed to get data for {symbol} {timeframe}: {e}")
        
    df = pd.read_csv(filename, parse_dates=[0])
    df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume'] + list(df.columns[6:])
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
    
    start_date = df.index[0]
    end_date = df.index[-1]
    duration_days = (end_date - start_date).days
    duration_years = duration_days / 365.25
    
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(RandomEntryTPSL, 
                       tp=tp,
                       sl=sl,
                       size_pct=size_pct,
                       entry_period=entry_period,
                       max_hold=max_hold,
                       trade_type=trade_type,
                       use_numba=use_numba)
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.01)
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.VWR, _name='vwr')
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='time_return')
    
    results = cerebro.run()
    strat = results[0]
    final_value = cerebro.broker.getvalue()
    sharpe = strat.analyzers.sharpe.get_analysis()
    returns = strat.analyzers.returns.get_analysis()
    drawdown = strat.analyzers.drawdown.get_analysis()
    trades = strat.analyzers.trades.get_analysis()
    vwr = strat.analyzers.vwr.get_analysis()
    
    pnl_pct = (final_value - initial_cash) / initial_cash * 100
    
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
        'start_date': start_date,
        'end_date': end_date,
        'duration_days': duration_days,
        'duration_years': duration_years,
        'elapsed': results[1],
        'num_cpus': results[2],
        'use_numba': use_numba
    }

def run_backtest(tp, sl, symbol, timeframe, commission, initial_cash, size_pct, entry_period, max_hold, trade_type, num_cpus, use_numba, progress_callback=None):
    print(f"Running backtests using {num_cpus} CPU cores...")
    args = (tp, sl, symbol, timeframe, commission, initial_cash, size_pct, entry_period, max_hold, trade_type, use_numba)
    start_time = time.time()
    # Se vuoi batch/grid, args_list = [(...), (...), ...]
    args_list = [args]  # Per ora solo una simulazione
    if len(args_list) == 1 or num_cpus == 1:
        # Caso singola simulazione: nessun multiprocessing
        result = run_single_backtest(args)
        elapsed = time.time() - start_time
        result['elapsed'] = elapsed
        result['num_cpus'] = 1
        result['use_numba'] = use_numba
        return result
    else:
        # Caso batch/grid: multiprocessing
        with Pool(num_cpus) as pool:
            results = pool.map(run_single_backtest, args_list)
        elapsed = time.time() - start_time
        # Qui results è una lista di dict, per ora ne restituiamo solo il primo
        results[0]['elapsed'] = elapsed
        results[0]['num_cpus'] = num_cpus
        results[0]['use_numba'] = use_numba
        return results[0]

def run_test():
    test_button.config(state='disabled')
    progress_bar['value'] = 0
    progress_bar['maximum'] = 100
    tp = float(tp_entry.get()) / 100
    sl = float(sl_entry.get()) / 100
    symbol = symbol_var.get()
    timeframe = timeframe_var.get()
    commission = float(commission_entry.get()) / 100
    initial_cash = float(initial_cash_entry.get())
    size_pct = float(size_pct_entry.get()) / 100
    entry_period = int(entry_period_entry.get())
    max_hold = int(exit_bars_entry.get())
    plot_enabled = plot_var.get()
    trade_type = trade_type_var.get()
    
    def update_status(msg):
        root.after(0, lambda: status_label.config(text=msg))
    
    def run_backtest_thread():
        try:
            def update_progress(value):
                if isinstance(value, str):
                    root.after(0, lambda: update_status(value))
                else:
                    root.after(0, lambda: progress_bar.configure(value=value))
            results = run_backtest(tp, sl, symbol, timeframe, commission, initial_cash, size_pct, entry_period, max_hold, trade_type, cpu_count_var.get(), use_numba_var.get(), progress_callback=update_progress)
            root.after(0, lambda: update_result(results, plot_enabled))
        except Exception as e:
            error_msg = str(e)
            root.after(0, lambda: update_error(error_msg))
    threading.Thread(target=run_backtest_thread, daemon=True).start()

def update_result(results, plot_enabled):
    test_button.config(state='normal')
    status_label.config(text="Backtest completed successfully")
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
        (f"Simulation period: {results['start_date'].strftime('%Y-%m-%d')} → {results['end_date'].strftime('%Y-%m-%d')}", other_color),
        (f"Duration: {results['duration_days']} days ({results['duration_years']:.2f} years)", other_color),
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
        (f"Tempo di calcolo: {results['elapsed']:.2f} secondi\nCPU usate: {results['num_cpus']}\nNumba: {'Sì' if results['use_numba'] else 'No'}", other_color),
    ]
    for i, (text, color) in enumerate(stats):
        lbl = tk.Label(results_frame, text=text, fg=color, anchor='w', font=('Arial', 12, 'bold'))
        lbl.pack(anchor='w', pady=2)
    if plot_enabled:
        results['cerebro'].plot(style='candlestick')

def update_error(error_msg):
    test_button.config(state='normal')
    status_label.config(text=f"Error: {error_msg}")
    for widget in results_frame.winfo_children():
        widget.destroy()
    lbl = tk.Label(results_frame, text=f"Error: {error_msg}", fg='red', anchor='w', font=('Arial', 12, 'bold'))
    lbl.pack(anchor='w', pady=2)

def get_available_trading_pairs():
    """Get all available trading pairs from Binance"""
    try:
        client = Client()
        exchange_info = client.get_exchange_info()
        trading_pairs = []
        
        # Get all USDT, BTC, ETH, and BNB pairs
        quote_currencies = ['USDT', 'BTC', 'ETH', 'BNB']
        for symbol_info in exchange_info['symbols']:
            symbol = symbol_info['symbol']
            if symbol_info['status'] == 'TRADING':
                for quote in quote_currencies:
                    if symbol.endswith(quote):
                        trading_pairs.append(symbol)
                        break
        
        return sorted(trading_pairs)
    except Exception as e:
        print(f"Error fetching trading pairs: {e}")
        # Return default pairs if API call fails
        return ["ETHBTC", "BTCUSDT", "ETHUSDT", "ADAUSDT", "LINKUSDT", "DOTUSDT", 
                "BNBUSDT", "SOLUSDT", "AVAXUSDT", "MATICUSDT", "XRPUSDT", "DOGEUSDT",
                "LTCUSDT", "UNIUSDT", "AAVEUSDT", "ATOMUSDT", "NEARUSDT", "ALGOUSDT",
                "ICPUSDT", "FILUSDT", "VETUSDT", "MANAUSDT", "SANDUSDT", "AXSUSDT",
                "THETAUSDT", "XTZUSDT", "EOSUSDT", "TRXUSDT", "XLMUSDT", "ADAUSDT"]

class UpdateCSVDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Update CSV Files")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Create main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Create frames for pairs and timeframes
        pairs_frame = ttk.LabelFrame(main_frame, text="Trading Pairs", padding="5")
        pairs_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        timeframes_frame = ttk.LabelFrame(main_frame, text="Timeframes", padding="5")
        timeframes_frame.pack(side='left', fill='both', expand=True, padx=(5, 0))
        
        # Add trading pairs listbox with scrollbar
        pairs_scroll = ttk.Scrollbar(pairs_frame)
        pairs_scroll.pack(side='right', fill='y')
        
        self.pairs_listbox = tk.Listbox(pairs_frame, selectmode='multiple', yscrollcommand=pairs_scroll.set, exportselection=0)
        self.pairs_listbox.pack(side='left', fill='both', expand=True)
        pairs_scroll.config(command=self.pairs_listbox.yview)
        
        # Add timeframes listbox with scrollbar
        tf_scroll = ttk.Scrollbar(timeframes_frame)
        tf_scroll.pack(side='right', fill='y')
        
        self.tf_listbox = tk.Listbox(timeframes_frame, selectmode='multiple', yscrollcommand=tf_scroll.set, exportselection=0)
        self.tf_listbox.pack(side='left', fill='both', expand=True)
        tf_scroll.config(command=self.tf_listbox.yview)
        
        # Add buttons frame
        buttons_frame = ttk.Frame(self.dialog, padding="5")
        buttons_frame.pack(fill='x', padx=10, pady=5)
        
        # Add Select All button for pairs
        ttk.Button(buttons_frame, text="Select All Pairs", 
                  command=lambda: self.select_all(self.pairs_listbox)).pack(side='left', padx=5)
        
        # Add Select All button for timeframes
        ttk.Button(buttons_frame, text="Select All Timeframes", 
                  command=lambda: self.select_all(self.tf_listbox)).pack(side='left', padx=5)
        
        # Add Update button
        ttk.Button(buttons_frame, text="Update Selected", 
                  command=self.on_update).pack(side='right', padx=5)
        
        # Add Cancel button
        ttk.Button(buttons_frame, text="Cancel", 
                  command=self.dialog.destroy).pack(side='right', padx=5)
        
        # Populate lists
        self.populate_lists()
        
        # Center the dialog
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # Bind mouse events to maintain selection
        self.pairs_listbox.bind('<Button-1>', lambda e: self.pairs_listbox.focus_set())
        self.tf_listbox.bind('<Button-1>', lambda e: self.tf_listbox.focus_set())
        
        # Set initial focus
        self.pairs_listbox.focus_set()
    
    def select_all(self, listbox):
        listbox.select_set(0, tk.END)
    
    def populate_lists(self):
        # Get available trading pairs
        trading_pairs = get_available_trading_pairs()
        for pair in trading_pairs:
            self.pairs_listbox.insert(tk.END, pair)
        
        # Add timeframes
        timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
        for tf in timeframes:
            self.tf_listbox.insert(tk.END, tf)
    
    def on_update(self):
        selected_pairs = [self.pairs_listbox.get(i) for i in self.pairs_listbox.curselection()]
        selected_timeframes = [self.tf_listbox.get(i) for i in self.tf_listbox.curselection()]
        
        if not selected_pairs or not selected_timeframes:
            messagebox.showwarning("Warning", "Please select at least one pair and one timeframe")
            return
        
        self.dialog.destroy()
        update_csv_files(selected_pairs, selected_timeframes)

def update_csv_files(selected_pairs, selected_timeframes):
    """Update CSV files for selected pairs and timeframes"""
    update_csv_button.config(state='disabled')
    progress_bar['value'] = 0
    progress_bar['maximum'] = 100
    
    def update_status(msg):
        root.after(0, lambda: status_label.config(text=msg))
    
    def update_progress(value):
        if isinstance(value, str):
            root.after(0, lambda: update_status(value))
        else:
            root.after(0, lambda: progress_bar.configure(value=value))
    
    def on_complete():
        root.after(0, lambda: update_csv_button.config(state='normal'))
        # Update comboboxes after download completes
        root.after(0, update_symbol_combo)
        root.after(0, update_timeframe_combo)
        # Update date limits for current symbol
        root.after(0, update_date_limits)
    
    def run_update():
        try:
            total_items = len(selected_pairs) * len(selected_timeframes)
            current_item = 0
            
            for symbol in selected_pairs:
                for timeframe in selected_timeframes:
                    try:
                        current_item += 1
                        progress = (current_item / total_items) * 100
                        update_progress(f"Processing {symbol} {timeframe} ({current_item}/{total_items})...")
                        
                        # Calculate start date based on timeframe
                        days = get_days_for_timeframe(timeframe)
                        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                        
                        # Download data
                        df = fetch_historical_klines(symbol, timeframe, start_date, progress_callback=update_progress)
                        
                        # Save to CSV
                        filename = os.path.join('csv', f'{symbol.lower()}_{timeframe}.csv')
                        df.to_csv(filename)
                        
                        update_progress(f"Successfully updated {filename} with {len(df)} rows")
                        
                    except Exception as e:
                        update_progress(f"Error updating {symbol} {timeframe}: {str(e)}")
                        continue
            
            # Update date limits for current symbol after all downloads
            update_date_limits()
            update_progress("All selected CSV files have been updated!")
            
        except Exception as e:
            update_progress(f"Error: {str(e)}")
        finally:
            on_complete()
    
    threading.Thread(target=run_update, daemon=True).start()

def update_csv_thread():
    """Show dialog to select pairs and timeframes for update"""
    dialog = UpdateCSVDialog(root)

def get_available_csv_files():
    """Get list of available CSV files in the csv directory"""
    available_pairs = set()
    available_timeframes = set()
    
    if os.path.exists('csv'):
        for filename in os.listdir('csv'):
            if filename.endswith('.csv'):
                # Extract symbol and timeframe from filename (e.g., 'btcusdt_1h.csv')
                parts = filename[:-4].split('_')  # Remove .csv and split
                if len(parts) == 2:
                    symbol, timeframe = parts
                    available_pairs.add(symbol.upper())
                    available_timeframes.add(timeframe)
    
    return sorted(list(available_pairs)), sorted(list(available_timeframes))

def update_symbol_combo():
    """Update the symbol combobox with available pairs"""
    available_pairs, _ = get_available_csv_files()
    if available_pairs:
        symbol_combo['values'] = available_pairs
        if symbol_var.get() not in available_pairs:
            symbol_var.set(available_pairs[0])
    else:
        symbol_combo['values'] = ["No CSV files available"]
        symbol_var.set("No CSV files available")

def update_timeframe_combo():
    """Update the timeframe combobox with available timeframes"""
    _, available_timeframes = get_available_csv_files()
    if available_timeframes:
        timeframe_combo['values'] = available_timeframes
        if timeframe_var.get() not in available_timeframes:
            timeframe_var.set(available_timeframes[0])
    else:
        timeframe_combo['values'] = ["No CSV files available"]
        timeframe_var.set("No CSV files available")

# --- GUI LAYOUT ---
root = tk.Tk()
root.title("Random Entry Strategy Tester")
#root.attributes('-zoomed', True)  # Maximize window on Linux
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

# LEFT: Input parameters
input_frame = ttk.LabelFrame(root, text="Parameters", padding="10")
input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
input_frame.grid_rowconfigure(99, weight=1)

ttk.Label(input_frame, text="Trading Pair:").grid(row=0, column=0, sticky="w")
symbol_var = tk.StringVar()
symbol_combo = ttk.Combobox(input_frame, textvariable=symbol_var)
symbol_combo.grid(row=0, column=1, padx=5, pady=2)
symbol_combo.bind('<<ComboboxSelected>>', lambda e: (update_cash_label(), update_date_limits()))

ttk.Label(input_frame, text="Take Profit (%):").grid(row=1, column=0, sticky="w")
tp_entry = ttk.Entry(input_frame)
tp_entry.insert(0, "10")
tp_entry.grid(row=1, column=1, padx=5, pady=2)

ttk.Label(input_frame, text="Stop Loss (%):").grid(row=2, column=0, sticky="w")
sl_entry = ttk.Entry(input_frame)
sl_entry.insert(0, "10")
sl_entry.grid(row=2, column=1, padx=5, pady=2)

ttk.Label(input_frame, text="Timeframe:").grid(row=3, column=0, sticky="w")
timeframe_var = tk.StringVar()
timeframe_combo = ttk.Combobox(input_frame, textvariable=timeframe_var)
timeframe_combo.grid(row=3, column=1, padx=5, pady=2)
timeframe_combo.bind('<<ComboboxSelected>>', lambda e: update_date_limits())

ttk.Label(input_frame, text="Commission (%):").grid(row=4, column=0, sticky="w")
commission_entry = ttk.Entry(input_frame)
commission_entry.insert(0, "0.05")
commission_entry.grid(row=4, column=1, padx=5, pady=2)

cash_label = ttk.Label(input_frame, text="Initial Cash (BTC):")
cash_label.grid(row=5, column=0, sticky="w")
initial_cash_entry = ttk.Entry(input_frame)
initial_cash_entry.insert(0, "1.0")
initial_cash_entry.grid(row=5, column=1, padx=5, pady=2)

ttk.Label(input_frame, text="Position Size (%):").grid(row=6, column=0, sticky="w")
size_pct_entry = ttk.Entry(input_frame)
size_pct_entry.insert(0, "10")
size_pct_entry.grid(row=6, column=1, padx=5, pady=2)

ttk.Label(input_frame, text="Entry Period (bars):").grid(row=7, column=0, sticky="w")
entry_period_entry = ttk.Entry(input_frame)
entry_period_entry.insert(0, "10")
entry_period_entry.grid(row=7, column=1, padx=5, pady=2)

# Add Exit after N bars parameter
exit_bars_label = ttk.Label(input_frame, text="Exit after N bars:")
exit_bars_label.grid(row=8, column=0, sticky="w")
exit_bars_entry = ttk.Entry(input_frame)
exit_bars_entry.insert(0, "3000")
exit_bars_entry.grid(row=8, column=1, padx=5, pady=2)

# Add Trade Type combobox
trade_type_label = ttk.Label(input_frame, text="Trade Type:")
trade_type_label.grid(row=9, column=0, sticky="w")
trade_type_var = tk.StringVar(value="LONG")
trade_type_combo = ttk.Combobox(input_frame, textvariable=trade_type_var, values=["LONG", "SHORT", "BOTH"])
trade_type_combo.grid(row=9, column=1, padx=5, pady=2)

# Checkbox for plot
plot_var = tk.BooleanVar(value=False)
plot_checkbox = ttk.Checkbutton(input_frame, text="Show Backtrader Plot", variable=plot_var)
plot_checkbox.grid(row=97, column=0, columnspan=2, pady=10)

cpu_count_var = tk.IntVar(value=cpu_count())
use_numba_var = tk.BooleanVar(value=True)

cpu_label = ttk.Label(input_frame, text="CPU da usare:")
cpu_label.grid(row=12, column=0, sticky="w")
cpu_entry = ttk.Entry(input_frame, textvariable=cpu_count_var, width=5)
cpu_entry.grid(row=12, column=1, padx=5, pady=2)

numba_check = ttk.Checkbutton(input_frame, text="Abilita Numba (compilazione veloce)", variable=use_numba_var)
numba_check.grid(row=13, column=0, columnspan=2, sticky="w")

test_button = ttk.Button(input_frame, text="Run Backtest", command=run_test)
test_button.grid(row=98, column=0, columnspan=2, pady=20)

# RIGHT: Results area
results_frame = ttk.LabelFrame(root, text="Results", padding="10")
results_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
results_label = ttk.Label(results_frame, text="No results yet.", justify='left', anchor='nw')
results_label.pack(fill='both', expand=True)

# Create progress frame
progress_frame = ttk.LabelFrame(root, text="Progress", padding="5")
progress_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
progress_frame.grid_columnconfigure(0, weight=1)

status_label = ttk.Label(progress_frame, text="Ready", anchor="w")
status_label.grid(row=0, column=0, sticky="ew", pady=(0, 5))

progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=300)
progress_bar.grid(row=1, column=0, sticky="ew")

# Add Update CSV button after the progress bar
update_csv_button = ttk.Button(progress_frame, text="Update CSV", command=update_csv_thread)
update_csv_button.grid(row=2, column=0, pady=5)

# Inizializza la label del cash con la valuta corretta
update_cash_label()

# Commento o rimuovo la funzione update_date_limits e tutti i riferimenti a start_date_picker e end_date_picker
# def update_date_limits():
#     ...
#     start_date_picker.config(...)
#     end_date_picker.config(...)
# ...
# E tutti i punti dove viene chiamata update_date_limits()

# Update comboboxes with available CSV files
update_symbol_combo()
update_timeframe_combo()

root.mainloop() 