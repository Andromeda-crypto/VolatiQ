from flask import Flask, request, jsonify
import tensorflow as tf
import joblib
import numpy as np
import os
import shap

MODEL_PATH = os.path.join(os.path.dirname(__file__), '../model/saved_model/volatility_model.keras')
SCALER_PATH = os.path.join(os.path.dirname(__file__), '../model/saved_model/scaler.save')

app = Flask(__name__)

# Root endpoint for browser visits
def api_info():
    return jsonify({
        'message': 'Welcome to the VolatiQ API!',
        'endpoints': {
            '/': 'API info',
            '/health': 'Health check',
            '/predict': 'POST: Predict volatility (expects JSON {"features": [[...], ...]})',
            '/explain': 'POST: Get SHAP feature attributions (expects JSON {"features": [[...], ...]})'
        }
    })

app.add_url_rule('/', 'api_info', api_info, methods=['GET'])

# Load model and scaler at startup
def load_model_and_scaler():
    model = tf.keras.models.load_model(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    return model, scaler

model, scaler = load_model_and_scaler()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200

@app.route('/predict', methods=['POST'])
def predict():
    """
    Expects JSON: {"features": [[...], [...], ...]}
    Returns: {"predictions": [val1, val2, ...]}
    """
    data = request.get_json()
    if not data or 'features' not in data:
        return jsonify({'error': 'Missing features in request'}), 400
    try:
        features = np.array(data['features'])
        features_scaled = scaler.transform(features)
        preds = model.predict(features_scaled)
        preds = preds.flatten().tolist()
        return jsonify({'predictions': preds})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/explain', methods=['POST'])
def explain():
    """
    Expects JSON: {"features": [[...], [...], ...]}
    Returns: {"predictions": [...], "shap_values": [[...], ...], "feature_names": [...]}
    """
    data = request.get_json()
    if not data or 'features' not in data:
        return jsonify({'error': 'Missing features in request'}), 400
    try:
        features = np.array(data['features'])
        features_scaled = scaler.transform(features)
        # Use a small background for KernelExplainer (first 50 rows of training data if available)
        background = np.zeros((1, features_scaled.shape[1]))
        explainer = shap.KernelExplainer(model.predict, background)
        shap_vals = explainer.shap_values(features_scaled, nsamples=100)
        preds = model.predict(features_scaled).flatten().tolist()
        shap_vals = np.array(shap_vals).tolist()
        # Try to get feature names from scaler or use generic
        feature_names = getattr(scaler, 'feature_names_in_', [f'feature_{i}' for i in range(features.shape[1])])
        return jsonify({
            'predictions': preds,
            'shap_values': shap_vals,
            'feature_names': list(feature_names)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
