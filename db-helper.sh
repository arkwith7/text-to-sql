#!/bin/bash

# Database & Cache Management Helper Script
# Enhanced with .env configuration support
#
# 🎯 주요 기능:
# - PostgreSQL 및 Redis 컨테이너의 통합 관리 도구
# - .env 파일에서 DATABASE_URL과 REDIS_URL을 자동 파싱
# - 컨테이너 상태 모니터링 및 연결 테스트
# - 컨테이너 생성, 시작, 중지, 삭제 등 전체 라이프사이클 관리
# - 실시간 로그 확인 및 문제 진단 지원
#
# 📋 사용법:
#   ./db-helper.sh [command] [container]
#
# 🔧 지원 명령어:
#   status              - 모든 컨테이너 상태 확인 (기본값)
#   start [container]   - 컨테이너 시작 [all|postgres|redis]
#   stop [container]    - 컨테이너 중지 [all|postgres|redis]
#   create [container]  - 새 컨테이너 생성 [all|postgres|redis]
#   remove [container]  - 컨테이너 삭제 [all|postgres|redis]
#   logs [container]    - 컨테이너 로그 확인 [postgres|redis]
#   test                - 서비스 연결 테스트
#   help                - 도움말 표시
#
# 📦 관리 대상:
#   - PostgreSQL 컨테이너: northwind-postgres
#   - Redis 컨테이너: redis-stack
#   - 각 컨테이너의 데이터 볼륨 및 네트워크 설정
#
# ⚙️  환경 설정:
#   - .env 파일의 DATABASE_URL 및 REDIS_URL 자동 파싱
#   - 설정이 없으면 기본값으로 fallback
#   - 실시간 연결 상태 및 헬스체크 제공
#
# 🔗 연관 스크립트:
#   - setup-northwind.sh: PostgreSQL 초기 설정
#   - dev-backend.sh: 백엔드 개발 환경
#   - start-existing-db.sh: 전체 애플리케이션 스택

echo "🗄️ PostgreSQL & Redis Container Management"
echo ""

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

# Load configuration from .env if available
load_config() {
    if [ -f ".env" ]; then
        set -a
        source .env
        set +a
        
        if [ -n "$DATABASE_URL" ]; then
            parse_database_url "$DATABASE_URL"
        else
            DB_USER="postgres"
            DB_PASSWORD="password"
            DB_HOST="localhost"
            DB_PORT="5432"
            DB_NAME="northwind"
        fi
        
        if [ -n "$REDIS_URL" ]; then
            parse_redis_url "$REDIS_URL"
        else
            REDIS_HOST="localhost"
            REDIS_PORT="6379"
        fi
    else
        # Default values
        DB_USER="postgres"
        DB_PASSWORD="password"
        DB_HOST="localhost"
        DB_PORT="5432"
        DB_NAME="northwind"
        REDIS_HOST="localhost"
        REDIS_PORT="6379"
    fi
    
    POSTGRES_CONTAINER_NAME="northwind-postgres"
    REDIS_CONTAINER_NAME="redis-stack"
}

show_status() {
    load_config
    
    echo "📊 Container Status:"
    echo ""
    
    # Check PostgreSQL
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$POSTGRES_CONTAINER_NAME"; then
        echo "✅ PostgreSQL ($POSTGRES_CONTAINER_NAME) is RUNNING"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep $POSTGRES_CONTAINER_NAME
        
        # Test connection
        if docker exec $POSTGRES_CONTAINER_NAME pg_isready -h localhost -p 5432 -U $DB_USER > /dev/null 2>&1; then
            echo "   🔗 Connection test: ✅ HEALTHY"
        else
            echo "   🔗 Connection test: ❌ NOT RESPONDING"
        fi
    elif docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -q "$POSTGRES_CONTAINER_NAME"; then
        echo "🛑 PostgreSQL ($POSTGRES_CONTAINER_NAME) is STOPPED"
        docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep $POSTGRES_CONTAINER_NAME
    else
        echo "❌ PostgreSQL ($POSTGRES_CONTAINER_NAME) container NOT FOUND"
    fi
    
    echo ""
    
    # Check Redis
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$REDIS_CONTAINER_NAME"; then
        echo "✅ Redis ($REDIS_CONTAINER_NAME) is RUNNING"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep $REDIS_CONTAINER_NAME
        
        # Test connection
        if docker exec $REDIS_CONTAINER_NAME redis-cli ping > /dev/null 2>&1; then
            echo "   🔗 Connection test: ✅ HEALTHY"
        else
            echo "   🔗 Connection test: ❌ NOT RESPONDING"
        fi
    elif docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -q "$REDIS_CONTAINER_NAME"; then
        echo "🛑 Redis ($REDIS_CONTAINER_NAME) is STOPPED"
        docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep $REDIS_CONTAINER_NAME
    else
        echo "❌ Redis ($REDIS_CONTAINER_NAME) container NOT FOUND"
    fi
    echo ""
    
    # Show configuration
    echo "📋 Configuration (from .env):"
    echo "   PostgreSQL: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
    echo "   Redis: $REDIS_HOST:$REDIS_PORT"
    echo ""
}

case "$1" in
    "status"|"")
        show_status
        ;;
    "start")
        load_config
        container_name="${2:-all}"
        
        if [ "$container_name" = "all" ] || [ "$container_name" = "postgres" ]; then
            if docker ps --format "table {{.Names}}" | grep -q "$POSTGRES_CONTAINER_NAME"; then
                echo "✅ PostgreSQL is already running"
            elif docker ps -a --format "table {{.Names}}" | grep -q "$POSTGRES_CONTAINER_NAME"; then
                echo "🔄 Starting PostgreSQL ($POSTGRES_CONTAINER_NAME)..."
                docker start $POSTGRES_CONTAINER_NAME
                
                # Wait for PostgreSQL to be ready
                echo "⏳ Waiting for PostgreSQL to be ready..."
                for i in {1..30}; do
                    if docker exec $POSTGRES_CONTAINER_NAME pg_isready -h localhost -p 5432 -U $DB_USER > /dev/null 2>&1; then
                        echo "✅ PostgreSQL is ready"
                        break
                    fi
                    sleep 1
                done
            else
                echo "❌ PostgreSQL container not found. Use './db-helper.sh create postgres' to create it."
            fi
        fi
        
        if [ "$container_name" = "all" ] || [ "$container_name" = "redis" ]; then
            if docker ps --format "table {{.Names}}" | grep -q "$REDIS_CONTAINER_NAME"; then
                echo "✅ Redis is already running"
            elif docker ps -a --format "table {{.Names}}" | grep -q "$REDIS_CONTAINER_NAME"; then
                echo "🔄 Starting Redis ($REDIS_CONTAINER_NAME)..."
                docker start $REDIS_CONTAINER_NAME
                
                # Wait for Redis to be ready
                echo "⏳ Waiting for Redis to be ready..."
                for i in {1..10}; do
                    if docker exec $REDIS_CONTAINER_NAME redis-cli ping > /dev/null 2>&1; then
                        echo "✅ Redis is ready"
                        break
                    fi
                    sleep 1
                done
            else
                echo "❌ Redis container not found. Use './db-helper.sh create redis' to create it."
            fi
        fi
        ;;
    "stop")
        load_config
        container_name="${2:-all}"
        
        if [ "$container_name" = "all" ] || [ "$container_name" = "postgres" ]; then
            if docker ps --format "table {{.Names}}" | grep -q "$POSTGRES_CONTAINER_NAME"; then
                echo "🛑 Stopping PostgreSQL ($POSTGRES_CONTAINER_NAME)..."
                docker stop $POSTGRES_CONTAINER_NAME
                echo "✅ PostgreSQL Stopped"
            else
                echo "⚠️  PostgreSQL is not running"
            fi
        fi
        
        if [ "$container_name" = "all" ] || [ "$container_name" = "redis" ]; then
            if docker ps --format "table {{.Names}}" | grep -q "$REDIS_CONTAINER_NAME"; then
                echo "🛑 Stopping Redis ($REDIS_CONTAINER_NAME)..."
                docker stop $REDIS_CONTAINER_NAME
                echo "✅ Redis Stopped"
            else
                echo "⚠️  Redis is not running"
            fi
        fi
        ;;
    "create")
        load_config
        container_name="${2:-all}"
        
        if [ "$container_name" = "all" ] || [ "$container_name" = "postgres" ]; then
            if docker ps -a --format "table {{.Names}}" | grep -q "$POSTGRES_CONTAINER_NAME"; then
                echo "⚠️  PostgreSQL container already exists"
            else
                echo "🚀 Creating new PostgreSQL container ($POSTGRES_CONTAINER_NAME)..."
                echo "   Using configuration: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
                
                docker run -d \
                    --name $POSTGRES_CONTAINER_NAME \
                    -e POSTGRES_DB=$DB_NAME \
                    -e POSTGRES_USER=$DB_USER \
                    -e POSTGRES_PASSWORD=$DB_PASSWORD \
                    -p $DB_PORT:5432 \
                    -v postgres_data:/var/lib/postgresql/data \
                    postgres:15
                    
                echo "⏳ Waiting for PostgreSQL to initialize..."
                sleep 15

                # Wait for PostgreSQL to be ready
                for i in {1..60}; do
                    if docker exec $POSTGRES_CONTAINER_NAME pg_isready -h localhost -p 5432 -U $DB_USER > /dev/null 2>&1; then
                        echo "✅ PostgreSQL is ready"
                        break
                    fi
                    sleep 2
                done

                echo "📥 Downloading Northwind SQL dump..."
                curl -s -o northwind.sql https://raw.githubusercontent.com/pthom/northwind_psql/master/northwind.sql

                echo "🔄 Importing data into Northwind database..."
                docker cp northwind.sql $POSTGRES_CONTAINER_NAME:/northwind.sql
                docker exec $POSTGRES_CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -f /northwind.sql
                rm northwind.sql

                echo "✅ Northwind database ready ($DB_HOST:$DB_PORT, DB: $DB_NAME, User: $DB_USER)"
            fi
        fi
        
        if [ "$container_name" = "all" ] || [ "$container_name" = "redis" ]; then
            if docker ps -a --format "table {{.Names}}" | grep -q "$REDIS_CONTAINER_NAME"; then
                echo "⚠️  Redis container already exists"
            else
                echo "🚀 Creating new Redis container ($REDIS_CONTAINER_NAME)..."
                echo "   Using configuration: $REDIS_HOST:$REDIS_PORT"
                
                docker run -d \
                    --name $REDIS_CONTAINER_NAME \
                    -p $REDIS_PORT:6379 \
                    -p 8001:8001 \
                    redis/redis-stack:latest
                    
                echo "⏳ Waiting for Redis to initialize..."
                sleep 10
                
                # Wait for Redis to be ready
                for i in {1..20}; do
                    if docker exec $REDIS_CONTAINER_NAME redis-cli ping > /dev/null 2>&1; then
                        echo "✅ Redis is ready"
                        break
                    fi
                    sleep 1
                done
            fi
        fi
        show_status
        ;;
    "remove")
        load_config
        container_name="${2:-all}"
        
        if [ "$container_name" = "all" ] || [ "$container_name" = "postgres" ]; then
            if docker ps --format "table {{.Names}}" | grep -q "$POSTGRES_CONTAINER_NAME"; then
                echo "🛑 Stopping PostgreSQL ($POSTGRES_CONTAINER_NAME)..."
                docker stop $POSTGRES_CONTAINER_NAME
            fi
            if docker ps -a --format "table {{.Names}}" | grep -q "$POSTGRES_CONTAINER_NAME"; then
                echo "🗑️  Removing PostgreSQL container..."
                docker rm $POSTGRES_CONTAINER_NAME
                echo "✅ PostgreSQL container removed"
            else
                echo "⚠️  PostgreSQL container not found"
            fi
        fi
        
        if [ "$container_name" = "all" ] || [ "$container_name" = "redis" ]; then
            if docker ps --format "table {{.Names}}" | grep -q "$REDIS_CONTAINER_NAME"; then
                echo "🛑 Stopping Redis ($REDIS_CONTAINER_NAME)..."
                docker stop $REDIS_CONTAINER_NAME
            fi
            if docker ps -a --format "table {{.Names}}" | grep -q "$REDIS_CONTAINER_NAME"; then
                echo "🗑️  Removing Redis container..."
                docker rm $REDIS_CONTAINER_NAME
                echo "✅ Redis container removed"
            else
                echo "⚠️  Redis container not found"
            fi
        fi
        ;;
    "logs")
        load_config
        container_name="${2:-postgres}"
        
        if [ "$container_name" = "postgres" ]; then
            if docker ps -a --format "table {{.Names}}" | grep -q "$POSTGRES_CONTAINER_NAME"; then
                echo "📋 PostgreSQL logs:"
                docker logs $POSTGRES_CONTAINER_NAME
            else
                echo "❌ PostgreSQL container not found"
            fi
        elif [ "$container_name" = "redis" ]; then
            if docker ps -a --format "table {{.Names}}" | grep -q "$REDIS_CONTAINER_NAME"; then
                echo "📋 Redis logs:"
                docker logs $REDIS_CONTAINER_NAME
            else
                echo "❌ Redis container not found"
            fi
        fi
        ;;
    "test")
        load_config
        echo "🔍 Testing service connections..."
        echo ""
        
        # Test PostgreSQL
        if docker ps --format "{{.Names}}" | grep -q "$POSTGRES_CONTAINER_NAME"; then
            if docker exec $POSTGRES_CONTAINER_NAME pg_isready -h localhost -p 5432 -U $DB_USER > /dev/null 2>&1; then
                echo "✅ PostgreSQL connection test successful"
                
                # Test from host if psql is available
                if command -v psql > /dev/null 2>&1; then
                    if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
                        echo "✅ PostgreSQL accessible from host"
                    else
                        echo "⚠️  PostgreSQL container running but not accessible from host"
                    fi
                fi
            else
                echo "❌ PostgreSQL connection test failed"
            fi
        else
            echo "❌ PostgreSQL container not running"
        fi
        
        # Test Redis
        if docker ps --format "{{.Names}}" | grep -q "$REDIS_CONTAINER_NAME"; then
            if docker exec $REDIS_CONTAINER_NAME redis-cli ping > /dev/null 2>&1; then
                echo "✅ Redis connection test successful"
                
                # Test from host if redis-cli is available
                if command -v redis-cli > /dev/null 2>&1; then
                    if redis-cli -h $REDIS_HOST -p $REDIS_PORT ping > /dev/null 2>&1; then
                        echo "✅ Redis accessible from host"
                    else
                        echo "⚠️  Redis container running but not accessible from host"
                    fi
                fi
            else
                echo "❌ Redis connection test failed"
            fi
        else
            echo "❌ Redis container not running"
        fi
        ;;
    "help")
        echo "Usage: ./db-helper.sh [command] [container]"
        echo ""
        echo "Commands:"
        echo "  status              Show all container status (default)"
        echo "  start [container]   Start container(s) [all|postgres|redis] (default: all)"
        echo "  stop [container]    Stop container(s) [all|postgres|redis] (default: all)"
        echo "  create [container]  Create new container(s) [all|postgres|redis] (default: all)"
        echo "  remove [container]  Stop and remove container(s) [all|postgres|redis] (default: all)"
        echo "  logs [container]    Show container logs [postgres|redis] (default: postgres)"
        echo "  test                Test service connections"
        echo "  help                Show this help message"
        echo ""
        echo "Configuration:"
        echo "  Reads DATABASE_URL and REDIS_URL from .env file if available"
        echo "  Falls back to default values if .env not found"
        echo ""
        echo "Examples:"
        echo "  ./db-helper.sh start redis     # Start only Redis"
        echo "  ./db-helper.sh stop postgres   # Stop only PostgreSQL"
        echo "  ./db-helper.sh create all       # Create both containers"
        echo "  ./db-helper.sh test             # Test all connections"
        echo "  ./db-helper.sh logs redis       # Show Redis logs"
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo "Use './db-helper.sh help' for available commands"
        exit 1
        ;;
esac
