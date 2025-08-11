import yfinance as yf
import pandas as pd
import os
 # fetch and preprocess historical market data
# Save to CSV for later use in model training
def fetch_and_preprocess(symbol='^GSPC', start='2015-01-01', end='2024-01-01', output_path='data/market_data.csv'):
    # Download historical data
    df = yf.download(symbol, start=start, end=end)
    # Basic preprocessing: keep only relevant columns, drop NAs
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
    df.index.name = 'Date'  # Set index name for clarity
    # Save to CSV, overwrite, with correct header
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path)
    print(f"Data saved to {output_path}")
    return df

if __name__ == '__main__':
    fetch_and_preprocess()


