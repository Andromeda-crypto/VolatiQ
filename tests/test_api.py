"""
Test suite for VolatiQ API endpoints
"""
import pytest
import json
import numpy as np
from api.app import app, config


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    with app.test_client() as client:
        yield client


class TestAPIEndpoints:
    """Test API endpoints"""
    
    def test_api_info(self, client):
        """Test API info endpoint"""
        response = client.get('/')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'message' in data
        assert 'version' in data
        assert 'endpoints' in data
        assert data['version'] == '1.0.0'
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        
        # Should return 200 or 503 depending on model availability
        assert response.status_code in [200, 503]
        
        data = json.loads(response.data)
        assert 'status' in data
        assert 'timestamp' in data
        assert data['status'] in ['healthy', 'unhealthy']
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint"""
        response = client.get('/metrics')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'model_info' in data
        assert 'system_info' in data
        assert 'timestamp' in data
        
        # Check model info structure
        model_info = data['model_info']
        assert 'model_type' in model_info
        assert 'framework' in model_info
        assert 'features' in model_info
        assert len(model_info['features']) == 5
    
    def test_predict_valid_input(self, client):
        """Test prediction with valid input"""
        valid_features = {
            "features": [
                [0.001, 0.02, 150.5, 149.8, 65.2],
                [0.002, 0.018, 151.0, 150.1, 68.5]
            ]
        }
        
        response = client.post('/predict',
                              data=json.dumps(valid_features),
                              content_type='application/json')
        
        # Should work if model is loaded, otherwise return 500
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'predictions' in data
            assert 'timestamp' in data
            assert 'model_version' in data
            assert len(data['predictions']) == 2
    
    def test_predict_invalid_input(self, client):
        """Test prediction with invalid input"""
        # Missing features
        response = client.post('/predict',
                              data=json.dumps({}),
                              content_type='application/json')
        assert response.status_code == 400
        
        # Wrong feature count
        invalid_features = {
            "features": [
                [0.001, 0.02, 150.5]  # Only 3 features instead of 5
            ]
        }
        response = client.post('/predict',
                              data=json.dumps(invalid_features),
                              content_type='application/json')
        assert response.status_code == 400
        
        # NaN values
        nan_features = {
            "features": [
                [0.001, float('nan'), 150.5, 149.8, 65.2]
            ]
        }
        response = client.post('/predict',
                              data=json.dumps(nan_features),
                              content_type='application/json')
        assert response.status_code == 400
    
    def test_predict_batch_size_limit(self, client):
        """Test prediction batch size limits"""
        # Create a large batch (over limit)
        large_batch = {
            "features": [[0.001, 0.02, 150.5, 149.8, 65.2]] * 1001
        }
        
        response = client.post('/predict',
                              data=json.dumps(large_batch),
                              content_type='application/json')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'batch size exceeds maximum' in data['error'].lower()
    
    def test_explain_valid_input(self, client):
        """Test explanation with valid input"""
        valid_features = {
            "features": [
                [0.001, 0.02, 150.5, 149.8, 65.2]
            ]
        }
        
        response = client.post('/explain',
                              data=json.dumps(valid_features),
                              content_type='application/json')
        
        # Should work if model is loaded, otherwise return 500
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'predictions' in data
            assert 'shap_values' in data
            assert 'feature_names' in data
            assert len(data['feature_names']) == 5
    
    def test_explain_batch_limit(self, client):
        """Test explanation batch size limits"""
        # Create batch over limit for explanations
        large_batch = {
            "features": [[0.001, 0.02, 150.5, 149.8, 65.2]] * 11
        }
        
        response = client.post('/explain',
                              data=json.dumps(large_batch),
                              content_type='application/json')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'maximum 10 samples' in data['error'].lower()
    
    def test_404_endpoint(self, client):
        """Test 404 handling"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_method_not_allowed(self, client):
        """Test method not allowed"""
        response = client.put('/predict')
        assert response.status_code == 405


class TestInputValidation:
    """Test input validation functions"""
    
    def test_validate_features_input(self):
        """Test feature validation function"""
        from api.app import validate_features_input
        
        # Valid input
        valid_data = {"features": [[0.001, 0.02, 150.5, 149.8, 65.2]]}
        is_valid, error_msg, features = validate_features_input(valid_data)
        assert is_valid is True
        assert error_msg == ''
        assert features.shape == (1, 5)
        
        # Missing features
        is_valid, error_msg, features = validate_features_input({})
        assert is_valid is False
        assert 'missing features' in error_msg.lower()
        
        # Wrong dimensions
        wrong_dim = {"features": [0.001, 0.02, 150.5, 149.8, 65.2]}
        is_valid, error_msg, features = validate_features_input(wrong_dim)
        assert is_valid is False
        assert '2d array' in error_msg.lower()
        
        # Wrong feature count
        wrong_count = {"features": [[0.001, 0.02, 150.5]]}
        is_valid, error_msg, features = validate_features_input(wrong_count)
        assert is_valid is False
        assert 'expected 5 features' in error_msg.lower()


class TestConfiguration:
    """Test configuration management"""
    
    def test_config_validation(self):
        """Test configuration validation"""
        from config import Config
        
        # Create test config
        test_config = Config()
        test_config.FLASK_ENV = 'production'
        test_config.SECRET_KEY = 'dev-key-change-in-production'
        
        errors = test_config.validate()
        assert len(errors) > 0
        assert any('SECRET_KEY must be changed' in error for error in errors)
    
    def test_config_properties(self):
        """Test configuration properties"""
        from config import Config
        
        dev_config = Config()
        dev_config.FLASK_ENV = 'development'
        assert dev_config.is_development is True
        assert dev_config.is_production is False
        
        prod_config = Config()
        prod_config.FLASK_ENV = 'production'
        assert prod_config.is_development is False
        assert prod_config.is_production is True


if __name__ == '__main__':
    pytest.main([__file__])
