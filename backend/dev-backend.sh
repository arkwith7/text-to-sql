#!/bin/bash

# Backend Development Script - SQLite + Redis Only
# Simple one-script solution for backend development setup
#
# 🎯 구성:
# - SQLite: 앱 데이터베이스 (사용자 계정, 채팅 기록)
# - Redis: 캐시/세션 저장소
# - PostgreSQL: 분석 대상 DB (프론트엔드에서 동적 연결)
#
# 📋 사용법:
#   ./dev-backend.sh
#
# 🔧 수행 작업:
#   1. .env 파일 확인 및 환경변수 로드
#   2. Redis 개발 컨테이너 생성/시작
#   3. Python 가상환경 및 의존성 설치
#   4. FastAPI 개발 서버 시작

echo "🐍 Starting Backend Development Environment..."

# Function to wait for Redis
wait_for_redis() {
    local container_name=$1
    echo "⏳ Waiting for Redis to be ready..."
    for i in {1..30}; do
        if docker exec $container_name redis-cli ping >/dev/null 2>&1; then
            echo "✅ Redis is ready"
            return 0
        fi
        echo "   Attempt $i/30: Redis not ready yet..."
        sleep 1
    done
    echo "❌ Redis failed to start"
    return 1
}

# Check if .env file exists in project root
if [ ! -f "../.env" ]; then
    echo "⚠️  .env file not found at ../.env"
    if [ -f "../.env.example" ]; then
        echo "📝 Copying from .env.example..."
        cp "../.env.example" "../.env"
        echo "✅ Please edit ../.env file with your Azure OpenAI credentials"
    else
        echo "❌ .env.example file not found. Please create ../.env file manually."
    fi
    exit 1
fi

# Load environment variables
echo "📋 Loading environment variables from ../.env..."
set -a
source "../.env"
set +a

# Check required Azure OpenAI settings
echo "🔍 Validating Azure OpenAI configuration..."
if [ -z "$AZURE_OPENAI_ENDPOINT" ] || [ -z "$AZURE_OPENAI_API_KEY" ] || [ -z "$AZURE_OPENAI_DEPLOYMENT_NAME" ]; then
    echo "❌ Missing required Azure OpenAI configuration in .env file"
    echo "   Please set: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_NAME"
    exit 1
fi

echo "✅ Azure OpenAI configuration validated"

# Setup Redis Development Container
REDIS_DEV_CONTAINER="redis-dev"
REDIS_DEV_PORT="6381"

echo ""
echo "📱 Setting up Redis development container..."

# Check if Redis port is available
if lsof -Pi :$REDIS_DEV_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "❌ Port $REDIS_DEV_PORT is already in use"
    echo "   Please stop the service using this port or use a different port"
    exit 1
fi

if docker ps --format "{{.Names}}" | grep -q "^${REDIS_DEV_CONTAINER}$"; then
    echo "✅ Redis development container already running: ${REDIS_DEV_CONTAINER}"
elif docker ps -a --format "{{.Names}}" | grep -q "^${REDIS_DEV_CONTAINER}$"; then
    echo "🔄 Starting stopped Redis development container..."
    docker start ${REDIS_DEV_CONTAINER}
    wait_for_redis $REDIS_DEV_CONTAINER
else
    echo "🚀 Creating Redis development container..."
    docker run -d \
        --name ${REDIS_DEV_CONTAINER} \
        -p ${REDIS_DEV_PORT}:6379 \
        --restart unless-stopped \
        redis:7-alpine
    
    wait_for_redis $REDIS_DEV_CONTAINER
fi

# Setup SQLite database path
SQLITE_DB_PATH="../app_data.db"
echo ""
echo "💾 SQLite database configuration..."
echo "   Database file: ${SQLITE_DB_PATH}"
if [ -f "$SQLITE_DB_PATH" ]; then
    echo "✅ SQLite database file exists"
else
    echo "📝 SQLite database will be created automatically when needed"
fi

# Set environment variables for development
# export APP_DATABASE_URL="sqlite+aiosqlite:///${SQLITE_DB_PATH}"  # .env의 값을 우선 사용하도록 주석 처리
export REDIS_URL="redis://localhost:${REDIS_DEV_PORT}"

# Set default values for missing environment variables
if [ -z "$SECRET_KEY" ]; then
    export SECRET_KEY="dev-secret-key-change-in-production"
fi

if [ -z "$JWT_SECRET_KEY" ]; then
    export JWT_SECRET_KEY="dev-jwt-secret-key-change-in-production"
fi

if [ -z "$ACCESS_TOKEN_EXPIRE_MINUTES" ]; then
    export ACCESS_TOKEN_EXPIRE_MINUTES="30"
fi

if [ -z "$REFRESH_TOKEN_EXPIRE_DAYS" ]; then
    export REFRESH_TOKEN_EXPIRE_DAYS="7"
fi

echo ""
echo "📊 Development Environment Summary:"
echo "   SQLite: ${SQLITE_DB_PATH} (app database)"
echo "   Redis: localhost:${REDIS_DEV_PORT} (cache/sessions)"
echo "   Azure OpenAI: ${AZURE_OPENAI_ENDPOINT}"
echo "   🔍 Analysis Target DBs: Configure via frontend UI"

# Test Redis connection
echo ""
echo "🔗 Testing Redis connection..."
if docker exec ${REDIS_DEV_CONTAINER} redis-cli ping >/dev/null 2>&1; then
    echo "✅ Redis connection test successful"
else
    echo "❌ Redis connection test failed"
    exit 1
fi

echo ""
echo "📂 Setting up Python environment..."
cd "$(dirname "$0")" || exit 1

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

# Validate configuration with Python
echo ""
echo "🔧 Validating backend configuration..."
if python -c "from core.config import get_settings, validate_settings; validate_settings(); print('✅ Configuration validation passed')" 2>/dev/null; then
    echo "✅ Backend configuration is valid"
else
    echo "❌ Backend configuration validation failed"
    echo "   Please check your .env file and config.py settings"
    exit 1
fi

echo ""
echo "🚀 Starting FastAPI development server..."
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo "   Interactive Docs: http://localhost:8000/redoc"
echo "   Health Check: http://localhost:8000/health"
echo ""
echo "🗄️  Development Environment:"
echo "   SQLite: ${SQLITE_DB_PATH} (app database)"
echo "   Redis: ${REDIS_DEV_CONTAINER} (localhost:${REDIS_DEV_PORT})"
echo ""
echo "🔗 Analysis Target Databases:"
echo "   PostgreSQL: Configure via frontend UI"
echo "   Other DBs: Configure via frontend UI"
echo ""
echo "🛠️  Management Commands:"
echo "   Stop Redis: docker stop ${REDIS_DEV_CONTAINER}"
echo "   Remove Redis: docker rm ${REDIS_DEV_CONTAINER}"
echo "   View Redis logs: docker logs ${REDIS_DEV_CONTAINER}"
echo "   SQLite location: ${SQLITE_DB_PATH}"
echo ""
echo "💡 Press Ctrl+C to stop the server"
echo "💡 Redis container will continue running for future use"
echo ""

# Start the development server with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-delay 1
