#!/bin/bash

# Backend Development Script
# Run FastAPI backend in development mode

echo "🐍 Starting Backend Development Server..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your Azure OpenAI credentials before continuing."
    exit 1
fi

# Source environment variables
source .env

# Check if required environment variables are set
if [ -z "$AZURE_OPENAI_ENDPOINT" ] || [ -z "$AZURE_OPENAI_API_KEY" ] || [ -z "$AZURE_OPENAI_DEPLOYMENT_NAME" ]; then
    echo "❌ Missing required Azure OpenAI configuration in .env file"
    echo "   Please set: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_NAME"
    exit 1
fi

echo "✅ Environment configuration found"

# Check if PostgreSQL is running
echo "🔍 Checking PostgreSQL availability..."
if ./db-helper.sh status | grep -q "RUNNING"; then
    echo "✅ PostgreSQL is running"
elif ./db-helper.sh status | grep -q "STOPPED"; then
    echo "🔄 Starting PostgreSQL..."
    ./db-helper.sh start
    sleep 3
elif ./db-helper.sh status | grep -q "NOT FOUND"; then
    echo "🚀 Creating PostgreSQL container..."
    ./db-helper.sh create
    sleep 10
fi

# Check if Redis is running
echo "🔍 Checking Redis availability..."
REDIS_CONTAINER_NAME="redis-stack"
if docker ps --format "{{.Names}}" | grep -q "^${REDIS_CONTAINER_NAME}$"; then
    echo "✅ Redis container '${REDIS_CONTAINER_NAME}' is running."
elif docker ps -a --format "{{.Names}}" | grep -q "^${REDIS_CONTAINER_NAME}$"; then
    echo "🔄 Found stopped Redis container. Starting it..."
    docker start ${REDIS_CONTAINER_NAME}
    sleep 3
    echo "✅ Redis container started."
else
    echo "🚀 Redis container not found. Creating and starting a new one..."
    docker run -d --name ${REDIS_CONTAINER_NAME} -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
    echo "⏳ Waiting for Redis to initialize..."
    sleep 10
    echo "✅ New Redis container created and running."
fi

# Set database URL for local development
export DATABASE_URL="postgresql://postgres:password@localhost:5432/northwind"

echo "📂 Changing to backend directory..."
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "🚀 Starting FastAPI development server..."
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo "   Interactive Docs: http://localhost:8000/redoc"
echo ""
echo "💡 Press Ctrl+C to stop the server"
echo ""

# Start the development server with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
