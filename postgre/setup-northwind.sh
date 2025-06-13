#!/bin/bash
# setup-northwind.sh - Northwind PostgreSQL 컨테이너 설정
#
# 🎯 주요 기능:
# - .env 파일에서 DATABASE_URL을 파싱하여 PostgreSQL 설정 자동 구성
# - Northwind 샘플 데이터베이스가 포함된 PostgreSQL 컨테이너 생성
# - 기존 컨테이너 정리 후 새로운 컨테이너로 완전 재설정
# - Northwind SQL 데이터 자동 다운로드 및 적재
# - 데이터베이스 연결 및 데이터 검증 테스트
#
# 📋 사용법:
#   ./postgre/setup-northwind.sh
#
# 📦 생성되는 리소스:
#   - Docker 컨테이너: northwind-postgres
#   - Docker 볼륨: postgres_data (데이터 영속성)
#   - 데이터베이스: northwind (고객, 주문, 제품 등 샘플 데이터)
#
# ⚙️  환경 설정:
#   - .env 파일의 DATABASE_URL 사용 (postgresql://user:password@host:port/database)
#   - .env 파일이 없으면 기본값 사용 (postgres:password@localhost:5432/northwind)
#
# 🔗 연관 스크립트:
#   - dev-backend.sh: 백엔드 개발 환경 시작
#   - db-helper.sh: 데이터베이스 컨테이너 관리
#   - start-existing-db.sh: 전체 애플리케이션 스택 시작

echo "🐳 Northwind PostgreSQL 컨테이너 설정 시작..."

# Function to parse database URL
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
        echo "   Expected format: postgresql://user:password@host:port/database"
        exit 1
    fi
}

# Check if .env file exists and load it
if [ -f "../.env" ]; then
    echo "📋 Loading environment variables from .env..."
    set -a
    source ../.env
    set +a
    
    if [ -n "$DATABASE_URL" ]; then
        parse_database_url "$DATABASE_URL"
        echo "📊 Configuration from .env:"
        echo "   Database: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
    else
        echo "⚠️  DATABASE_URL not found in .env, using defaults"
        DB_USER="postgres"
        DB_PASSWORD="password"
        DB_HOST="localhost"
        DB_PORT="5432"
        DB_NAME="northwind"
    fi
else
    echo "⚠️  .env file not found, using default configuration"
    DB_USER="postgres"
    DB_PASSWORD="password"
    DB_HOST="localhost"
    DB_PORT="5432"
    DB_NAME="northwind"
fi

POSTGRES_CONTAINER_NAME="northwind-postgres"

# 기존 컨테이너 정리
echo "🧹 Cleaning up existing containers..."
if docker ps --format "{{.Names}}" | grep -q "^${POSTGRES_CONTAINER_NAME}$"; then
    echo "🛑 Stopping existing PostgreSQL container..."
    docker stop $POSTGRES_CONTAINER_NAME
fi

if docker ps -a --format "{{.Names}}" | grep -q "^${POSTGRES_CONTAINER_NAME}$"; then
    echo "🗑️  Removing existing PostgreSQL container..."
    docker rm $POSTGRES_CONTAINER_NAME
fi

# 컨테이너 실행
echo "📦 Creating PostgreSQL container with configuration:"
echo "   Container: $POSTGRES_CONTAINER_NAME"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo "   Port: $DB_PORT"

docker run -d \
    --name $POSTGRES_CONTAINER_NAME \
    -e POSTGRES_DB=$DB_NAME \
    -e POSTGRES_USER=$DB_USER \
    -e POSTGRES_PASSWORD=$DB_PASSWORD \
    -p $DB_PORT:5432 \
    -v postgres_data:/var/lib/postgresql/data \
    postgres:15

# 컨테이너 시작 대기
echo "⏳ Waiting for PostgreSQL to initialize..."
sleep 15

# Wait for PostgreSQL to be ready
echo "🔗 Waiting for PostgreSQL to accept connections..."
for i in {1..60}; do
    if docker exec $POSTGRES_CONTAINER_NAME pg_isready -h localhost -p 5432 -U $DB_USER > /dev/null 2>&1; then
        echo "✅ PostgreSQL is ready"
        break
    fi
    echo "   Attempt $i/60: PostgreSQL not ready yet..."
    sleep 2
    if [ $i -eq 60 ]; then
        echo "❌ PostgreSQL failed to start within 120 seconds"
        exit 1
    fi
done

# Northwind 데이터 다운로드
echo "📥 Downloading Northwind sample data..."
if [ ! -f "northwind.sql" ]; then
    curl -s -o northwind.sql https://raw.githubusercontent.com/pthom/northwind_psql/master/northwind.sql
    if [ $? -eq 0 ]; then
        echo "✅ Northwind SQL file downloaded"
    else
        echo "❌ Failed to download Northwind SQL file"
        exit 1
    fi
else
    echo "✅ Northwind SQL file already exists"
fi

# 데이터 적재
echo "🔄 Loading Northwind data into database..."
docker cp northwind.sql $POSTGRES_CONTAINER_NAME:/northwind.sql
if docker exec $POSTGRES_CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -f /northwind.sql > /dev/null 2>&1; then
    echo "✅ Northwind data loaded successfully"
else
    echo "❌ Failed to load Northwind data"
    exit 1
fi

# 확인
echo "🔍 Verifying database setup..."
CUSTOMER_COUNT=$(docker exec $POSTGRES_CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM customers;" 2>/dev/null | tr -d ' ')

if [ -n "$CUSTOMER_COUNT" ] && [ "$CUSTOMER_COUNT" -gt 0 ]; then
    echo "✅ Database verification successful!"
    echo "   Found $CUSTOMER_COUNT customers in the database"
else
    echo "❌ Database verification failed"
    exit 1
fi

# Test connection from host (if psql is available)
echo "🔗 Testing connection from host..."
if command -v psql > /dev/null 2>&1; then
    if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
        echo "✅ Host connection test successful"
    else
        echo "⚠️  PostgreSQL container running but not accessible from host"
    fi
else
    echo "ℹ️  psql not installed on host, skipping direct connection test"
fi

# Cleanup
rm -f northwind.sql

echo ""
echo "🎉 Northwind 데이터베이스 준비 완료!"
echo ""
echo "📊 Connection Information:"
echo "   Host: $DB_HOST"
echo "   Port: $DB_PORT"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo "   Password: $DB_PASSWORD"
echo ""
echo "🔗 Connection URL: postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "💡 You can now start the backend with: ./dev-backend.sh"