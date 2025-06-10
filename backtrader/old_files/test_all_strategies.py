import backtrader as bt
import pandas as pd
from datetime import datetime
from advanced_strategies import (
    VolatilityBreakoutStrategy,
    MeanReversionWithMomentum,
    AdaptiveTrendFollowing
)

def run_backtest(strategy_class, timeframe, **kwargs):
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
    cerebro.addstrategy(strategy_class, **kwargs)
    
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
    returns = strat.analyzers.returns.get_analysis()['rnorm100'] if 'rnorm100' in strat.analyzers.returns.get_analysis() else None
    drawdown = strat.analyzers.drawdown.get_analysis()['max']['drawdown'] if 'max' in strat.analyzers.drawdown.get_analysis() else None
    trades = strat.analyzers.trades.get_analysis()
    
    return {
        'strategy': strategy_class.__name__,
        'timeframe': timeframe,
        'final_value': final_value,
        'sharpe': sharpe,
        'returns': returns,
        'drawdown': drawdown,
        'total_trades': trades.get('total', {}).get('total', 0),
        'won_trades': trades.get('won', {}).get('total', 0),
        'lost_trades': trades.get('lost', {}).get('total', 0)
    }

def main():
    timeframes = ['1m', '5m', '15m', '1h']
    strategies = [
        (VolatilityBreakoutStrategy, {
            'atr_period': 14,
            'atr_multiplier': 2.0,
            'risk_per_trade': 0.02,
            'trailing_stop': 0.03,
            'profit_target': 0.06
        }),
        (MeanReversionWithMomentum, {
            'period': 20,
            'zentry': 2.0,
            'zexit': 0.5,
            'rsi_period': 14,
            'rsi_threshold': 30,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'vol_period': 20,
            'vol_threshold': 0.02,
            'risk_per_trade': 0.02
        }),
        (AdaptiveTrendFollowing, {
            'fast_period': 10,
            'slow_period': 30,
            'signal_period': 5,
            'atr_period': 14,
            'atr_multiplier': 2.0,
            'risk_per_trade': 0.02,
            'trailing_stop': 0.03,
            'profit_target': 0.06
        })
    ]
    
    results = []
    for strategy_class, params in strategies:
        print(f"\nTesting {strategy_class.__name__}...")
        for tf in timeframes:
            print(f"\nTesting {tf} timeframe...")
            result = run_backtest(strategy_class, tf, **params)
            results.append(result)
            
            # Print results
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
    
    # Print final rankings
    print("\n=== FINAL RANKINGS ===")
    for i, result in enumerate(results, 1):
        sharpe = result['sharpe'] if result['sharpe'] is not None else 'N/A'
        returns = result['returns'] if result['returns'] is not None else 'N/A'
        drawdown = result['drawdown'] if result['drawdown'] is not None else 'N/A'
        print(f"\n{i}. {result['strategy']} on {result['timeframe']} Timeframe")
        print(f"   Final Value: ${result['final_value']:.2f}")
        print(f"   Sharpe Ratio: {sharpe if sharpe == 'N/A' else f'{sharpe:.2f}'}")
        print(f"   Annual Return: {returns if returns == 'N/A' else f'{returns:.2f}%'}")
        print(f"   Max Drawdown: {drawdown if drawdown == 'N/A' else f'{drawdown:.2f}%'}")
        print(f"   Total Trades: {result['total_trades']}")
        win_rate = (result['won_trades'] / result['total_trades'] * 100) if result['total_trades'] > 0 else 0
        print(f"   Win Rate: {win_rate:.2f}%")

if __name__ == '__main__':
    main() 