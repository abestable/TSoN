import argparse
import time
import pandas as pd
import numpy as np
import backtrader as bt
from multiprocessing import Pool, cpu_count
from random_entry_strategy import RandomEntryTPSL
import os
from tqdm import tqdm
import sys
import cProfile
import pstats

def ensure_data_file(symbol, timeframe):
    filename = os.path.join('csv', f'{symbol.lower()}_{timeframe}.csv')
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File {filename} non trovato. Scaricalo o generane uno.")
    return filename

class ProgressStrategy(RandomEntryTPSL):
    def __init__(self, *args, progress_bar=None, total_bars=None, **kwargs):
        self.progress_bar = progress_bar
        self.total_bars = total_bars
        self.current_bar = 0
        super().__init__(*args, **kwargs)
    def next(self):
        self.current_bar += 1
        if self.progress_bar:
            self.progress_bar.update(1)
        super().next()

def run_single_backtest(args):
    tp, sl, symbol, timeframe, commission, initial_cash, size_pct, entry_period, max_hold, trade_type, use_numba = args
    cerebro = bt.Cerebro()
    filename = ensure_data_file(symbol, timeframe)
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
    total_bars = len(df)
    with tqdm(total=total_bars, desc='Simulazione', ncols=80) as pbar:
        cerebro.addstrategy(ProgressStrategy,
                           tp=tp,
                           sl=sl,
                           size_pct=size_pct,
                           entry_period=entry_period,
                           max_hold=max_hold,
                           trade_type=trade_type,
                           use_numba=use_numba,
                           progress_bar=pbar,
                           total_bars=total_bars)
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
        'duration_years': duration_years
    }

def run_backtest(args, num_cpus=1):
    start_time = time.time()
    if num_cpus == 1:
        result = run_single_backtest(args)
        elapsed = time.time() - start_time
        result['elapsed'] = elapsed
        result['num_cpus'] = 1
        result['use_numba'] = args[-1]
        return result
    else:
        args_list = [args]
        with Pool(num_cpus) as pool:
            results = pool.map(run_single_backtest, args_list)
        elapsed = time.time() - start_time
        results[0]['elapsed'] = elapsed
        results[0]['num_cpus'] = num_cpus
        results[0]['use_numba'] = args[-1]
        return results[0]

def main():
    parser = argparse.ArgumentParser(description="Random Entry Strategy CLI")
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading Pair')
    parser.add_argument('--tp', type=float, default=0.01, help='Take Profit (%)')
    parser.add_argument('--sl', type=float, default=0.01, help='Stop Loss (%)')
    parser.add_argument('--timeframe', type=str, default='15m', help='Timeframe')
    parser.add_argument('--commission', type=float, default=0.0005, help='Commission (%)')
    parser.add_argument('--initial_cash', type=float, default=100000, help='Initial Cash')
    parser.add_argument('--size_pct', type=float, default=0.1, help='Position Size (%)')
    parser.add_argument('--entry_period', type=int, default=10, help='Entry Period (bars)')
    parser.add_argument('--max_hold', type=int, default=3000, help='Max Hold (bars)')
    parser.add_argument('--trade_type', type=str, default='LONG', choices=['LONG', 'SHORT', 'BOTH'], help='Trade Type')
    parser.add_argument('--num_cpus', type=int, default=1, help='Numero di CPU da usare')
    parser.add_argument('--use_numba', action='store_true', help='Abilita Numba (compilazione veloce)')
    parser.add_argument('--profile', action='store_true', help='Abilita profilazione cProfile')
    args = parser.parse_args()

    backtest_args = (
        args.tp,
        args.sl,
        args.symbol,
        args.timeframe,
        args.commission,
        args.initial_cash,
        args.size_pct,
        args.entry_period,
        args.max_hold,
        args.trade_type,
        args.use_numba
    )
    results = run_backtest(backtest_args, num_cpus=args.num_cpus)

    print("\n=== RISULTATI SIMULAZIONE ===")
    print(f"Trading Pair: {args.symbol}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Periodo: {results['start_date'].strftime('%Y-%m-%d')} → {results['end_date'].strftime('%Y-%m-%d')}")
    print(f"Durata: {results['duration_days']} giorni ({results['duration_years']:.2f} anni)")
    print(f"Take Profit: {args.tp*100:.2f}%  Stop Loss: {args.sl*100:.2f}%")
    print(f"Commissione: {args.commission*100:.2f}%  Capitale iniziale: {args.initial_cash}")
    print(f"Posizione: {args.size_pct*100:.2f}%  Entry Period: {args.entry_period}  Max Hold: {args.max_hold}")
    print(f"Trade Type: {args.trade_type}")
    print(f"CPU usate: {results['num_cpus']}  Numba: {'Sì' if results['use_numba'] else 'No'}")
    print(f"Tempo di calcolo: {results['elapsed']:.2f} secondi")
    print("------------------------------")
    print(f"PnL finale: {results['pnl']:.2f}%")
    print(f"Sharpe Ratio: {results['sharpe']:.2f}")
    print(f"Annual Return: {results['annual_return']:.2f}%")
    print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Win Rate: {results['win_rate']:.2f}%")
    print(f"Avg Trade: {results['avg_trade']:.2f}")
    print(f"VWR: {results['vwr']:.2f}")
    print(f"Exit by Take Profit: {results['exit_tp'] if results['exit_tp'] is not None else 'N/A'}")
    print(f"Exit by Stop Loss: {results['exit_sl'] if results['exit_sl'] is not None else 'N/A'}")
    print(f"Exit by Time Expiry: {results['exit_time'] if results['exit_time'] is not None else 'N/A'}")

if __name__ == "__main__":
    if '--profile' in sys.argv:
        sys.argv.remove('--profile')
        with cProfile.Profile() as pr:
            main()
        stats = pstats.Stats(pr)
        print("\n--- PROFILING: 30 funzioni più lente (cumtime) ---")
        stats.sort_stats("cumtime").print_stats(30)
    else:
        main() 