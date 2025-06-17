#!/bin/bash

# Backend Development Script
# Run FastAPI backend in development mode with proper service management
#
# 🎯 주요 기능:
# - Text-to-SQL 백엔드 개발 환경 전용 시작 스크립트
# - .env 파일 기반 환경 설정 자동 검증 및 파싱
# - PostgreSQL 및 Redis 서비스 의존성 자동 관리
# - Python 가상환경 및 의존성 패키지 자동 설정
# - FastAPI 개발 서버 핫 리로드 모드로 실행
# - 전체 백엔드 스택 헬스체크 및 연결 테스트
#
# 📋 사용법:
#   ./dev-backend.sh
#
# 🔧 수행 작업:
#   1. .env 파일 존재 및 필수 환경변수 검증
#   2. DATABASE_URL, REDIS_URL 파싱 및 연결 설정 추출
#   3. PostgreSQL 컨테이너 상태 확인 및 자동 시작/생성
#   4. Redis 컨테이너 상태 확인 및 자동 시작/생성
#   5. 호스트에서 데이터베이스 서비스 접근성 테스트
#   6. Python 가상환경 활성화 및 의존성 설치
#   7. 백엔드 환경 설정 검증 (config.py 실행)
#   8. FastAPI 개발 서버 시작 (uvicorn --reload)
#
# 📦 관리 대상:
#   - PostgreSQL: northwind-postgres (메인 데이터베이스)
#   - Redis: redis-stack (캐시 및 세션 스토어)
#   - Python 가상환경: venv (백엔드 의존성)
#   - FastAPI 서버: localhost:8000 (개발 서버)
#
# ⚙️  필수 환경 설정:
#   - AZURE_OPENAI_ENDPOINT: Azure OpenAI 서비스 엔드포인트
#   - AZURE_OPENAI_API_KEY: Azure OpenAI API 키
#   - AZURE_OPENAI_DEPLOYMENT_NAME: 배포된 모델 이름
#   - DATABASE_URL: PostgreSQL 연결 URL (postgresql://user:pass@host:port/db)
#   - REDIS_URL: Redis 연결 URL (redis://host:port)
#   - SECRET_KEY: JWT 토큰 암호화 키
#   - REFRESH_TOKEN_EXPIRE_DAYS: 리프레시 토큰 만료 기간
#
# 🔗 연관 스크립트:
#   - setup-northwind.sh: PostgreSQL 초기 데이터 설정
#   - db-helper.sh: 데이터베이스 컨테이너 관리
#   - start-app.sh: 전체 애플리케이션 스택
#
# 💡 개발 워크플로우:
#   1. 최초 실행: 모든 서비스 자동 설정 및 시작
#   2. 일반 실행: 기존 서비스 상태 확인 후 백엔드만 재시작
#   3. 코드 변경: 핫 리로드로 자동 반영
#   4. 디버깅: 상세한 로그 및 상태 정보 제공
#
# 🚨 주의사항:
#   - 첫 실행 시 Docker 이미지 다운로드로 시간 소요
#   - PostgreSQL 초기화 시 Northwind 데이터 자동 로드
#   - 포트 충돌 시 기존 서비스 확인 필요 (8000, 5432, 6379)

echo "🐍 Starting Backend Development Server..."

# Function to parse URL and extract components
parse_database_url() {
    local url="$1"
    # Extract components from postgresql://user:password@host:port/database
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
    exit 1
fi

if [ -z "$REDIS_URL" ]; then
    echo "❌ REDIS_URL not found in .env file"
    exit 1
fi

echo "✅ Environment configuration validated"

# Parse database and redis URLs
parse_database_url "$DATABASE_URL"
parse_redis_url "$REDIS_URL"

echo "📊 Configuration Summary:"
echo "   Database: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
echo "   Redis: $REDIS_HOST:$REDIS_PORT"

# Check if PostgreSQL is running
echo ""
echo "🔍 Checking PostgreSQL availability..."
POSTGRES_CONTAINER_NAME="northwind-postgres"

# Check if PostgreSQL container exists and is running
if docker ps --format "{{.Names}}" | grep -q "^${POSTGRES_CONTAINER_NAME}$"; then
    echo "✅ PostgreSQL container '${POSTGRES_CONTAINER_NAME}' is running"
    
    # Test actual connection
    echo "🔗 Testing PostgreSQL connection..."
    if docker exec $POSTGRES_CONTAINER_NAME pg_isready -h localhost -p 5432 -U postgres > /dev/null 2>&1; then
        echo "✅ PostgreSQL connection test successful"
        
        # Check if Northwind database needs initialization
        echo "🗄️  Checking if Northwind database needs initialization..."
        
        # Check if Northwind tables exist (checking for customers table as indicator)
        echo "🔍 Checking if Northwind data already exists..."
        TABLE_COUNT=$(docker exec $POSTGRES_CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customers';" 2>/dev/null | tr -d ' \n' || echo "0")
        
        if [ "$TABLE_COUNT" -gt 0 ]; then
            echo "✅ Northwind database already initialized (found existing tables)"
        else
            echo "📥 Northwind database not found, initializing with sample data..."
            if [ -f "../postgre/northwind.sql" ]; then
                echo "📂 Loading Northwind data from ../postgre/northwind.sql..."
                docker exec -i $POSTGRES_CONTAINER_NAME psql -U $DB_USER -d $DB_NAME < ../postgre/northwind.sql
                echo "✅ Northwind data loaded successfully"
            else
                echo "⚠️  Northwind SQL file not found at ../postgre/northwind.sql"
                echo "   Please ensure the file exists at /home/wjadmin/Dev/text-to-sql/postgre/northwind.sql"
            fi
        fi
    else
        echo "⚠️  PostgreSQL container is running but not ready. Waiting..."
        sleep 5
    fi
    
elif docker ps -a --format "{{.Names}}" | grep -q "^${POSTGRES_CONTAINER_NAME}$"; then
    echo "🔄 Found stopped PostgreSQL container. Starting it..."
    docker start ${POSTGRES_CONTAINER_NAME}
    echo "⏳ Waiting for PostgreSQL to initialize..."
    sleep 10
    
    # Wait for PostgreSQL to be ready
    echo "🔗 Waiting for PostgreSQL to accept connections..."
    for i in {1..30}; do
        if docker exec $POSTGRES_CONTAINER_NAME pg_isready -h localhost -p 5432 -U postgres > /dev/null 2>&1; then
            echo "✅ PostgreSQL is ready"
            break
        fi
        echo "   Attempt $i/30: PostgreSQL not ready yet..."
        sleep 2
    done
    
    # Check if Northwind database needs initialization
    echo "🗄️  Checking if Northwind database needs initialization..."
    
    # Check if Northwind tables exist (checking for customers table as indicator)
    echo "🔍 Checking if Northwind data already exists..."
    TABLE_COUNT=$(docker exec $POSTGRES_CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customers';" 2>/dev/null | tr -d ' \n' || echo "0")
    
    if [ "$TABLE_COUNT" -gt 0 ]; then
        echo "✅ Northwind database already initialized (found existing tables)"
    else
        echo "📥 Northwind database not found, initializing with sample data..."
        if [ -f "../postgre/northwind.sql" ]; then
            echo "📂 Loading Northwind data from ../postgre/northwind.sql..."
            docker exec -i $POSTGRES_CONTAINER_NAME psql -U $DB_USER -d $DB_NAME < ../postgre/northwind.sql
            echo "✅ Northwind data loaded successfully"
        else
            echo "⚠️  Northwind SQL file not found at ../postgre/northwind.sql"
            echo "   Please ensure the file exists at /home/wjadmin/Dev/text-to-sql/postgre/northwind.sql"
        fi
    fi
    
else
    echo "🚀 PostgreSQL container not found. Creating and starting a new one..."
    
    # Create PostgreSQL container with settings from .env
    docker run -d \
        --name ${POSTGRES_CONTAINER_NAME} \
        -e POSTGRES_USER=${DB_USER} \
        -e POSTGRES_PASSWORD=${DB_PASSWORD} \
        -e POSTGRES_DB=${DB_NAME} \
        -p ${DB_PORT}:5432 \
        -v postgres_data:/var/lib/postgresql/data \
        postgres:15
    
    echo "⏳ Waiting for PostgreSQL to initialize..."
    sleep 15
    
    # Wait for PostgreSQL to be ready
    echo "🔗 Waiting for PostgreSQL to accept connections..."
    for i in {1..60}; do
        if docker exec $POSTGRES_CONTAINER_NAME pg_isready -h localhost -p 5432 -U postgres > /dev/null 2>&1; then
            echo "✅ PostgreSQL is ready"
            break
        fi
        echo "   Attempt $i/60: PostgreSQL not ready yet..."
        sleep 2
    done
    
    # Initialize Northwind database if needed
    echo "🗄️  Checking if Northwind database needs initialization..."
    
    # Check if Northwind tables exist (checking for customers table as indicator)
    echo "🔍 Checking if Northwind data already exists..."
    TABLE_COUNT=$(docker exec $POSTGRES_CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customers';" 2>/dev/null | tr -d ' \n' || echo "0")
    
    if [ "$TABLE_COUNT" -gt 0 ]; then
        echo "✅ Northwind database already initialized (found existing tables)"
    else
        echo "📥 Northwind database not found, initializing with sample data..."
        if [ -f "../postgre/northwind.sql" ]; then
            echo "� Loading Northwind data from ../postgre/northwind.sql..."
            docker exec -i $POSTGRES_CONTAINER_NAME psql -U $DB_USER -d $DB_NAME < ../postgre/northwind.sql
            echo "✅ Northwind data loaded successfully"
        else
            echo "⚠️  Northwind SQL file not found at ../postgre/northwind.sql"
            echo "   Please ensure the file exists at /home/wjadmin/Dev/text-to-sql/postgre/northwind.sql"
        fi
    fi
fi

# Check if Redis is running
echo ""
echo "🔍 Checking Redis availability..."
REDIS_CONTAINER_NAME="redis-stack"

if docker ps --format "{{.Names}}" | grep -q "^${REDIS_CONTAINER_NAME}$"; then
    echo "✅ Redis container '${REDIS_CONTAINER_NAME}' is running"
    
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
    
    # Create Redis container with settings from .env
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

echo ""
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
echo "🗄️  Database Services:"
echo "   PostgreSQL: $DB_HOST:$DB_PORT (Database: $DB_NAME)"
echo "   Redis: $REDIS_HOST:$REDIS_PORT"
echo ""
echo "💡 Press Ctrl+C to stop the server"
echo ""

# Start the development server with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
