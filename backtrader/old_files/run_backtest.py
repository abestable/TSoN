import backtrader as bt
import datetime
from strategy_variations import (
    MeanReversionEMA,
    MeanReversionWithVolatility,
    MeanReversionWithTrend,
    MeanReversionWithRSI,
    MeanReversionWithVolume
)

def run_backtest(timeframe, **kwargs):
    cerebro = bt.Cerebro()
    
    # Add data
    data = bt.feeds.GenericCSVData(
        dataname=f'ethbtc_{timeframe}.csv',
        dtformat='%Y-%m-%d %H:%M:%S',
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
    final_value = cerebro.broker.getvalue()
    sharpe = strat.analyzers.sharpe.get_analysis()['sharperatio'] if 'sharperatio' in strat.analyzers.sharpe.get_analysis() else None
    returns = strat.analyzers.returns.get_analysis()
    drawdown = strat.analyzers.drawdown.get_analysis()
    trades = strat.analyzers.trades.get_analysis()
    
    return {
        'final_value': final_value,
        'sharpe': sharpe,
        'annual_return': returns.get('rnorm100', None),
        'max_drawdown': drawdown.get('max', {}).get('drawdown', None),
        'total_trades': trades.get('total', {}).get('total', 0),
        'win_rate': trades.get('won', {}).get('total', 0) / trades.get('total', {}).get('total', 1) * 100 if trades.get('total', {}).get('total', 0) > 0 else 0
    }

def main():
    timeframes = ['1m', '5m', '15m', '1h']
    
    # Optimized parameters for each timeframe
    params = {
        '1m': {
            'period': 20,
            'zentry': 2.0,
            'zexit': 0.5,
            'vol_period': 20,
            'vol_threshold': 1.5
        },
        '5m': {
            'period': 30,
            'zentry': 2.0,
            'zexit': 0.5,
            'vol_period': 30,
            'vol_threshold': 1.5
        },
        '15m': {
            'period': 40,
            'zentry': 2.0,
            'zexit': 0.5,
            'vol_period': 40,
            'vol_threshold': 1.5
        },
        '1h': {
            'period': 50,
            'zentry': 2.0,
            'zexit': 0.5,
            'vol_period': 50,
            'vol_threshold': 1.5
        }
    }
    
    results = []
    
    for timeframe in timeframes:
        print(f"\nTesting {timeframe} timeframe...")
        result = run_backtest(timeframe, **params[timeframe])
        results.append((timeframe, result))
        
        print(f"Final Value: ${result['final_value']:.2f}")
        print(f"Sharpe Ratio: {result['sharpe']:.2f}" if result['sharpe'] is not None else "Sharpe Ratio: N/A")
        print(f"Annual Return: {result['annual_return']:.2f}%" if result['annual_return'] is not None else "Annual Return: N/A")
        print(f"Max Drawdown: {result['max_drawdown']:.2f}%" if result['max_drawdown'] is not None else "Max Drawdown: N/A")
        print(f"Total Trades: {result['total_trades']}")
        print(f"Win Rate: {result['win_rate']:.2f}%")
    
    # Sort results by final value
    results.sort(key=lambda x: x[1]['final_value'], reverse=True)
    
    print("\n=== FINAL RANKINGS ===")
    for i, (timeframe, result) in enumerate(results, 1):
        print(f"\n{i}. {timeframe} Timeframe")
        print(f"   Final Value: ${result['final_value']:.2f}")
        print(f"   Sharpe Ratio: {result['sharpe']:.2f}" if result['sharpe'] is not None else "   Sharpe Ratio: N/A")
        print(f"   Annual Return: {result['annual_return']:.2f}%" if result['annual_return'] is not None else "   Annual Return: N/A")
        print(f"   Max Drawdown: {result['max_drawdown']:.2f}%" if result['max_drawdown'] is not None else "   Max Drawdown: N/A")
        print(f"   Total Trades: {result['total_trades']}")
        print(f"   Win Rate: {result['win_rate']:.2f}%")

if __name__ == '__main__':
    main()