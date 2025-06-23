#!/bin/bash

# Backend Development Script
# Run FastAPI backend in development mode
#
# 🎯 주요 기능:
# - Text-to-SQL 백엔드 개발 환경 전용 시작 스크립트
# - .env 파일 기반 환경 설정 자동 검증
# - Redis 컨테이너 자동 관리 (Docker)
# - Python 가상환경 및 의존성 패키지 자동 설정
# - FastAPI 개발 서버 핫 리로드 모드로 실행
#
# 📋 사용법:
#   ./dev-backend.sh
#
# 🔧 수행 작업:
#   1. .env 파일 존재 및 필수 환경변수 검증
#   2. Redis 컨테이너 상태 확인 및 자동 시작 (필요시)
#   3. Python 가상환경 활성화 및 의존성 설치
#   4. 백엔드 환경 설정 검증 (config.py 실행)
#   5. FastAPI 개발 서버 시작 (uvicorn --reload)
#
# 📦 관리 대상:
#   - Redis Stack: redis-stack (애플리케이션 캐시 및 세션)
#   - Python 가상환경: venv (백엔드 의존성)
#   - FastAPI 서버: localhost:8000 (개발 서버)
#
# ⚙️ 필수 환경 설정:
#   - AZURE_OPENAI_ENDPOINT: Azure OpenAI 서비스 엔드포인트
#   - AZURE_OPENAI_API_KEY: Azure OpenAI API 키
#   - AZURE_OPENAI_DEPLOYMENT_NAME: 배포된 모델 이름
#   - DATABASE_URL: PostgreSQL 연결 URL (외부 데이터베이스)
#   - REDIS_URL: Redis 연결 URL (애플리케이션 캐시 및 세션)
#   - SECRET_KEY: JWT 토큰 암호화 키
#   - REFRESH_TOKEN_EXPIRE_DAYS: 리프레시 토큰 만료 기간
#
# 💡 개발 워크플로우:
#   1. 외부 PostgreSQL (Northwind 데이터)가 실행 중이어야 함
#   2. Redis는 자동으로 컨테이너 상태 확인 및 시작
#   3. 코드 변경 시 핫 리로드로 자동 반영
#   4. 백엔드 API만 로컬에서 개발 시 사용
#
# 🚨 주의사항:
#   - 외부 PostgreSQL (Northwind 데이터)가 미리 실행되어 있어야 함
#   - Redis는 Docker 컨테이너로 자동 관리됨
#   - 포트 충돌 시 기존 서비스 확인 필요 (8000, 6379, 8001)

echo "🐍 Starting Backend Development Server..."

# Function to parse Redis URL and extract components
parse_redis_url() {
    local url="$1"
    # Extract components from redis://host:port
    if [[ $url =~ redis://([^:]+):([0-9]+) ]]; then
        REDIS_HOST="${BASH_REMATCH[1]}"
        REDIS_PORT="${BASH_REMATCH[2]}"
    elif [[ $url =~ redis://([^:]+) ]]; then
        REDIS_HOST="${BASH_REMATCH[1]}"
        REDIS_PORT="6379"
    else
        echo "❌ Invalid REDIS_URL format: $url"
        exit 1
    fi
}

# Check if .env file exists in project root
if [ ! -f "../.env" ]; then
    echo "⚠️  .env file not found at ../.env. Copying from .env.example..."
    if [ -f "../.env.example" ]; then
        cp "../.env.example" "../.env"
        echo "📝 Please edit ../.env file with your Azure OpenAI credentials before continuing."
    else
        echo "❌ .env.example file not found. Please create ../.env file manually."
    fi
    exit 1
fi

# Source environment variables
echo "📋 Loading environment variables from ../.env..."
set -a  # automatically export all variables
source "../.env"
set +a

# Check if required environment variables are set
echo "🔍 Validating environment configuration..."
if [ -z "$AZURE_OPENAI_ENDPOINT" ] || [ -z "$AZURE_OPENAI_API_KEY" ] || [ -z "$AZURE_OPENAI_DEPLOYMENT_NAME" ]; then
    echo "❌ Missing required Azure OpenAI configuration in .env file"
    echo "   Please set: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_NAME"
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not found in .env file"
    echo "   Please ensure external PostgreSQL is running and DATABASE_URL is set"
    exit 1
fi

if [ -z "$REDIS_URL" ]; then
    echo "❌ REDIS_URL not found in .env file"
    exit 1
fi

echo "✅ Environment configuration validated"

# Parse Redis URL to extract connection details
parse_redis_url "$REDIS_URL"

echo ""
echo "📊 Configuration Summary:"
echo "   Database: External PostgreSQL (${DATABASE_URL})"
echo "   Redis: ${REDIS_HOST}:${REDIS_PORT} (애플리케이션 캐시)"
echo "   Azure OpenAI: ${AZURE_OPENAI_ENDPOINT}"

# Check if Redis is running and manage Redis container
echo ""
echo "🔍 Checking Redis availability..."
REDIS_CONTAINER_NAME="redis-stack"

if docker ps --format "{{.Names}}" | grep -q "^${REDIS_CONTAINER_NAME}$"; then
    echo "✅ Redis container '${REDIS_CONTAINER_NAME}' is already running"
    
    # Test Redis connection
    echo "🔗 Testing Redis connection..."
    if docker exec $REDIS_CONTAINER_NAME redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis connection test successful"
    else
        echo "⚠️  Redis container is running but not responding. Restarting..."
        docker restart $REDIS_CONTAINER_NAME
        sleep 5
    fi
    
elif docker ps -a --format "{{.Names}}" | grep -q "^${REDIS_CONTAINER_NAME}$"; then
    echo "🔄 Found stopped Redis container. Starting it..."
    docker start ${REDIS_CONTAINER_NAME}
    sleep 5
    
    # Test Redis connection
    echo "🔗 Testing Redis connection..."
    for i in {1..10}; do
        if docker exec $REDIS_CONTAINER_NAME redis-cli ping > /dev/null 2>&1; then
            echo "✅ Redis is ready"
            break
        fi
        echo "   Attempt $i/10: Redis not ready yet..."
        sleep 1
    done
    
else
    echo "🚀 Redis container not found. Creating and starting a new one..."
    
    # Create Redis container
    docker run -d \
        --name ${REDIS_CONTAINER_NAME} \
        -p ${REDIS_PORT}:6379 \
        -p 8001:8001 \
        redis/redis-stack:latest
    
    echo "⏳ Waiting for Redis to initialize..."
    sleep 10
    
    # Test Redis connection
    echo "🔗 Testing Redis connection..."
    for i in {1..20}; do
        if docker exec $REDIS_CONTAINER_NAME redis-cli ping > /dev/null 2>&1; then
            echo "✅ Redis is ready"
            break
        fi
        echo "   Attempt $i/20: Redis not ready yet..."
        sleep 1
    done
fi

echo ""
echo "📂 Changing to backend directory..."
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
    echo "   Make sure external PostgreSQL (Northwind) is running"
    exit 1
fi

echo ""
echo "🚀 Starting FastAPI development server..."
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo "   Interactive Docs: http://localhost:8000/redoc"
echo "   Health Check: http://localhost:8000/health"
echo ""
echo "🗄️  Service Dependencies:"
echo "   PostgreSQL: ${DATABASE_URL} (외부 서비스)"
echo "   Redis: ${REDIS_HOST}:${REDIS_PORT} (Docker 컨테이너)"
echo "   Redis Insight: http://localhost:8001 (관리 도구)"
echo ""
echo "💡 Press Ctrl+C to stop the server"
echo "💡 Redis는 자동으로 관리되며, PostgreSQL (Northwind)는 외부에서 실행되어야 합니다"
echo ""

# Start the development server with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
