#!/bin/bash

# Smart Business Analytics Assistant - Startup Script (Using Existing DB)

echo "🚀 Starting Smart Business Analytics Assistant..."

# Check if Docker is installed
if ! command -v docker &> /dev/null
then
    echo "❌ Docker가 설치되어 있지 않습니다. 스크립트를 계속 진행하려면 Docker를 먼저 설치해주세요."
    echo "   Docker 설치 안내: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your Azure OpenAI credentials before continuing."
    echo "   Required: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_NAME"
    exit 1
fi

# Check if required environment variables are set
source .env

if [ -z "$AZURE_OPENAI_ENDPOINT" ] || [ -z "$AZURE_OPENAI_API_KEY" ] || [ -z "$AZURE_OPENAI_DEPLOYMENT_NAME" ]; then
    echo "❌ Missing required Azure OpenAI configuration in .env file"
    echo "   Please set: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_NAME"
    exit 1
fi

echo "✅ Environment configuration found"

# Check if existing PostgreSQL container is running
if docker ps --format "table {{.Names}}" | grep -q "northwind-postgres"; then
    echo "✅ Found existing PostgreSQL container (northwind-postgres)"
    
    # Test database connection
    if docker exec northwind-postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo "✅ PostgreSQL is responding"
        
        # Check if northwind database exists
        if docker exec northwind-postgres psql -U postgres -lqt | cut -d \| -f 1 | grep -qw northwind; then
            echo "✅ Northwind database found"
        else
            echo "⚠️  Northwind database not found. You may need to import the data."
            echo "   Run: docker exec -i northwind-postgres psql -U postgres < ./postgre/northwind.sql"
        fi
    else
        echo "❌ PostgreSQL container is not responding"
        exit 1
    fi
elif docker ps -a --format "table {{.Names}}" | grep -q "northwind-postgres"; then
    echo "🔄 Found stopped PostgreSQL container (northwind-postgres). Starting it..."
    docker start northwind-postgres
    
    # Wait for PostgreSQL to be ready
    echo "⏳ Waiting for PostgreSQL to start..."
    for i in {1..30}; do
        if docker exec northwind-postgres pg_isready -U postgres > /dev/null 2>&1; then
            echo "✅ PostgreSQL is now running"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            echo "❌ PostgreSQL failed to start within 30 seconds"
            exit 1
        fi
    done
    
    # Check if northwind database exists
    if docker exec northwind-postgres psql -U postgres -lqt | cut -d \| -f 1 | grep -qw northwind; then
        echo "✅ Northwind database found"
    else
        echo "⚠️  Northwind database not found. You may need to import the data."
        echo "   Run: docker exec -i northwind-postgres psql -U postgres < ./postgre/northwind.sql"
    fi
else
    echo "❌ PostgreSQL container 'northwind-postgres' not found"
    echo ""
    echo "🚀 Creating and starting new PostgreSQL container with Northwind data..."
    
    # Create and start PostgreSQL container with Northwind data
    docker run -d \
        --name northwind-postgres \
        -e POSTGRES_DB=northwind \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=password \
        -p 5432:5432 \
        -v "$(pwd)/postgre/northwind.sql:/docker-entrypoint-initdb.d/northwind.sql" \
        postgres:15
    
    # Wait for PostgreSQL to be ready
    echo "⏳ Waiting for PostgreSQL to initialize..."
    for i in {1..60}; do
        if docker exec northwind-postgres pg_isready -U postgres > /dev/null 2>&1; then
            echo "✅ PostgreSQL is running and ready"
            break
        fi
        sleep 1
        if [ $i -eq 60 ]; then
            echo "❌ PostgreSQL failed to initialize within 60 seconds"
            exit 1
        fi
    done
    
    echo "✅ New PostgreSQL container created with Northwind database"
fi

# Stop any existing text-to-sql containers (but keep the database)
echo "🛑 Stopping existing text-to-sql containers..."
docker stop text-to-sql-backend text-to-sql-frontend 2>/dev/null || true
docker rm text-to-sql-backend text-to-sql-frontend 2>/dev/null || true

# Build and start services (excluding database)
echo "🔨 Building and starting backend and frontend services..."
docker-compose up --build -d backend frontend

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Health check
echo "🔍 Checking service health..."

# Check backend
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running"
else
    echo "❌ Backend is not responding"
    echo "📋 Check backend logs: docker-compose logs backend"
fi

# Check frontend
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is running"
else
    echo "❌ Frontend is not responding"
    echo "📋 Check frontend logs: docker-compose logs frontend"
fi

echo ""
echo "🎉 Smart Business Analytics Assistant is ready!"
echo ""
echo "📱 Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📋 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down (this will keep your database running)"
