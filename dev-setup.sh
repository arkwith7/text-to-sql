#!/bin/bash

# Development Environment Setup Script
# Starts database and shows options for backend/frontend

echo "🛠️ Text-to-SQL Development Environment"
echo ""

# Check and setup database
echo "🗄️ Setting up database..."
if ./db-helper.sh status | grep -q "RUNNING"; then
    echo "✅ PostgreSQL is already running"
elif ./db-helper.sh status | grep -q "STOPPED"; then
    echo "🔄 Starting PostgreSQL..."
    ./db-helper.sh start
    sleep 3
    echo "✅ PostgreSQL started"
elif ./db-helper.sh status | grep -q "NOT FOUND"; then
    echo "🚀 Creating PostgreSQL container..."
    ./db-helper.sh create
    sleep 10
    echo "✅ PostgreSQL created and started"
fi

# Check .env file
if [ ! -f .env ]; then
    echo ""
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your Azure OpenAI credentials"
    echo ""
fi

echo ""
echo "🎯 Development Environment Ready!"
echo ""
echo "Choose your development mode:"
echo ""
echo "1️⃣  Backend Development:"
echo "   Terminal 1: ./dev-backend.sh"
echo "   → Runs Python FastAPI with auto-reload"
echo "   → API available at http://localhost:8000"
echo ""
echo "2️⃣  Frontend Development:"
echo "   Terminal 2: ./dev-frontend.sh" 
echo "   → Runs Vue.js with hot reload"
echo "   → App available at http://localhost:3000"
echo ""
echo "3️⃣  Full Docker Development:"
echo "   ./start-existing-db.sh"
echo "   → Runs everything in containers"
echo ""
echo "📋 Useful Commands:"
echo "   ./db-helper.sh status    # Check database status"
echo "   ./db-helper.sh logs      # View database logs"
echo "   ./db-helper.sh stop      # Stop database"
echo ""
echo "🔧 For VS Code users:"
echo "   - Backend debugging: Set Python interpreter to ./backend/venv/bin/python"
echo "   - Frontend debugging: Use Vue.js DevTools extension"
echo ""

# Show current status
echo "📊 Current Status:"
echo -n "   Database: "
if ./db-helper.sh status | grep -q "RUNNING"; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

echo -n "   Backend:  "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Running (http://localhost:8000)"
else
    echo "❌ Not running"
fi

echo -n "   Frontend: "
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Running (http://localhost:3000)"
else
    echo "❌ Not running"
fi
