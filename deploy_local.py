#!/usr/bin/env python3
"""
VolatiQ Local Deployment Script
Automatically deploys both API and Dashboard locally with proper port handling
"""

import subprocess
import sys
import time
import requests
import webbrowser
import signal
import os
from pathlib import Path

# Global process tracking
api_process = None
dashboard_process = None

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Shutting down VolatiQ services...")
    cleanup_processes()
    sys.exit(0)

def cleanup_processes():
    """Clean up all processes"""
    global api_process, dashboard_process
    
    if api_process:
        api_process.terminate()
        try:
            api_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            api_process.kill()
        print("✅ API server stopped")
    
    if dashboard_process:
        dashboard_process.terminate()
        try:
            dashboard_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            dashboard_process.kill()
        print("✅ Dashboard stopped")

def check_port(port, timeout=2):
    """Check if a service is running on a port"""
    try:
        response = requests.get(f'http://localhost:{port}/health', timeout=timeout)
        return response.status_code == 200
    except:
        return False

def kill_port_processes(port):
    """Kill any processes using the specified port"""
    try:
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True, check=False)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    subprocess.run(['kill', pid], check=False)
                    print(f"🧹 Killed process {pid} using port {port}")
                except:
                    pass
    except:
        pass

def start_api():
    """Start the API server on port 5001"""
    global api_process
    
    print("🚀 Starting VolatiQ API server...")
    
    # Kill any existing processes on port 5001
    kill_port_processes(5001)
    time.sleep(1)
    
    # Start API server
    api_process = subprocess.Popen([
        sys.executable, 'api/app.py'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
      env={**os.environ, 'API_PORT': '5001'})
    
    # Wait for API to start
    print("⏳ Waiting for API to start...")
    for i in range(15):
        time.sleep(1)
        if check_port(5001):
            print("✅ API started successfully on http://localhost:5001")
            return True
        print(f"   Attempt {i+1}/15...")
    
    print("❌ API failed to start")
    return False

def start_dashboard():
    """Start the dashboard server"""
    global dashboard_process
    
    print("📊 Starting VolatiQ Dashboard...")
    
    # Kill any existing processes on port 8050
    kill_port_processes(8050)
    time.sleep(1)
    
    # Start dashboard
    dashboard_process = subprocess.Popen([
        sys.executable, 'dashboard/app.py'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
      env={**os.environ, 'API_URL': 'http://localhost:5001'})
    
    # Wait for dashboard to start
    print("⏳ Waiting for dashboard to start...")
    time.sleep(5)
    
    # Check if dashboard is accessible
    try:
        response = requests.get('http://localhost:8050', timeout=5)
        if response.status_code == 200:
            print("✅ Dashboard started successfully on http://localhost:8050")
            return True
    except:
        pass
    
    print("✅ Dashboard process started on http://localhost:8050")
    return True

def test_services():
    """Test that both services are working"""
    print("\n🧪 Testing services...")
    
    # Test API
    try:
        response = requests.get('http://localhost:5001/health', timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API Health: {health_data['status']}")
            print(f"   Model loaded: {health_data.get('model_loaded', 'Unknown')}")
        else:
            print(f"⚠️  API Health check returned: {response.status_code}")
    except Exception as e:
        print(f"❌ API Health check failed: {e}")
        return False
    
    # Test prediction
    try:
        test_data = {'features': [[0.001, 0.02, 150.5, 149.8, 65.2]]}
        response = requests.post('http://localhost:5001/predict', json=test_data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            prediction = result['predictions'][0]
            print(f"✅ Prediction test: {prediction:.6f}")
        else:
            print(f"⚠️  Prediction test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Prediction test failed: {e}")
    
    return True

def open_browser():
    """Open browser tabs"""
    print("\n🌐 Opening browser...")
    try:
        webbrowser.open('http://localhost:5001')
        time.sleep(1)
        webbrowser.open('http://localhost:8050')
        print("✅ Browser tabs opened")
    except:
        print("⚠️  Could not open browser automatically")

def main():
    """Main deployment function"""
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 VolatiQ Local Deployment")
    print("=" * 50)
    print("👤 GitHub: Andromeda-crypto")
    print("📁 Project: VolatiQ - Quantitative Risk Intelligence")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path('api/app.py').exists():
        print("❌ Please run this script from the VolatiQ project root")
        print("   Current directory:", os.getcwd())
        sys.exit(1)
    
    # Check virtual environment
    if not sys.prefix != sys.base_prefix:
        print("⚠️  Virtual environment not detected")
        print("   Please run: source venv/bin/activate")
    
    # Start API
    if not start_api():
        print("❌ Failed to start API. Exiting.")
        cleanup_processes()
        sys.exit(1)
    
    # Start Dashboard
    if not start_dashboard():
        print("❌ Failed to start Dashboard. Continuing anyway.")
    
    # Test services
    test_services()
    
    # Open browser
    open_browser()
    
    # Display status
    print("\n" + "=" * 50)
    print("🎉 VolatiQ is LIVE locally!")
    print("=" * 50)
    print("📋 Services running:")
    print("  🔧 API Server:    http://localhost:5001")
    print("  📊 Dashboard:     http://localhost:8050")
    print()
    print("🧪 Quick tests:")
    print("  curl http://localhost:5001/health")
    print("  curl http://localhost:5001/")
    print()
    print("📱 Usage:")
    print("  1. Visit http://localhost:8050 for the dashboard")
    print("  2. Upload CSV with features: log_return, volatility, ma_5, ma_10, rsi")
    print("  3. Run predictions and explore SHAP explanations")
    print("  4. Use API endpoints for programmatic access")
    print()
    print("📚 Documentation:")
    print("  • API Docs: See API_DOCUMENTATION.md")
    print("  • Deployment: See DEPLOYMENT_GUIDE.md")
    print("  • Quick Start: See START_HERE.md")
    print()
    print("🛑 Press Ctrl+C to stop all services")
    print("=" * 50)
    
    # Keep running until interrupted
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass  # Handled by signal handler

if __name__ == "__main__":
    main()
