from binance.client import Client
import pandas as pd
from datetime import datetime, timedelta
import time
from tqdm import tqdm

def get_days_for_timeframe(timeframe):
    """
    Get appropriate number of days to download based on timeframe
    """
    # Scarica almeno 3 anni per ogni timeframe
    return 3 * 365

def fetch_historical_klines(symbol, interval, start_str, end_str=None):
    """
    Fetch historical klines/candlestick data from Binance
    
    Parameters:
    symbol (str): Trading pair symbol (e.g., 'ETHBTC')
    interval (str): Kline interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
    start_str (str): Start time in UTC format
    end_str (str, optional): End time in UTC format. Defaults to current time.
    
    Returns:
    pandas.DataFrame: DataFrame containing the klines data
    """
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
    print(f"\nFetching {symbol} {interval} data for {total_days} days...")
    
    # Fetch data in chunks to avoid hitting rate limits
    current_start = start_str
    with tqdm(total=total_days, desc=f"Downloading {interval} data") as pbar:
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
                
                # Update progress bar
                days_processed = (datetime.fromtimestamp(klines[-1][0] / 1000) - current_start).days
                pbar.update(days_processed)
                
                # Update start time for next iteration
                current_start = datetime.fromtimestamp(klines[-1][0] / 1000) + timedelta(seconds=1)
                
                # Sleep to avoid hitting rate limits
                time.sleep(0.1)
                
            except Exception as e:
                print(f"\nError fetching data: {e}")
                print("Retrying in 5 seconds...")
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

def main():
    # Define timeframes
    timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
    
    # Fetch data for each timeframe
    for tf in timeframes:
        try:
            # Calculate start date based on timeframe
            days = get_days_for_timeframe(tf)
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            print(f"\nProcessing {tf} timeframe (last {days} days)...")
            df = fetch_historical_klines('ETHBTC', tf, start_date)
            
            # Save to CSV
            filename = f'ethbtc_{tf}.csv'
            df.to_csv(filename)
            print(f"\n✓ Saved {len(df)} rows to {filename}")
            
        except Exception as e:
            print(f"\nError processing {tf} timeframe: {e}")
            continue

if __name__ == "__main__":
    main()
