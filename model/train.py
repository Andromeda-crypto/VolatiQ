import pandas as pd
import numpy as np
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from model import build_advanced_model
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf

def compute_features(df, horizon=5):
    """
    Compute features for volatility forecasting.
    Features: log returns, rolling volatility, moving averages, RSI.
    """
    df = df.copy()
    df['log_return'] = np.log(df['Close'] / df['Close'].shift(1))
    df['volatility'] = df['log_return'].rolling(window=horizon).std()
    df['ma_5'] = df['Close'].rolling(window=5).mean()
    df['ma_10'] = df['Close'].rolling(window=10).mean()
    # RSI calculation
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['rsi'] = 100 - (100 / (1 + rs))
    # Drop rows with NaN values
    df = df.dropna()
    return df

def compute_target(df, horizon=5):
    """
    Compute future realized volatility as the target.
    """
    future_returns = np.log(df['Close'].shift(-horizon) / df['Close'])
    realized_vol = future_returns.rolling(window=horizon).std()
    return realized_vol

def prepare_data(df, horizon=5):
    df = compute_features(df, horizon)
    df['target_vol'] = compute_target(df, horizon)
    df = df.dropna()
    features = df[['log_return', 'volatility', 'ma_5', 'ma_10', 'rsi']].values
    target = df['target_vol'].values
    return features, target

def main(data_path='data/market_data.csv', model_save_path='model/saved_model', horizon=5):
    # Load data
    df = pd.read_csv(data_path, index_col=0)
    features, target = prepare_data(df, horizon)
    # Scale features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(features_scaled, target, test_size=0.2, random_state=42)
    # Build model
    model = build_advanced_model(input_shape=(X_train.shape[1],))
    # Train
    model.fit(X_train, y_train, epochs=30, batch_size=32, validation_data=(X_test, y_test))
    # Save model and scaler
    os.makedirs(model_save_path, exist_ok=True)
    model.save(os.path.join(model_save_path, 'volatility_model.keras'))
    # Save scaler
    import joblib
    joblib.dump(scaler, os.path.join(model_save_path, 'scaler.save'))
    print(f"Model and scaler saved to {model_save_path}")

if __name__ == '__main__':
    main()
