#!/bin/bash

# Smart Business Analytics Assistant - Fresh Start Script

echo "🚀 Starting Smart Business Analytics Assistant (Fresh Installation)..."

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

# Stop and remove any existing containers that might conflict
echo "🛑 Stopping any conflicting containers..."
docker stop northwind-postgres text-to-sql-postgres text-to-sql-backend text-to-sql-frontend 2>/dev/null || true
docker rm northwind-postgres text-to-sql-postgres text-to-sql-backend text-to-sql-frontend 2>/dev/null || true

# Restore the original docker-compose.yml with database service
echo "🔄 Restoring full docker-compose configuration..."

# Create a temporary docker-compose file with database included
cat > docker-compose-full.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL Database with Northwind data
  postgres:
    image: postgres:15
    container_name: text-to-sql-postgres
    environment:
      POSTGRES_DB: northwind
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgre/northwind.sql:/docker-entrypoint-initdb.d/northwind.sql
    networks:
      - text-to-sql-network

  # Backend API (FastAPI)
  backend:
    build: ./backend
    container_name: text-to-sql-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/northwind
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - AZURE_OPENAI_API_VERSION=${AZURE_OPENAI_API_VERSION}
      - AZURE_OPENAI_DEPLOYMENT_NAME=${AZURE_OPENAI_DEPLOYMENT_NAME}
    depends_on:
      - postgres
    networks:
      - text-to-sql-network
    volumes:
      - ./backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  # Frontend (Vue.js)
  frontend:
    build: ./frontend
    container_name: text-to-sql-frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
    depends_on:
      - backend
    networks:
      - text-to-sql-network
    volumes:
      - ./frontend:/app
      - /app/node_modules

volumes:
  postgres_data:

networks:
  text-to-sql-network:
    driver: bridge
EOF

# Build and start all services
echo "🔨 Building and starting all services..."
docker-compose -f docker-compose-full.yml up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Health check
echo "🔍 Checking service health..."

# Check backend
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running"
else
    echo "❌ Backend is not responding"
fi

# Check frontend
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is running"
else
    echo "❌ Frontend is not responding"
fi

# Check database
if docker exec text-to-sql-postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ Database is running"
else
    echo "❌ Database is not responding"
fi

echo ""
echo "🎉 Smart Business Analytics Assistant is ready!"
echo ""
echo "📱 Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📋 To view logs: docker-compose -f docker-compose-full.yml logs -f"
echo "🛑 To stop: docker-compose -f docker-compose-full.yml down"
