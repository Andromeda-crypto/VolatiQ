# VolatiQ API Documentation

## Overview

The VolatiQ API provides endpoints for market volatility prediction using advanced machine learning models. The API is built with Flask and offers features like rate limiting, input validation, and comprehensive error handling.

**Base URL:** `http://localhost:5000` (development) or your deployed URL  
**Version:** 1.0.0  
**Authentication:** None (public API)

## Rate Limits

- **Default:** 200 requests per day, 50 per hour
- **Predictions:** 100 per hour
- **Explanations:** 50 per hour

Rate limits are applied per IP address.

## Endpoints

### 1. API Information

**GET** `/`

Get API information and available endpoints.

**Response:**
```json
{
  "message": "Welcome to the VolatiQ API!",
  "version": "1.0.0",
  "status": "operational",
  "endpoints": {
    "/": "API info",
    "/health": "Health check",
    "/predict": "POST: Predict volatility",
    "/explain": "POST: Get SHAP feature attributions",
    "/metrics": "GET: Model performance metrics"
  },
  "rate_limits": {
    "default": "200 per day, 50 per hour",
    "predict": "100 per hour",
    "explain": "50 per hour"
  }
}
```

### 2. Health Check

**GET** `/health`

Check API and model health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "model_loaded": true,
  "prediction_working": true,
  "version": "1.0.0"
}
```

**Status Codes:**
- `200`: Healthy
- `503`: Unhealthy

### 3. Predict Volatility

**POST** `/predict`

Generate volatility predictions for given financial features.

**Rate Limit:** 100 requests per hour

**Request Body:**
```json
{
  "features": [
    [0.001, 0.02, 150.5, 149.8, 65.2],
    [0.002, 0.018, 151.0, 150.1, 68.5]
  ]
}
```

**Feature Order:**
1. `log_return`: Log return of the asset
2. `volatility`: Rolling volatility 
3. `ma_5`: 5-day moving average
4. `ma_10`: 10-day moving average
5. `rsi`: Relative Strength Index

**Validation Rules:**
- Maximum 1000 samples per request
- Features must be a 2D array
- Exactly 5 features per sample
- No NaN or infinite values

**Response:**
```json
{
  "predictions": [0.0234, 0.0198],
  "timestamp": "2024-01-15T10:30:00.000Z",
  "processing_time_seconds": 0.123,
  "model_version": "1.0.0",
  "num_predictions": 2
}
```

**Error Responses:**
```json
{
  "error": "Missing features in request",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### 4. Explain Predictions

**POST** `/explain`

Generate SHAP explanations for volatility predictions.

**Rate Limit:** 50 requests per hour

**Request Body:**
```json
{
  "features": [
    [0.001, 0.02, 150.5, 149.8, 65.2]
  ]
}
```

**Limits:**
- Maximum 10 samples per request (computationally expensive)
- Same validation rules as `/predict`

**Response:**
```json
{
  "predictions": [0.0234],
  "shap_values": [
    [0.001, -0.003, 0.002, 0.001, -0.001]
  ],
  "feature_names": [
    "log_return", "volatility", "ma_5", "ma_10", "rsi"
  ],
  "timestamp": "2024-01-15T10:30:00.000Z",
  "processing_time_seconds": 2.456
}
```

### 5. Model Metrics

**GET** `/metrics`

Get model and system information.

**Response:**
```json
{
  "model_info": {
    "model_type": "Deep Neural Network",
    "framework": "TensorFlow/Keras",
    "version": "1.0.0",
    "features": ["log_return", "volatility", "ma_5", "ma_10", "rsi"],
    "target": "future_realized_volatility",
    "training_horizon": "5 days"
  },
  "system_info": {
    "python_version": "3.11.0",
    "tensorflow_version": "2.16.0",
    "model_loaded": true,
    "scaler_loaded": true
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

## Error Handling

### HTTP Status Codes

- `200`: Success
- `400`: Bad Request (invalid input)
- `404`: Not Found
- `429`: Too Many Requests (rate limit exceeded)
- `500`: Internal Server Error
- `503`: Service Unavailable (health check failed)

### Error Response Format

```json
{
  "error": "Error description",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Common Errors

1. **Invalid Features Format**
```json
{
  "error": "Features must be a 2D array"
}
```

2. **Batch Size Exceeded**
```json
{
  "error": "Batch size exceeds maximum of 1000"
}
```

3. **Rate Limit Exceeded**
```json
{
  "error": "Rate limit exceeded. Try again later."
}
```

## Usage Examples

### Python

```python
import requests
import numpy as np

# API base URL
api_url = "http://localhost:5000"

# Sample features: [log_return, volatility, ma_5, ma_10, rsi]
features = [
    [0.001, 0.02, 150.5, 149.8, 65.2],
    [0.002, 0.018, 151.0, 150.1, 68.5]
]

# Make prediction
response = requests.post(
    f"{api_url}/predict",
    json={"features": features}
)

if response.status_code == 200:
    result = response.json()
    print(f"Predictions: {result['predictions']}")
else:
    print(f"Error: {response.json()['error']}")

# Get explanation for first sample
explain_response = requests.post(
    f"{api_url}/explain",
    json={"features": [features[0]]}
)

if explain_response.status_code == 200:
    explanation = explain_response.json()
    print(f"SHAP values: {explanation['shap_values'][0]}")
```

### JavaScript

```javascript
const apiUrl = 'http://localhost:5000';

// Sample features
const features = [
  [0.001, 0.02, 150.5, 149.8, 65.2],
  [0.002, 0.018, 151.0, 150.1, 68.5]
];

// Make prediction
fetch(`${apiUrl}/predict`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ features })
})
.then(response => response.json())
.then(data => {
  if (data.predictions) {
    console.log('Predictions:', data.predictions);
  } else {
    console.error('Error:', data.error);
  }
});
```

### curl

```bash
# Health check
curl http://localhost:5000/health

# Make prediction
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": [
      [0.001, 0.02, 150.5, 149.8, 65.2]
    ]
  }'

# Get explanation
curl -X POST http://localhost:5000/explain \
  -H "Content-Type: application/json" \
  -d '{
    "features": [
      [0.001, 0.02, 150.5, 149.8, 65.2]
    ]
  }'
```

## Feature Engineering

To use the API effectively, you'll need to calculate the required features:

### Log Return
```python
import numpy as np
log_return = np.log(price / price_previous)
```

### Rolling Volatility
```python
import pandas as pd
volatility = pd.Series(log_returns).rolling(window=5).std()
```

### Moving Averages
```python
ma_5 = pd.Series(prices).rolling(window=5).mean()
ma_10 = pd.Series(prices).rolling(window=10).mean()
```

### RSI (Relative Strength Index)
```python
def calculate_rsi(prices, window=14):
    delta = pd.Series(prices).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))
```

## Model Information

- **Architecture**: Deep Neural Network with BatchNormalization and Dropout
- **Input Features**: 5 financial indicators
- **Output**: Predicted volatility (continuous value)
- **Training Data**: Historical S&P 500 data (2015-2024)
- **Prediction Horizon**: 5-day forward-looking volatility

## Security & Best Practices

1. **Rate Limiting**: Respect the rate limits to avoid being blocked
2. **Input Validation**: Ensure your features are properly formatted
3. **Error Handling**: Always check response status codes
4. **Batch Processing**: Use batch predictions for efficiency
5. **Monitoring**: Monitor your API usage and performance

## Support

For API issues or questions:
- Check the `/health` endpoint for system status
- Review error messages for specific issues
- Ensure your features match the expected format
- Verify you're within rate limits
