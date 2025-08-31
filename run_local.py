#!/usr/bin/env python3
"""
VolatiQ Local Development Runner
Starts both API and Dashboard services locally
"""

import subprocess
import sys
import time
import requests
import webbrowser
from pathlib import Path

def check_port(port):
    """Check if a port is available"""
    try:
        response = requests.get(f'http://localhost:{port}/health', timeout=2)
        return response.status_code == 200
    except:
        return False

def start_api():
    """Start the API server"""
    print("🚀 Starting VolatiQ API server...")
    
    # Check if API is already running
    if check_port(5000):
        print("✅ API already running on http://localhost:5000")
        return None
    
    # Start API in background
    api_process = subprocess.Popen([
        sys.executable, 'api/app.py'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for API to start
    for i in range(10):
        time.sleep(1)
        if check_port(5000):
            print("✅ API started successfully on http://localhost:5000")
            return api_process
        print(f"⏳ Waiting for API to start... ({i+1}/10)")
    
    print("❌ API failed to start")
    return None

def start_dashboard():
    """Start the dashboard"""
    print("📊 Starting VolatiQ Dashboard...")
    
    dashboard_process = subprocess.Popen([
        sys.executable, 'dashboard/app.py'
    ])
    
    # Wait a moment for dashboard to start
    time.sleep(3)
    print("✅ Dashboard started on http://localhost:8050")
    
    return dashboard_process

def open_browser():
    """Open browser tabs for API and Dashboard"""
    time.sleep(2)
    print("🌐 Opening browser...")
    
    try:
        webbrowser.open('http://localhost:5000')
        time.sleep(1)
        webbrowser.open('http://localhost:8050')
        print("✅ Browser tabs opened")
    except:
        print("⚠️  Could not open browser automatically")

def main():
    """Main function to start VolatiQ locally"""
    print("🎯 VolatiQ Local Development")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path('api/app.py').exists():
        print("❌ Please run this script from the VolatiQ project root")
        sys.exit(1)
    
    # Start API
    api_process = start_api()
    if not api_process and not check_port(5000):
        print("❌ Failed to start API. Exiting.")
        sys.exit(1)
    
    # Start Dashboard
    dashboard_process = start_dashboard()
    
    # Open browser
    open_browser()
    
    print("\n" + "=" * 40)
    print("🎉 VolatiQ is running locally!")
    print("=" * 40)
    print("📋 Services:")
    print("  • API:       http://localhost:5000")
    print("  • Dashboard: http://localhost:8050")
    print("\n🧪 Test endpoints:")
    print("  • Health:    curl http://localhost:5000/health")
    print("  • API Info:  curl http://localhost:5000/")
    print("\n📱 Next steps:")
    print("  1. Visit the dashboard at http://localhost:8050")
    print("  2. Upload a CSV file with financial features")
    print("  3. Run predictions and explore SHAP explanations")
    print("  4. Test the API endpoints with curl or Postman")
    print("\n🛑 Press Ctrl+C to stop all services")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping VolatiQ services...")
        
        if api_process:
            api_process.terminate()
            print("✅ API stopped")
        
        if dashboard_process:
            dashboard_process.terminate()
            print("✅ Dashboard stopped")
        
        print("👋 VolatiQ services stopped. Goodbye!")

if __name__ == "__main__":
    main()
