#!/bin/bash
# Text-to-SQL 전용 읽기 전용 사용자 생성 스크립트 (개선된 버전)

POSTGRES_CONTAINER_NAME="northwind-postgres"
DB_USER="postgres"
DB_NAME="northwind"
READONLY_USER="texttosql_reader"
READONLY_PASSWORD="readonly_secure_password_2024"

echo "👤 Text-to-SQL용 읽기 전용 사용자 생성..."

# 컨테이너 실행 상태 확인
if ! docker ps --format "{{.Names}}" | grep -q "^${POSTGRES_CONTAINER_NAME}$"; then
    echo "❌ PostgreSQL 컨테이너가 실행되지 않음: $POSTGRES_CONTAINER_NAME"
    exit 1
fi

# 데이터베이스 존재 확인
if ! docker exec $POSTGRES_CONTAINER_NAME psql -U $DB_USER -lqt | grep -q "$DB_NAME"; then
    echo "❌ 데이터베이스가 존재하지 않음: $DB_NAME"
    exit 1
fi

# 기존 사용자 확인 및 삭제
echo "🔍 기존 사용자 확인 중..."
if docker exec $POSTGRES_CONTAINER_NAME psql -U $DB_USER -tAc "SELECT 1 FROM pg_roles WHERE rolname='$READONLY_USER'" | grep -q 1; then
    echo "⚠️  기존 사용자가 존재합니다. 삭제 후 재생성합니다."
    docker exec $POSTGRES_CONTAINER_NAME psql -U $DB_USER -c "DROP USER IF EXISTS $READONLY_USER;"
fi

# 읽기 전용 사용자 생성
echo "🔧 사용자 생성 중..."
docker exec $POSTGRES_CONTAINER_NAME psql -U $DB_USER -d $DB_NAME << EOF
-- 읽기 전용 사용자 생성
CREATE USER $READONLY_USER WITH PASSWORD '$READONLY_PASSWORD';

-- 데이터베이스 연결 권한 부여
GRANT CONNECT ON DATABASE $DB_NAME TO $READONLY_USER;

-- 스키마 사용 권한 부여
GRANT USAGE ON SCHEMA public TO $READONLY_USER;

-- 모든 테이블에 대한 SELECT 권한 부여
GRANT SELECT ON ALL TABLES IN SCHEMA public TO $READONLY_USER;

-- 향후 생성될 테이블에도 자동으로 SELECT 권한 부여
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO $READONLY_USER;

-- 시퀀스 읽기 권한 (필요한 경우)
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO $READONLY_USER;

-- 함수 실행 권한 (읽기 전용 함수들만)
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO $READONLY_USER;
EOF

if [ $? -eq 0 ]; then
    echo "✅ 읽기 전용 사용자 생성 완료"
    
    # 연결 테스트
    echo "🔗 연결 테스트 중..."
    if docker exec $POSTGRES_CONTAINER_NAME psql -U $READONLY_USER -d $DB_NAME -c "SELECT COUNT(*) FROM customers;" > /dev/null 2>&1; then
        echo "✅ 연결 테스트 성공"
        
        # 권한 테스트 (INSERT가 차단되는지 확인)
        echo "🛡️  권한 테스트 중..."
        if docker exec $POSTGRES_CONTAINER_NAME psql -U $READONLY_USER -d $DB_NAME -c "INSERT INTO customers (customer_id, company_name) VALUES ('TEST', 'Test');" 2>&1 | grep -q "permission denied"; then
            echo "✅ 쓰기 권한 차단 확인됨 (정상)"
        else
            echo "⚠️  쓰기 권한 테스트 실패"
        fi
    else
        echo "❌ 연결 테스트 실패"
        exit 1
    fi
    
    echo ""
    echo "📋 Text-to-SQL 연결 정보:"
    echo "   Host: localhost"
    echo "   Port: 5432"
    echo "   Database: $DB_NAME"
    echo "   User: $READONLY_USER"
    echo "   Password: $READONLY_PASSWORD"
    echo ""
    echo "🔗 연결 URL: postgresql://$READONLY_USER:$READONLY_PASSWORD@localhost:5432/$DB_NAME"
    echo ""
    echo "⚠️  이 사용자는 읽기 전용이므로 SELECT 쿼리만 실행 가능합니다."
else
    echo "❌ 읽기 전용 사용자 생성 실패"
    exit 1
fi
