#!/bin/bash

# Smart Business Analytics Assistant - Startup Script (Using Existing DB)
# Enhanced with .env configuration support
#
# 🎯 주요 기능:
# - 전체 Text-to-SQL 애플리케이션 스택의 통합 시작 스크립트
# - 기존 데이터베이스 컨테이너를 활용한 빠른 개발 환경 구성
# - .env 파일 기반 환경 설정 자동 검증 및 적용
# - PostgreSQL 및 Redis 서비스 상태 확인 및 자동 복구
# - 백엔드/프론트엔드 서비스 빌드 및 시작
# - 전체 시스템 헬스체크 및 접근성 테스트
#
# 📋 사용법:
#   ./start-existing-db.sh
#
# 🔧 수행 작업:
#   1. Docker 설치 확인
#   2. .env 파일 존재 및 필수 설정 검증
#   3. DATABASE_URL, REDIS_URL 파싱 및 설정 적용
#   4. PostgreSQL 컨테이너 상태 확인 및 시작
#   5. Redis 컨테이너 상태 확인 및 시작
#   6. 호스트에서 서비스 접근성 테스트
#   7. 기존 애플리케이션 컨테이너 정리
#   8. 백엔드/프론트엔드 서비스 빌드 및 시작
#   9. 전체 시스템 헬스체크
#
# 📦 관리 대상:
#   - PostgreSQL: northwind-postgres (데이터베이스 서비스)
#   - Redis: redis-stack (캐시 및 세션 스토어)
#   - Backend: text-to-sql-backend (FastAPI 서버)
#   - Frontend: text-to-sql-frontend (React 애플리케이션)
#
# ⚙️  필수 환경 설정:
#   - AZURE_OPENAI_ENDPOINT: Azure OpenAI 서비스 엔드포인트
#   - AZURE_OPENAI_API_KEY: Azure OpenAI API 키
#   - AZURE_OPENAI_DEPLOYMENT_NAME: 배포된 모델 이름
#   - DATABASE_URL: PostgreSQL 연결 URL
#   - REDIS_URL: Redis 연결 URL (선택사항)
#
# 🔗 연관 스크립트:
#   - setup-northwind.sh: 새로운 데이터베이스 설정
#   - db-helper.sh: 데이터베이스 컨테이너 관리
#   - dev-backend.sh: 백엔드 전용 개발 환경
#
# 💡 사용 시나리오:
#   - 개발 환경 빠른 시작 (기존 DB 활용)
#   - 전체 스택 통합 테스트
#   - 프로덕션 유사 환경 구성

echo "🚀 Starting Smart Business Analytics Assistant..."

# Function to parse database URL
parse_database_url() {
    local url="$1"
    if [[ $url =~ postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
        DB_USER="${BASH_REMATCH[1]}"
        DB_PASSWORD="${BASH_REMATCH[2]}"
        DB_HOST="${BASH_REMATCH[3]}"
        DB_PORT="${BASH_REMATCH[4]}"
        DB_NAME="${BASH_REMATCH[5]}"
    else
        echo "❌ Invalid DATABASE_URL format: $url"
        exit 1
    fi
}

parse_redis_url() {
    local url="$1"
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
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "📝 Please edit .env file with your Azure OpenAI credentials before continuing."
        echo "   Required: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_NAME"
    else
        echo "❌ .env.example file not found. Please create .env file manually."
    fi
    exit 1
fi

# Load environment variables
echo "📋 Loading environment variables from .env..."
set -a
source .env
set +a

# Check if required environment variables are set
echo "🔍 Validating environment configuration..."
if [ -z "$AZURE_OPENAI_ENDPOINT" ] || [ -z "$AZURE_OPENAI_API_KEY" ] || [ -z "$AZURE_OPENAI_DEPLOYMENT_NAME" ]; then
    echo "❌ Missing required Azure OpenAI configuration in .env file"
    echo "   Please set: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_NAME"
    exit 1
fi

# Parse database and redis URLs
if [ -n "$DATABASE_URL" ]; then
    parse_database_url "$DATABASE_URL"
else
    echo "❌ DATABASE_URL not found in .env file"
    exit 1
fi

if [ -n "$REDIS_URL" ]; then
    parse_redis_url "$REDIS_URL"
else
    echo "⚠️  REDIS_URL not found in .env, using defaults"
    REDIS_HOST="localhost"
    REDIS_PORT="6379"
fi

echo "✅ Environment configuration validated"
echo "📊 Configuration Summary:"
echo "   Database: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
echo "   Redis: $REDIS_HOST:$REDIS_PORT"

POSTGRES_CONTAINER_NAME="northwind-postgres"
REDIS_CONTAINER_NAME="redis-stack"

# Check if existing PostgreSQL container is running
echo ""
echo "🔍 Checking PostgreSQL availability..."
if docker ps --format "{{.Names}}" | grep -q "^${POSTGRES_CONTAINER_NAME}$"; then
    echo "✅ Found existing PostgreSQL container ($POSTGRES_CONTAINER_NAME)"
    
    # Test database connection
    echo "🔗 Testing PostgreSQL connection..."
    if docker exec $POSTGRES_CONTAINER_NAME pg_isready -h localhost -p 5432 -U $DB_USER > /dev/null 2>&1; then
        echo "✅ PostgreSQL is responding"
        
        # Check if northwind database exists
        if docker exec $POSTGRES_CONTAINER_NAME psql -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
            echo "✅ $DB_NAME database found"
        else
            echo "⚠️  $DB_NAME database not found. You may need to import the data."
            echo "   Run: docker exec -i $POSTGRES_CONTAINER_NAME psql -U $DB_USER < ./postgre/northwind.sql"
        fi
    else
        echo "❌ PostgreSQL container is not responding"
        exit 1
    fi
elif docker ps -a --format "{{.Names}}" | grep -q "^${POSTGRES_CONTAINER_NAME}$"; then
    echo "🔄 Found stopped PostgreSQL container ($POSTGRES_CONTAINER_NAME). Starting it..."
    docker start $POSTGRES_CONTAINER_NAME
    
    # Wait for PostgreSQL to be ready
    echo "⏳ Waiting for PostgreSQL to start..."
    for i in {1..30}; do
        if docker exec $POSTGRES_CONTAINER_NAME pg_isready -h localhost -p 5432 -U $DB_USER > /dev/null 2>&1; then
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
    if docker exec $POSTGRES_CONTAINER_NAME psql -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
        echo "✅ $DB_NAME database found"
    else
        echo "⚠️  $DB_NAME database not found. You may need to import the data."
        echo "   Run: docker exec -i $POSTGRES_CONTAINER_NAME psql -U $DB_USER < ./postgre/northwind.sql"
    fi
else
    echo "❌ PostgreSQL container '$POSTGRES_CONTAINER_NAME' not found"
    echo ""
    echo "🚀 Creating and starting new PostgreSQL container with Northwind data..."
    
    # Create and start PostgreSQL container with Northwind data
    docker run -d \
        --name $POSTGRES_CONTAINER_NAME \
        -e POSTGRES_DB=$DB_NAME \
        -e POSTGRES_USER=$DB_USER \
        -e POSTGRES_PASSWORD=$DB_PASSWORD \
        -p $DB_PORT:5432 \
        -v postgres_data:/var/lib/postgresql/data \
        postgres:15
    
    # Wait for PostgreSQL to be ready
    echo "⏳ Waiting for PostgreSQL to initialize..."
    for i in {1..60}; do
        if docker exec $POSTGRES_CONTAINER_NAME pg_isready -h localhost -p 5432 -U $DB_USER > /dev/null 2>&1; then
            echo "✅ PostgreSQL is running and ready"
            break
        fi
        sleep 2
        if [ $i -eq 60 ]; then
            echo "❌ PostgreSQL failed to initialize within 120 seconds"
            exit 1
        fi
    done
    
    # Load Northwind data if SQL file exists
    if [ -f "postgre/northwind.sql" ]; then
        echo "📥 Loading Northwind sample data..."
        docker cp postgre/northwind.sql $POSTGRES_CONTAINER_NAME:/northwind.sql
        docker exec $POSTGRES_CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -f /northwind.sql
        echo "✅ Northwind data loaded"
    else
        echo "⚠️  Northwind SQL file not found at postgre/northwind.sql"
        echo "   You may need to download it manually"
    fi
    
    echo "✅ New PostgreSQL container created with $DB_NAME database"
fi

# Check Redis
echo ""
echo "🔍 Checking Redis availability..."
if docker ps --format "{{.Names}}" | grep -q "^${REDIS_CONTAINER_NAME}$"; then
    echo "✅ Redis container '$REDIS_CONTAINER_NAME' is running"
    
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
    docker start $REDIS_CONTAINER_NAME
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
    
    # Create Redis container with settings from .env
    docker run -d \
        --name $REDIS_CONTAINER_NAME \
        -p $REDIS_PORT:6379 \
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

# Verify services are accessible from host
echo ""
echo "🔗 Final connectivity tests..."

# Test PostgreSQL from host
if command -v psql > /dev/null 2>&1; then
    if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
        echo "✅ PostgreSQL accessible from host"
    else
        echo "⚠️  PostgreSQL container running but not accessible from host"
    fi
else
    echo "ℹ️  psql not installed on host, skipping direct connection test"
fi

# Test Redis from host
if command -v redis-cli > /dev/null 2>&1; then
    if redis-cli -h $REDIS_HOST -p $REDIS_PORT ping > /dev/null 2>&1; then
        echo "✅ Redis accessible from host"
    else
        echo "⚠️  Redis container running but not accessible from host"
    fi
else
    echo "ℹ️  redis-cli not installed on host, skipping direct connection test"
fi

# Stop any existing text-to-sql containers (but keep the database)
echo ""
echo "🛑 Stopping existing text-to-sql containers..."
docker stop text-to-sql-backend text-to-sql-frontend 2>/dev/null || true
docker rm text-to-sql-backend text-to-sql-frontend 2>/dev/null || true

# Build and start services (excluding database)
echo "🔨 Building and starting backend and frontend services..."
if [ -f "docker-compose.yml" ]; then
    docker-compose up --build -d backend frontend
else
    echo "⚠️  docker-compose.yml not found. Skipping container orchestration."
    echo "   You may need to start services manually."
fi

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
echo "   Health Check: http://localhost:8000/health"
echo ""
echo "🗄️  Database Services:"
echo "   PostgreSQL: $DB_HOST:$DB_PORT (Database: $DB_NAME)"
echo "   Redis: $REDIS_HOST:$REDIS_PORT"
echo ""
echo "📋 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down (this will keep your database running)"
