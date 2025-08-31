#!/bin/bash

echo "🚀 Starting VolatiQ Local Deployment"
echo "======================================"

# Activate virtual environment
source venv/bin/activate

# Check if API is running
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ API already running on http://localhost:5000"
else
    echo "🔄 Starting API server..."
    python api/app.py &
    API_PID=$!
    echo "API started with PID: $API_PID"
    sleep 5
fi

# Test API
echo "🧪 Testing API..."
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ API health check passed"
    echo "📊 API available at: http://localhost:5000"
    echo "📋 API documentation: http://localhost:5000/"
else
    echo "❌ API health check failed"
    exit 1
fi

echo ""
echo "🎯 Next Steps:"
echo "1. API is running at: http://localhost:5000"
echo "2. Test with: curl http://localhost:5000/health"
echo "3. Start dashboard with: python dashboard/app.py"
echo "4. Visit dashboard at: http://localhost:8050"
echo ""
echo "🔧 To start dashboard in new terminal:"
echo "   cd /Users/omanand/Desktop/Projects/VolatiQ"
echo "   source venv/bin/activate"
echo "   python dashboard/app.py"
