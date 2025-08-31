#!/bin/bash

echo "🚀 VolatiQ Local Deployment"
echo "👤 GitHub: Andromeda-crypto"
echo "================================"

# Navigate to project directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "python api/app.py" 2>/dev/null || true
pkill -f "python dashboard/app.py" 2>/dev/null || true
sleep 2

# Start API on port 5001
echo "🚀 Starting API server on port 5001..."
API_PORT=5001 python api/app.py &
API_PID=$!
echo "API started with PID: $API_PID"

# Wait for API to start
echo "⏳ Waiting for API to start..."
sleep 8

# Test API
echo "🧪 Testing API..."
if curl -s http://localhost:5001/health > /dev/null; then
    echo "✅ API is running on http://localhost:5001"
else
    echo "❌ API failed to start"
    exit 1
fi

# Start Dashboard
echo "📊 Starting Dashboard..."
API_URL=http://localhost:5001 python dashboard/app.py &
DASH_PID=$!
echo "Dashboard started with PID: $DASH_PID"

# Wait for dashboard
sleep 5

echo ""
echo "🎉 VolatiQ is now running locally!"
echo "================================"
echo "📋 Services:"
echo "  🔧 API:       http://localhost:5001"
echo "  📊 Dashboard: http://localhost:8050"
echo ""
echo "🧪 Test endpoints:"
echo "  curl http://localhost:5001/health"
echo "  curl http://localhost:5001/"
echo ""
echo "📱 Next steps:"
echo "  1. Visit http://localhost:8050 for the dashboard"
echo "  2. Test the API at http://localhost:5001"
echo "  3. Upload CSV data and run predictions"
echo ""
echo "🛑 To stop: pkill -f 'python api/app.py' && pkill -f 'python dashboard/app.py'"
echo ""

# Keep script running
echo "Press Ctrl+C to stop all services..."
trap 'echo "🛑 Stopping services..."; kill $API_PID $DASH_PID 2>/dev/null; exit' INT
wait
