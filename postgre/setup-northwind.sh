#!/bin/bash
# setup-northwind.sh

echo "🐳 Northwind PostgreSQL 컨테이너 설정 시작..."

# 기존 컨테이너 정리
docker stop northwind-postgres 2>/dev/null
docker rm northwind-postgres 2>/dev/null

# 컨테이너 실행
echo "📦 PostgreSQL 컨테이너 실행..."
docker run --name northwind-postgres \
  -e POSTGRES_DB=northwind \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  -d postgres:latest

# 컨테이너 시작 대기
echo "⏳ 컨테이너 시작 대기..."
sleep 10

# Northwind 데이터 다운로드
echo "📥 Northwind 데이터 다운로드..."
curl -o northwind.sql https://raw.githubusercontent.com/pthom/northwind_psql/master/northwind.sql

# 데이터 적재
echo "🔄 데이터베이스에 데이터 적재..."
docker cp northwind.sql northwind-postgres:/northwind.sql
docker exec northwind-postgres psql -U postgres -d northwind -f /northwind.sql

# 확인
echo "✅ 설정 완료! 테스트 쿼리 실행..."
docker exec northwind-postgres psql -U postgres -d northwind -c "SELECT COUNT(*) as customer_count FROM customers;"

echo "🎉 Northwind 데이터베이스 준비 완료!"
echo "연결 정보: localhost:5432, DB: northwind, User: postgres, Password: password"