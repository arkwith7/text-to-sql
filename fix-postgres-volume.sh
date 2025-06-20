#!/bin/bash

# PostgreSQL 볼륨 영속성 문제 해결 스크립트
# 현재 익명 볼륨을 명명된 볼륨으로 마이그레이션

echo "🔧 PostgreSQL 데이터 영속성 문제 해결 중..."

# 현재 컨테이너 상태 확인
if ! docker ps --format "{{.Names}}" | grep -q "^northwind-postgres$"; then
    echo "❌ northwind-postgres 컨테이너가 실행되지 않음"
    exit 1
fi

# 백업 생성
echo "📦 현재 데이터 백업 중..."
mkdir -p /tmp/postgres_migration
docker exec northwind-postgres pg_dump -U postgres northwind > /tmp/postgres_migration/northwind_backup.sql

if [ $? -eq 0 ]; then
    echo "✅ 백업 완료: /tmp/postgres_migration/northwind_backup.sql"
else
    echo "❌ 백업 실패"
    exit 1
fi

# 명명된 볼륨 생성 (이미 있으면 무시)
echo "📁 명명된 볼륨 생성 중..."
docker volume create postgres_data

# 현재 컨테이너 중지 및 제거
echo "🛑 현재 컨테이너 중지 및 제거 중..."
docker stop northwind-postgres
docker rm northwind-postgres

# .env 파일에서 데이터베이스 설정 읽기
if [ -f ".env" ]; then
    source ".env"
elif [ -f "../.env" ]; then
    source "../.env"
else
    echo "❌ .env 파일을 찾을 수 없음"
    exit 1
fi

# DATABASE_URL 파싱
if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
    DB_USER="${BASH_REMATCH[1]}"
    DB_PASSWORD="${BASH_REMATCH[2]}"
    DB_HOST="${BASH_REMATCH[3]}"
    DB_PORT="${BASH_REMATCH[4]}"
    DB_NAME="${BASH_REMATCH[5]}"
else
    echo "❌ DATABASE_URL 형식이 잘못됨"
    exit 1
fi

# 새 컨테이너 생성 (명명된 볼륨 사용)
echo "🚀 새 컨테이너 생성 중 (명명된 볼륨 사용)..."
docker run -d \
    --name northwind-postgres \
    -e POSTGRES_USER=${DB_USER} \
    -e POSTGRES_PASSWORD=${DB_PASSWORD} \
    -e POSTGRES_DB=${DB_NAME} \
    -p ${DB_PORT}:5432 \
    -v postgres_data:/var/lib/postgresql/data \
    postgres:15

# PostgreSQL 시작 대기
echo "⏳ PostgreSQL 시작 대기 중..."
sleep 15

# 연결 대기
for i in {1..30}; do
    if docker exec northwind-postgres pg_isready -h localhost -p 5432 -U $DB_USER > /dev/null 2>&1; then
        echo "✅ PostgreSQL 준비 완료"
        break
    fi
    echo "   시도 $i/30: PostgreSQL 준비 중..."
    sleep 2
done

# 백업 데이터 복원
echo "📥 백업 데이터 복원 중..."
docker exec -i northwind-postgres psql -U $DB_USER -d $DB_NAME < /tmp/postgres_migration/northwind_backup.sql

if [ $? -eq 0 ]; then
    echo "✅ 데이터 복원 완료"
else
    echo "⚠️  데이터 복원 중 일부 오류 발생 (정상적일 수 있음)"
fi

# 테이블 확인
echo "🔍 데이터 복원 검증 중..."
TABLE_COUNT=$(docker exec northwind-postgres psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' \n')

echo "📊 복원된 테이블 수: $TABLE_COUNT"

if [ "$TABLE_COUNT" -gt 10 ]; then
    echo "✅ 데이터 복원 성공!"
    echo ""
    echo "🎉 PostgreSQL 볼륨 영속성 문제가 해결되었습니다!"
    echo "   이제 컨테이너를 재시작해도 데이터가 보존됩니다."
    echo ""
    echo "📋 사용된 볼륨: postgres_data"
    echo "🗂️  백업 파일: /tmp/postgres_migration/northwind_backup.sql"
else
    echo "❌ 데이터 복원 실패"
    echo "   수동으로 백업 파일을 확인하세요: /tmp/postgres_migration/northwind_backup.sql"
fi
