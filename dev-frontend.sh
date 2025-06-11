#!/bin/bash

# Frontend Development Script
# Run Vue.js frontend in development mode

echo "⚡ Starting Frontend Development Server..."

# Check if backend is running
echo "🔍 Checking if backend is available..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "⚠️  Backend is not running on port 8000"
    echo "   Please start the backend first with: ./dev-backend.sh"
    echo "   Or use full docker setup with: ./start-existing-db.sh"
    echo ""
    echo "   Continue anyway? (y/N)"
    read -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📂 Changing to frontend directory..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
else
    echo "✅ Node.js dependencies found"
fi

# Set environment variable for API connection
export VITE_API_BASE_URL="http://localhost:8000"

echo ""
echo "🚀 Starting Vue.js development server..."
echo "   Frontend: http://localhost:3000"
echo "   Connecting to Backend: http://localhost:8000"
echo ""
echo "💡 Press Ctrl+C to stop the server"
echo "🔥 Hot reload is enabled - changes will be reflected automatically"
echo ""

# Start the development server
npm run dev
