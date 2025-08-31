from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import tensorflow as tf
import joblib
import numpy as np
import os
import sys
import logging
import shap
from datetime import datetime
from typing import Dict, List, Any
import traceback

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

# Set up rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Validate configuration
config_errors = config.validate()
if config_errors:
    for error in config_errors:
        logger.error(f"Configuration error: {error}")
    if config.is_production:
        raise RuntimeError("Configuration validation failed in production")

def validate_features_input(data: Dict[str, Any]) -> tuple[bool, str, np.ndarray]:
    """Validate features input and return status, error message, and features array"""
    if not data or 'features' not in data:
        return False, 'Missing features in request', None
    
    try:
        features = np.array(data['features'])
        
        # Validate shape
        if features.ndim != 2:
            return False, 'Features must be a 2D array', None
        
        # Validate batch size
        if features.shape[0] > config.MAX_PREDICTION_BATCH_SIZE:
            return False, f'Batch size exceeds maximum of {config.MAX_PREDICTION_BATCH_SIZE}', None
        
        # Validate feature count (should match training data)
        expected_features = 5  # log_return, volatility, ma_5, ma_10, rsi
        if features.shape[1] != expected_features:
            return False, f'Expected {expected_features} features, got {features.shape[1]}', None
        
        # Check for NaN or infinite values
        if np.any(np.isnan(features)) or np.any(np.isinf(features)):
            return False, 'Features contain NaN or infinite values', None
        
        return True, '', features
        
    except Exception as e:
        return False, f'Invalid features format: {str(e)}', None

@app.route('/')
def api_info():
    """API information endpoint"""
    return jsonify({
        'message': 'Welcome to the VolatiQ API!',
        'version': '1.0.0',
        'status': 'operational',
        'endpoints': {
            '/': 'API info',
            '/health': 'Health check',
            '/predict': 'POST: Predict volatility (expects JSON {"features": [[...], ...]})',
            '/explain': 'POST: Get SHAP feature attributions (expects JSON {"features": [[...], ...]})',
            '/metrics': 'GET: Model performance metrics'
        },
        'rate_limits': {
            'default': '200 per day, 50 per hour',
            'predict': '100 per hour',
            'explain': '50 per hour'
        }
    })

# Load model and scaler at startup
def load_model_and_scaler():
    """Load ML model and scaler with error handling"""
    try:
        logger.info(f"Loading model from {config.MODEL_PATH}")
        model = tf.keras.models.load_model(config.MODEL_PATH)
        
        logger.info(f"Loading scaler from {config.SCALER_PATH}")
        scaler = joblib.load(config.SCALER_PATH)
        
        logger.info("Model and scaler loaded successfully")
        return model, scaler
    except Exception as e:
        logger.error(f"Failed to load model or scaler: {str(e)}")
        raise

try:
    model, scaler = load_model_and_scaler()
except Exception as e:
    logger.critical(f"Critical error during startup: {str(e)}")
    if config.is_production:
        raise

@app.route('/health', methods=['GET'])
def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Check model availability
        model_status = model is not None and scaler is not None
        
        # Check if we can make a dummy prediction
        test_features = np.array([[0.01, 0.02, 100.0, 101.0, 50.0]])
        try:
            test_scaled = scaler.transform(test_features)
            test_pred = model.predict(test_scaled, verbose=0)
            prediction_status = True
        except Exception:
            prediction_status = False
        
        health_status = model_status and prediction_status
        
        return jsonify({
            'status': 'healthy' if health_status else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'model_loaded': model_status,
            'prediction_working': prediction_status,
            'version': '1.0.0'
        }), 200 if health_status else 503
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503

@app.route('/predict', methods=['POST'])
@limiter.limit("100 per hour")
def predict():
    """
    Predict volatility for given features
    Expects JSON: {"features": [[...], [...], ...]}
    Returns: {"predictions": [val1, val2, ...], "timestamp": "...", "model_version": "..."}
    """
    start_time = datetime.utcnow()
    data = request.get_json()
    
    # Validate input
    is_valid, error_msg, features = validate_features_input(data)
    if not is_valid:
        logger.warning(f"Invalid prediction request: {error_msg}")
        return jsonify({'error': error_msg}), 400
    
    try:
        # Scale features
        features_scaled = scaler.transform(features)
        
        # Make predictions
        preds = model.predict(features_scaled, verbose=0)
        preds = preds.flatten().tolist()
        
        # Log successful prediction
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Prediction successful: {len(preds)} predictions in {processing_time:.3f}s")
        
        return jsonify({
            'predictions': preds,
            'timestamp': start_time.isoformat(),
            'processing_time_seconds': processing_time,
            'model_version': '1.0.0',
            'num_predictions': len(preds)
        })
        
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'error': 'Internal server error during prediction',
            'timestamp': start_time.isoformat()
        }), 500

@app.route('/explain', methods=['POST'])
@limiter.limit("50 per hour")
def explain():
    """
    Generate SHAP explanations for predictions
    Expects JSON: {"features": [[...], [...], ...]}
    Returns: {"predictions": [...], "shap_values": [[...], ...], "feature_names": [...]}
    """
    start_time = datetime.utcnow()
    data = request.get_json()
    
    # Validate input
    is_valid, error_msg, features = validate_features_input(data)
    if not is_valid:
        logger.warning(f"Invalid explanation request: {error_msg}")
        return jsonify({'error': error_msg}), 400
    
    # Limit batch size for explanations (computationally expensive)
    if features.shape[0] > 10:
        return jsonify({'error': 'Maximum 10 samples allowed for explanations'}), 400
    
    try:
        features_scaled = scaler.transform(features)
        
        # Create SHAP explainer with minimal background
        background = np.zeros((1, features_scaled.shape[1]))
        explainer = shap.KernelExplainer(model.predict, background)
        
        # Generate SHAP values
        shap_vals = explainer.shap_values(features_scaled, nsamples=100)
        preds = model.predict(features_scaled, verbose=0).flatten().tolist()
        shap_vals = np.array(shap_vals).tolist()
        
        # Feature names
        feature_names = ['log_return', 'volatility', 'ma_5', 'ma_10', 'rsi']
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Explanation successful: {len(preds)} explanations in {processing_time:.3f}s")
        
        return jsonify({
            'predictions': preds,
            'shap_values': shap_vals,
            'feature_names': feature_names,
            'timestamp': start_time.isoformat(),
            'processing_time_seconds': processing_time
        })
        
    except Exception as e:
        logger.error(f"Explanation failed: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'error': 'Internal server error during explanation',
            'timestamp': start_time.isoformat()
        }), 500

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Get model performance metrics and system information"""
    try:
        # Model information
        model_info = {
            'model_type': 'Deep Neural Network',
            'framework': 'TensorFlow/Keras',
            'version': '1.0.0',
            'features': ['log_return', 'volatility', 'ma_5', 'ma_10', 'rsi'],
            'target': 'future_realized_volatility',
            'training_horizon': '5 days'
        }
        
        # System information
        system_info = {
            'python_version': sys.version.split()[0],
            'tensorflow_version': tf.__version__,
            'model_loaded': model is not None,
            'scaler_loaded': scaler is not None
        }
        
        return jsonify({
            'model_info': model_info,
            'system_info': system_info,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {str(e)}")
        return jsonify({'error': 'Failed to get metrics'}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Run the application
    app.run(
        host=config.API_HOST,
        port=config.API_PORT,
        debug=config.is_development
    )
