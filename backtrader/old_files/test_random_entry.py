import backtrader as bt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from random_entry_strategy import RandomEntryTPSL

def run_backtest(tp, sl, timeframe='1m'):
    cerebro = bt.Cerebro()
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
    cerebro.addstrategy(RandomEntryTPSL, tp=tp, sl=sl)
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)
    results = cerebro.run()
    final_value = cerebro.broker.getvalue()
    # Calcolo PnL annuo percentuale
    initial_value = 100000.0
    pnl_pct = (final_value - initial_value) / initial_value * 100
    return pnl_pct

def main():
    tp_values = np.linspace(0.001, 0.10, 5)  # TP da 0.1% a 10% con 5 punti
    sl_values = np.linspace(0.001, 0.10, 5)  # SL da 0.1% a 10% con 5 punti
    pnl_matrix = np.zeros((len(tp_values), len(sl_values)))
    for i, tp in enumerate(tp_values):
        for j, sl in enumerate(sl_values):
            print(f"Testing TP={tp:.3f}, SL={sl:.3f}")
            pnl_pct = run_backtest(tp, sl, timeframe='1m')
            pnl_matrix[i, j] = pnl_pct
    # Salva risultati
    df = pd.DataFrame(pnl_matrix, index=tp_values, columns=sl_values)
    df.to_csv('random_entry_grid_results.csv')
    # Plot heatmap
    plt.figure(figsize=(10,8))
    plt.imshow(pnl_matrix, origin='lower', aspect='auto', extent=[sl_values[0], sl_values[-1], tp_values[0], tp_values[-1]], cmap='RdYlGn')
    plt.colorbar(label='Annual PnL (%)')
    plt.xlabel('Stop Loss (%)')
    plt.ylabel('Take Profit (%)')
    plt.title('Random Entry TP/SL Grid Search (1m timeframe)')
    plt.savefig('random_entry_heatmap.png')
    plt.show()

if __name__ == '__main__':
    main() 