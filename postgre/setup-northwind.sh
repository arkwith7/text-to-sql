#!/bin/bash
# setup-northwind.sh - 안정적인 Northwind PostgreSQL 컨테이너 설정
#
# 🎯 주요 개선 사항:
# - 기존 데이터 검증 후 재사용 (불필요한 재생성 방지)
# - 볼륨 데이터 무결성 검증
# - 실패 시 자동 복구 및 재시도
# - 상세한 진단 정보 제공
#
# 📋 사용법:
#   ./postgre/setup-northwind.sh [--force-recreate]
#
# 🔧 옵션:
#   --force-recreate: 기존 컨테이너와 볼륨을 강제로 삭제하고 새로 생성

set -e  # 오류 발생 시 스크립트 중단

FORCE_RECREATE=false
if [[ "$1" == "--force-recreate" ]]; then
    FORCE_RECREATE=true
    echo "🔄 Force recreate mode enabled"
fi

echo "🐳 Northwind PostgreSQL 컨테이너 설정 시작..."

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
POSTGRES_VOLUME_NAME="postgres_northwind_data"

# Function to check if database has data
check_database_data() {
    local container_name=$1
    echo "🔍 Checking if database has Northwind data..."
    
    if ! docker ps --format "{{.Names}}" | grep -q "^${container_name}$"; then
        echo "   Container not running"
        return 1
    fi
    
    # Check if northwind database exists and has data
    local customer_count=$(docker exec $container_name psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM customers;" 2>/dev/null | tr -d ' ' || echo "0")
    
    if [ -n "$customer_count" ] && [ "$customer_count" -gt 0 ]; then
        echo "✅ Database has $customer_count customers - data is present"
        return 0
    else
        echo "❌ Database is empty or northwind data is missing"
        return 1
    fi
}

# Function to wait for PostgreSQL
wait_for_postgres() {
    local container_name=$1
    echo "⏳ Waiting for PostgreSQL to be ready..."
    
    for i in {1..60}; do
        if docker exec $container_name pg_isready -h localhost -p 5432 -U $DB_USER > /dev/null 2>&1; then
            echo "✅ PostgreSQL is ready"
            return 0
        fi
        echo "   Attempt $i/60: PostgreSQL not ready yet..."
        sleep 2
    done
    
    echo "❌ PostgreSQL failed to start within 120 seconds"
    return 1
}

# Function to load northwind data
load_northwind_data() {
    local container_name=$1
    
    echo "📥 Preparing Northwind sample data..."
    
    # Download northwind.sql if not exists
    if [ ! -f "northwind.sql" ]; then
        echo "   Downloading Northwind SQL file..."
        if curl -s -o northwind.sql https://raw.githubusercontent.com/pthom/northwind_psql/master/northwind.sql; then
            echo "✅ Northwind SQL file downloaded"
        else
            echo "❌ Failed to download Northwind SQL file"
            return 1
        fi
    else
        echo "✅ Northwind SQL file already exists"
    fi
    
    echo "🔄 Loading Northwind data into database..."
    
    # Copy SQL file to container
    if ! docker cp northwind.sql $container_name:/northwind.sql; then
        echo "❌ Failed to copy SQL file to container"
        return 1
    fi
    
    # Load data with detailed error reporting
    if docker exec $container_name psql -U $DB_USER -d $DB_NAME -f /northwind.sql; then
        echo "✅ Northwind data loaded successfully"
        
        # Verify data was loaded
        local customer_count=$(docker exec $container_name psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM customers;" 2>/dev/null | tr -d ' ')
        if [ -n "$customer_count" ] && [ "$customer_count" -gt 0 ]; then
            echo "✅ Data verification successful - Found $customer_count customers"
            return 0
        else
            echo "❌ Data verification failed - Tables might be empty"
            return 1
        fi
    else
        echo "❌ Failed to load Northwind data"
        return 1
    fi
}

# Main setup logic
setup_postgres_container() {
    
    # Check if container exists and is running with data
    if ! $FORCE_RECREATE && docker ps --format "{{.Names}}" | grep -q "^${POSTGRES_CONTAINER_NAME}$"; then
        echo "📦 Container $POSTGRES_CONTAINER_NAME is running, checking data..."
        
        if check_database_data $POSTGRES_CONTAINER_NAME; then
            echo "🎉 Existing container has valid data - no recreation needed!"
            return 0
        else
            echo "⚠️  Container exists but data is missing, will reload data..."
            if wait_for_postgres $POSTGRES_CONTAINER_NAME && load_northwind_data $POSTGRES_CONTAINER_NAME; then
                echo "🎉 Data reloaded successfully!"
                return 0
            else
                echo "❌ Failed to reload data, will recreate container..."
            fi
        fi
    fi
    
    # Check if stopped container exists
    if docker ps -a --format "{{.Names}}" | grep -q "^${POSTGRES_CONTAINER_NAME}$"; then
        echo "🗑️  Removing existing container..."
        docker stop $POSTGRES_CONTAINER_NAME 2>/dev/null || true
        docker rm $POSTGRES_CONTAINER_NAME 2>/dev/null || true
    fi
    
    # Remove volume if force recreate
    if $FORCE_RECREATE; then
        echo "🗑️  Removing existing volume..."
        docker volume rm $POSTGRES_VOLUME_NAME 2>/dev/null || true
    fi
    
    # Create volume if not exists
    if ! docker volume ls --format "{{.Name}}" | grep -q "^${POSTGRES_VOLUME_NAME}$"; then
        echo "📂 Creating PostgreSQL volume..."
        docker volume create $POSTGRES_VOLUME_NAME
    fi
    
    # Check if port is available
    if lsof -Pi :$DB_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ Port $DB_PORT is already in use"
        echo "   Please stop the service using this port or change the port in .env"
        exit 1
    fi
    
    echo "🚀 Creating PostgreSQL container..."
    echo "   Container: $POSTGRES_CONTAINER_NAME"
    echo "   Database: $DB_NAME"
    echo "   User: $DB_USER"
    echo "   Port: $DB_PORT"
    echo "   Volume: $POSTGRES_VOLUME_NAME"
    
    # Create and start container
    docker run -d \
        --name $POSTGRES_CONTAINER_NAME \
        -e POSTGRES_DB=$DB_NAME \
        -e POSTGRES_USER=$DB_USER \
        -e POSTGRES_PASSWORD=$DB_PASSWORD \
        -e POSTGRES_INITDB_ARGS="--encoding=UTF8 --locale=C" \
        -p $DB_PORT:5432 \
        -v $POSTGRES_VOLUME_NAME:/var/lib/postgresql/data \
        --restart unless-stopped \
        postgres:15
    
    # Wait for PostgreSQL to be ready
    if ! wait_for_postgres $POSTGRES_CONTAINER_NAME; then
        echo "❌ PostgreSQL failed to start"
        docker logs $POSTGRES_CONTAINER_NAME --tail 20
        exit 1
    fi
    
    # Load Northwind data
    if ! load_northwind_data $POSTGRES_CONTAINER_NAME; then
        echo "❌ Failed to load Northwind data"
        docker logs $POSTGRES_CONTAINER_NAME --tail 20
        exit 1
    fi
    
    echo "🎉 PostgreSQL container setup completed successfully!"
}

# Test connection from host
test_host_connection() {
    echo "🔗 Testing connection from host..."
    
    if command -v psql > /dev/null 2>&1; then
        if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT version();" > /dev/null 2>&1; then
            echo "✅ Host connection test successful"
        else
            echo "⚠️  PostgreSQL container running but not accessible from host"
            echo "   This might be normal if psql client version is incompatible"
        fi
    else
        echo "ℹ️  psql not installed on host, skipping direct connection test"
    fi
}

# Main execution
main() {
    setup_postgres_container
    test_host_connection
    
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
    echo "   Volume: $POSTGRES_VOLUME_NAME"
    echo ""
    echo "🔗 Connection URL: postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
    echo ""
    echo "🛠️  Management Commands:"
    echo "   Check status: docker ps | grep $POSTGRES_CONTAINER_NAME"
    echo "   View logs: docker logs $POSTGRES_CONTAINER_NAME"
    echo "   Connect: docker exec -it $POSTGRES_CONTAINER_NAME psql -U $DB_USER -d $DB_NAME"
    echo "   Stop: docker stop $POSTGRES_CONTAINER_NAME"
    echo "   Force recreate: $0 --force-recreate"
    echo ""
    echo "💡 You can now start the backend with: ./backend/dev-backend.sh"
}

# Run main function
main "$@"
