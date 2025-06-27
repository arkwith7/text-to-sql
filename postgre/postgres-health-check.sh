#!/bin/bash
# PostgreSQL 헬스체크 및 복구 스크립트

POSTGRES_CONTAINER_NAME="northwind-postgres"
DB_USER="postgres"
DB_NAME="northwind"

check_container_health() {
    echo "🔍 PostgreSQL 컨테이너 상태 확인..."
    
    if ! docker ps --format "{{.Names}}" | grep -q "^${POSTGRES_CONTAINER_NAME}$"; then
        echo "❌ 컨테이너가 실행되지 않음"
        return 1
    fi
    
    # DB 연결 확인
    if ! docker exec $POSTGRES_CONTAINER_NAME pg_isready -h localhost -U $DB_USER > /dev/null 2>&1; then
        echo "❌ PostgreSQL 서비스 응답 없음"
        return 1
    fi
    
    # 데이터 무결성 확인
    local customer_count=$(docker exec $POSTGRES_CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM customers;" 2>/dev/null | tr -d ' ' || echo "0")
    
    if [ -z "$customer_count" ] || [ "$customer_count" -eq 0 ]; then
        echo "❌ Northwind 데이터가 손실됨"
        return 1
    fi
    
    echo "✅ PostgreSQL 정상 동작 중 (고객 수: $customer_count)"
    return 0
}

# 주기적 헬스체크 (cron에서 사용)
if [[ "$1" == "--cron" ]]; then
    if ! check_container_health; then
        echo "$(date): PostgreSQL 문제 감지, 복구 시도..." >> /home/wjadmin/Dev/text-to-sql/logs/postgres-health.log
        cd /home/wjadmin/Dev/text-to-sql/postgre
        ./setup-northwind.sh
    fi
else
    check_container_health
fi
