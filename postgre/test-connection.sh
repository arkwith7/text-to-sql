#!/bin/bash
# PostgreSQL 연결 테스트 스크립트
# bash 히스토리 확장 문제 해결

echo "=== PostgreSQL Text-to-SQL 연결 테스트 ==="

# 1. 기본 연결 테스트
echo "1. 기본 연결 테스트:"
docker exec northwind-postgres psql -U texttosql_reader -d northwind -c "SELECT 'Connection OK' as status;"

# 2. 데이터 확인
echo -e "\n2. 데이터 확인:"
docker exec northwind-postgres psql -U texttosql_reader -d northwind -c "SELECT COUNT(*) as customer_count FROM customers;"

# 3. 스키마 정보
echo -e "\n3. 테이블 목록:"
docker exec northwind-postgres psql -U texttosql_reader -d northwind -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"

# 4. 샘플 쿼리 (Text-to-SQL에서 자주 사용되는 패턴)
echo -e "\n4. 샘플 쿼리 - 고객별 주문 수:"
docker exec northwind-postgres psql -U texttosql_reader -d northwind -c "
SELECT c.company_name, COUNT(o.order_id) as order_count 
FROM customers c 
LEFT JOIN orders o ON c.customer_id = o.customer_id 
GROUP BY c.customer_id, c.company_name 
ORDER BY order_count DESC 
LIMIT 5;
"

# 5. 권한 테스트 (실패해야 정상)
echo -e "\n5. 권한 테스트 (INSERT 시도 - 실패해야 정상):"
docker exec northwind-postgres psql -U texttosql_reader -d northwind -c "
INSERT INTO customers (customer_id, company_name) VALUES ('TEST', 'Test Company');
" 2>&1 | head -1

echo -e "\n=== 테스트 완료 ==="
echo "✅ 모든 SELECT 쿼리가 성공하고 INSERT가 차단되면 정상입니다."
