#!/usr/bin/env python3
"""
VolatiQ Setup Validation Script
Validates that the environment is properly configured and ready for deployment
"""

import sys
import os
import subprocess
import importlib
import requests
import threading
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_python_version():
    """Check Python version compatibility"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible. Need Python 3.11+")
        return False

def check_dependencies():
    """Check if all required packages are installed"""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        'flask', 'flask_limiter', 'tensorflow', 'dash', 'pandas', 
        'numpy', 'joblib', 'shap', 'requests', 'dash_bootstrap_components',
        'sklearn', 'yfinance', 'dotenv', 'redis', 'psycopg2',
        'gunicorn', 'pytest'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Not found")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed")
    return True

def check_model_files():
    """Check if model files exist"""
    print("\n🤖 Checking model files...")
    
    model_path = project_root / "model" / "saved_model" / "volatility_model.keras"
    scaler_path = project_root / "model" / "saved_model" / "scaler.save"
    
    if model_path.exists():
        print(f"✅ Model file found: {model_path}")
        model_ok = True
    else:
        print(f"❌ Model file missing: {model_path}")
        model_ok = False
    
    if scaler_path.exists():
        print(f"✅ Scaler file found: {scaler_path}")
        scaler_ok = True
    else:
        print(f"❌ Scaler file missing: {scaler_path}")
        scaler_ok = False
    
    if not (model_ok and scaler_ok):
        print("Run: python model/train.py")
        return False
    
    return True

def check_directories():
    """Check if required directories exist"""
    print("\n📁 Checking directories...")
    
    required_dirs = ['logs', 'data', 'model/saved_model']
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"⚠️  Creating {dir_path}/")
            full_path.mkdir(parents=True, exist_ok=True)
    
    return True

def test_api_startup():
    """Test that the API can start and respond"""
    print("\n🌐 Testing API startup...")
    
    try:
        # Import and start API
        from api.app import app
        
        def start_server():
            app.run(host='127.0.0.1', port=5003, debug=False, use_reloader=False)
        
        # Start server in background
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        time.sleep(3)
        
        # Test health endpoint
        response = requests.get('http://127.0.0.1:5003/health', timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API health check passed")
            print(f"   Status: {health_data['status']}")
            print(f"   Model loaded: {health_data['model_loaded']}")
            print(f"   Prediction working: {health_data['prediction_working']}")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API startup failed: {e}")
        return False

def test_dashboard_import():
    """Test that the dashboard can be imported"""
    print("\n📊 Testing dashboard import...")
    
    try:
        from dashboard.app import app as dash_app
        print("✅ Dashboard import successful")
        return True
    except Exception as e:
        print(f"❌ Dashboard import failed: {e}")
        return False

def test_prediction():
    """Test a sample prediction"""
    print("\n🔮 Testing prediction...")
    
    try:
        from api.app import app
        
        def start_server():
            app.run(host='127.0.0.1', port=5004, debug=False, use_reloader=False)
        
        # Start server in background
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        time.sleep(3)
        
        # Test prediction
        test_data = {
            'features': [[0.001, 0.02, 150.5, 149.8, 65.2]]
        }
        
        response = requests.post(
            'http://127.0.0.1:5004/predict',
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Prediction successful")
            print(f"   Prediction: {result['predictions'][0]:.6f}")
            print(f"   Processing time: {result['processing_time_seconds']:.3f}s")
            return True
        else:
            print(f"❌ Prediction failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Prediction test failed: {e}")
        return False

def check_environment_config():
    """Check environment configuration"""
    print("\n⚙️  Checking environment configuration...")
    
    try:
        from config import config
        
        print(f"✅ Environment: {config.FLASK_ENV}")
        print(f"✅ API Host: {config.API_HOST}")
        print(f"✅ API Port: {config.API_PORT}")
        print(f"✅ Dashboard Host: {config.DASH_HOST}")
        print(f"✅ Dashboard Port: {config.DASH_PORT}")
        
        # Check for production settings
        if config.is_production:
            warnings = []
            if config.SECRET_KEY == 'dev-key-change-in-production':
                warnings.append("SECRET_KEY needs to be changed in production")
            if config.JWT_SECRET_KEY == 'jwt-secret-change-in-production':
                warnings.append("JWT_SECRET_KEY needs to be changed in production")
            
            if warnings:
                print("⚠️  Production warnings:")
                for warning in warnings:
                    print(f"   - {warning}")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment config error: {e}")
        return False

def main():
    """Run all validation checks"""
    print("🚀 VolatiQ Setup Validation")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Model Files", check_model_files),
        ("Directories", check_directories),
        ("Environment Config", check_environment_config),
        ("API Startup", test_api_startup),
        ("Dashboard Import", test_dashboard_import),
        ("Prediction Test", test_prediction),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} check failed with exception: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 ALL CHECKS PASSED! VolatiQ is ready for deployment!")
        print("\nNext steps:")
        print("  1. docker-compose up -d")
        print("  2. Visit http://localhost:5000 (API)")
        print("  3. Visit http://localhost:8050 (Dashboard)")
        return True
    else:
        print(f"\n⚠️  {failed} checks failed. Please fix the issues above before deployment.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
