import tensorflow as tf
from tensorflow.keras import layers, models

def build_advanced_model(input_shape):
    """
    Build an advanced DNN for volatility forecasting.
    Includes batch normalization, dropout, and flexible input size.
    """
    model = models.Sequential()
    model.add(layers.InputLayer(input_shape=input_shape))
    model.add(layers.Dense(128, activation='relu'))
    model.add(layers.BatchNormalization())
    model.add(layers.Dropout(0.3))
    model.add(layers.Dense(64, activation='relu'))
    model.add(layers.BatchNormalization())
    model.add(layers.Dropout(0.3))
    model.add(layers.Dense(32, activation='relu'))
    model.add(layers.Dense(1))  # Output: predicted volatility
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    return model
