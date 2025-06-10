import backtrader as bt
from strategy_variations import MeanReversionWithVolatility
import pandas as pd
from datetime import datetime

def run_backtest(timeframe, **kwargs):
    cerebro = bt.Cerebro()
    
    # Select date format based on timeframe
    if timeframe == '1d':
        dtformat = '%Y-%m-%d'
    else:
        dtformat = '%Y-%m-%d %H:%M:%S'
    
    # Add data
    data = bt.feeds.GenericCSVData(
        dataname=f'ethbtc_{timeframe}.csv',
        dtformat=dtformat,
        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        openinterest=-1
    )
    cerebro.adddata(data)
    
    # Add strategy
    cerebro.addstrategy(MeanReversionWithVolatility, **kwargs)
    
    # Set broker parameters
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission
    
    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    
    # Run backtest
    results = cerebro.run()
    strat = results[0]
    
    # Get results
    sharpe = strat.analyzers.sharpe.get_analysis()['sharperatio']
    returns = strat.analyzers.returns.get_analysis()['rnorm100']
    drawdown = strat.analyzers.drawdown.get_analysis()['max']['drawdown']
    trades = strat.analyzers.trades.get_analysis()
    
    return {
        'timeframe': timeframe,
        'final_value': cerebro.broker.getvalue(),
        'sharpe': sharpe,
        'returns': returns,
        'drawdown': drawdown,
        'total_trades': trades.get('total', {}).get('total', 0),
        'won_trades': trades.get('won', {}).get('total', 0),
        'lost_trades': trades.get('lost', {}).get('total', 0)
    }

def main():
    timeframes = ['1m', '5m', '15m', '1h']
    
    # Strategy parameters optimized for each timeframe
    params = {
        '1m': {
            'period': 10,
            'zentry': 1.2,
            'zexit': 0.3,
            'vol_period': 5,
            'vol_threshold': 0.008,
            'stop_loss': 0.03,      # 3% stop loss
            'take_profit': 0.06,    # 6% take profit
            'trailing_stop': 0.02,  # 2% trailing stop
            'min_volume': 100,
            'rsi_period': 10,
            'rsi_threshold': 35,
            'trend_period': 100
        },
        '5m': {
            'period': 15,
            'zentry': 1.5,
            'zexit': 0.4,
            'vol_period': 7,
            'vol_threshold': 0.01,
            'stop_loss': 0.04,      # 4% stop loss
            'take_profit': 0.07,    # 7% take profit
            'trailing_stop': 0.025, # 2.5% trailing stop
            'min_volume': 100,
            'rsi_period': 12,
            'rsi_threshold': 38,
            'trend_period': 150
        },
        '15m': {
            'period': 20,
            'zentry': 1.7,
            'zexit': 0.5,
            'vol_period': 10,
            'vol_threshold': 0.012,
            'stop_loss': 0.05,      # 5% stop loss
            'take_profit': 0.08,    # 8% take profit
            'trailing_stop': 0.03,  # 3% trailing stop
            'min_volume': 100,
            'rsi_period': 14,
            'rsi_threshold': 40,
            'trend_period': 200
        },
        '1h': {
            'period': 50,
            'zentry': 2.0,
            'zexit': 0.5,
            'vol_period': 20,
            'vol_threshold': 0.02,
            'stop_loss': 0.06,      # 6% stop loss
            'take_profit': 0.1,     # 10% take profit
            'trailing_stop': 0.04,  # 4% trailing stop
            'min_volume': 100,
            'rsi_period': 14,
            'rsi_threshold': 40,
            'trend_period': 200
        }
    }
    
    results = []
    for tf in timeframes:
        print(f"\nTesting {tf} timeframe...")
        result = run_backtest(tf, **params[tf])
        results.append(result)
        print(f"Final Value: ${result['final_value']:.2f}")
        sharpe = result['sharpe'] if result['sharpe'] is not None else 'N/A'
        returns = result['returns'] if result['returns'] is not None else 'N/A'
        drawdown = result['drawdown'] if result['drawdown'] is not None else 'N/A'
        print(f"Sharpe Ratio: {sharpe if sharpe == 'N/A' else f'{sharpe:.2f}'}")
        print(f"Annual Return: {returns if returns == 'N/A' else f'{returns:.2f}%'}")
        print(f"Max Drawdown: {drawdown if drawdown == 'N/A' else f'{drawdown:.2f}%'}")
        print(f"Total Trades: {result['total_trades']}")
        win_rate = (result['won_trades'] / result['total_trades'] * 100) if result['total_trades'] > 0 else 0
        print(f"Win Rate: {win_rate:.2f}%")
    
    # Sort results by final value
    results.sort(key=lambda x: x['final_value'], reverse=True)
    
    print("\n=== FINAL RANKINGS BY TIMEFRAME ===")
    for i, result in enumerate(results, 1):
        sharpe = result['sharpe'] if result['sharpe'] is not None else 'N/A'
        returns = result['returns'] if result['returns'] is not None else 'N/A'
        drawdown = result['drawdown'] if result['drawdown'] is not None else 'N/A'
        print(f"\n{i}. {result['timeframe']} Timeframe")
        print(f"   Final Value: ${result['final_value']:.2f}")
        print(f"   Sharpe Ratio: {sharpe if sharpe == 'N/A' else f'{sharpe:.2f}'}")
        print(f"   Annual Return: {returns if returns == 'N/A' else f'{returns:.2f}%'}")
        print(f"   Max Drawdown: {drawdown if drawdown == 'N/A' else f'{drawdown:.2f}%'}")
        print(f"   Total Trades: {result['total_trades']}")
        win_rate = (result['won_trades'] / result['total_trades'] * 100) if result['total_trades'] > 0 else 0
        print(f"   Win Rate: {win_rate:.2f}%")

if __name__ == '__main__':
    main() 