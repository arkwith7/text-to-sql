# PostgreSQL for Text-to-SQL 종합 가이드

## 📋 목차

1. [개요](#개요)
2. [주요 주의사항](#주요-주의사항)
3. [연결 정보](#연결-정보)
4. [보안 설정](#보안-설정)
5. [설정 및 운영](#설정-및-운영)
6. [모니터링 설정](#모니터링-설정)
7. [문제 해결](#문제-해결)
8. [성능 최적화](#성능-최적화)
9. [체크리스트](#체크리스트)
10. [비상 복구](#비상-복구)

---

## 🎯 개요

이 문서는 **Azure OpenAI 기반 Text-to-SQL 시스템**에서 **PostgreSQL Northwind 데이터베이스**를 안전하고 안정적으로 사용하기 위한 종합 가이드입니다.

### 주요 목표

- **데이터 손실 방지**: PostgreSQL 컨테이너에서 Northwind 데이터 보호
- **안전한 쿼리 실행**: AI 생성 쿼리로 인한 데이터베이스 손상 방지
- **자동화된 관리**: 백업, 모니터링, 복구 시스템 구축
- **성능 최적화**: 효율적인 Text-to-SQL 운영

---

## ⚠️ 주요 주의사항

### 🚨 데이터베이스 손실 위험 요소

#### 1. Text-to-SQL로 인한 위험

| 위험 유형      | 설명           | 발생 가능한 쿼리                               | 해결책         |
| ---------- | ------------ | --------------------------------------- | ----------- |
| **스키마 변경** | 테이블 구조 수정/삭제 | `ALTER TABLE`, `DROP TABLE`             | SQL 안전성 검증기 |
| **데이터 삭제** | 대량 데이터 삭제    | `DELETE FROM ... WHERE 1=1`, `TRUNCATE` | 읽기 전용 사용자   |
| **무한 루프**  | 재귀 쿼리 무한 실행  | `WITH RECURSIVE` 잘못된 조건                 | 쿼리 복잡도 검사   |
| **카티지안 곱** | 과도한 메모리 사용   | `JOIN` 조건 누락                            | 쿼리 검증       |

#### 2. Docker 컨테이너 관련 위험

- **볼륨 손실**: 컨테이너 삭제 시 데이터 손실
- **메모리 부족**: 컨테이너 크래시로 인한 데이터 불일치
- **네트워크 문제**: 연결 끊김으로 인한 트랜잭션 실패

### 🛡️ 핵심 보호 조치

1. **읽기 전용 사용자 사용 필수**
2. **자동 백업 시스템 운영**
3. **SQL 쿼리 사전 검증**
4. **실시간 헬스체크 모니터링**

---

## 🔐 연결 정보

### Text-to-SQL 시스템용 (읽기 전용) ⭐ 권장

```
Host: localhost
Port: 5432
Database: northwind
User: texttosql_reader
Password: readonly_secure_password_2024

연결 URL: postgresql://texttosql_reader:readonly_secure_password_2024@localhost:5432/northwind
```

### 관리자용 (관리 목적만)

```
Host: localhost
Port: 5432
Database: northwind
User: postgres
Password: password

연결 URL: postgresql://postgres:password@localhost:5432/northwind
```

### 연결 확인 방법

```bash
# 읽기 전용 사용자 연결 테스트
docker exec northwind-postgres psql -U texttosql_reader -d northwind -c "SELECT COUNT(*) FROM customers;"

# 관리자 연결 테스트
docker exec northwind-postgres psql -U postgres -d northwind -c "SELECT version();"
```

---

## 🔒 보안 설정

### 읽기 전용 사용자 권한

```sql
-- 허용되는 작업
✅ SELECT 쿼리
✅ VIEW 조회
✅ 함수 실행 (읽기 전용)
✅ 스키마 정보 조회

-- 차단되는 작업
❌ INSERT, UPDATE, DELETE
❌ CREATE, ALTER, DROP
❌ TRUNCATE
❌ 권한 변경
```

### 사용자 생성 및 권한 설정

```bash
# 읽기 전용 사용자 생성
./create-readonly-user.sh

# 수동 생성 (필요 시)
docker exec northwind-postgres psql -U postgres -d northwind << EOF
CREATE USER texttosql_reader WITH PASSWORD 'readonly_secure_password_2024';
GRANT CONNECT ON DATABASE northwind TO texttosql_reader;
GRANT USAGE ON SCHEMA public TO texttosql_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO texttosql_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO texttosql_reader;
EOF
```

---

## 🛠️ 설정 및 운영

### 1. PostgreSQL 컨테이너 초기 설정

```bash
# 전체 설정 (데이터 포함)
./setup-northwind.sh

# 강제 재생성 (문제 발생 시)
./setup-northwind.sh --force-recreate

# 읽기 전용 사용자 생성
./create-readonly-user.sh

# 첫 백업 생성
./postgres-backup.sh backup
```

### 2. 컨테이너 관리 명령어

```bash
# 상태 확인
docker ps | grep northwind-postgres
docker logs northwind-postgres

# 시작/중지/재시작
docker start northwind-postgres
docker stop northwind-postgres
docker restart northwind-postgres

# 리소스 사용량 확인
docker stats northwind-postgres
```

### 3. 데이터베이스 직접 접속

```bash
# 관리자로 접속
docker exec -it northwind-postgres psql -U postgres -d northwind

# 읽기 전용 사용자로 접속
docker exec -it northwind-postgres psql -U texttosql_reader -d northwind
```

---

## 📊 모니터링 설정

### 자동 모니터링 (Cron 설정)

```bash
# crontab -e 명령으로 다음 내용 추가

# 매시간 헬스체크 및 자동 복구
0 * * * * /home/wjadmin/Dev/text-to-sql/postgre/postgres-health-check.sh --cron

# 매일 새벽 2시 자동 백업
0 2 * * * /home/wjadmin/Dev/text-to-sql/postgre/postgres-backup.sh auto

# 매주 일요일 새벽 3시 컨테이너 재시작 (메모리 정리)
0 3 * * 0 docker restart northwind-postgres

# 매일 새벽 4시 로그 파일 압축
0 4 * * * find /home/wjadmin/Dev/text-to-sql/logs -name "*.log" -size +100M -exec gzip {} \;
```

### 수동 모니터링

```bash
# 헬스체크
./postgres-health-check.sh

# 백업 상태 확인
ls -la /home/wjadmin/Dev/text-to-sql/backups/

# 데이터 무결성 확인
docker exec northwind-postgres psql -U postgres -d northwind -c "
SELECT 
    'customers' as table_name, COUNT(*) as count FROM customers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_details', COUNT(*) FROM order_details;
"
```

---

## 🔧 문제 해결

### 자주 발생하는 문제

#### 1. 컨테이너가 시작되지 않음

```bash
# 문제 진단
docker ps -a | grep northwind-postgres
docker logs northwind-postgres

# 해결 방법
docker stop northwind-postgres 2>/dev/null
docker rm northwind-postgres 2>/dev/null
./setup-northwind.sh
```

#### 2. 포트 충돌 (5432 포트 사용 중)

```bash
# 포트 사용 확인
lsof -i :5432
sudo netstat -tulpn | grep 5432

# 해결 방법
sudo systemctl stop postgresql  # 시스템 PostgreSQL 중지
docker restart northwind-postgres
```

#### 3. 데이터베이스 연결 실패

```bash
# 연결 테스트
docker exec northwind-postgres pg_isready -U postgres

# 사용자 확인
docker exec northwind-postgres psql -U postgres -c "\du"

# 데이터베이스 확인
docker exec northwind-postgres psql -U postgres -l
```

#### 4. Northwind 데이터 손실

```bash
# 1단계: 데이터 확인
docker exec northwind-postgres psql -U postgres -d northwind -c "SELECT COUNT(*) FROM customers;"

# 2단계: 최신 백업에서 복구
LATEST_BACKUP=$(ls -t /home/wjadmin/Dev/text-to-sql/backups/northwind_backup_*.sql.gz | head -1)
./postgres-backup.sh restore "$LATEST_BACKUP"

# 3단계: 백업이 없으면 전체 재설정
./setup-northwind.sh --force-recreate
```

### 진단 스크립트

```bash
#!/bin/bash
echo "=== PostgreSQL 시스템 진단 ==="

echo "1. 컨테이너 상태:"
docker ps | grep northwind-postgres

echo "2. 볼륨 상태:"
docker volume ls | grep postgres

echo "3. 포트 상태:"
lsof -i :5432 2>/dev/null || echo "포트 5432 사용 없음"

echo "4. 메모리 사용량:"
free -h

echo "5. 디스크 사용량:"
df -h

echo "6. 데이터베이스 연결 테스트:"
docker exec northwind-postgres pg_isready -U postgres

echo "7. 데이터 무결성 확인:"
docker exec northwind-postgres psql -U postgres -d northwind -c "SELECT COUNT(*) FROM customers;" 2>/dev/null || echo "연결 실패"

echo "=== 진단 완료 ==="
```

---

## 📈 성능 최적화

### 1. PostgreSQL 설정 최적화

```bash
# PostgreSQL 설정 확인
docker exec northwind-postgres psql -U postgres -c "
SELECT name, setting, unit FROM pg_settings 
WHERE name IN ('shared_buffers', 'effective_cache_size', 'work_mem', 'max_connections');
"

# 최적화 설정 적용
docker exec northwind-postgres psql -U postgres -c "
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET max_connections = '100';
SELECT pg_reload_conf();
"
```

### 2. 인덱스 최적화

```sql
-- 현재 인덱스 확인
SELECT tablename, indexname, indexdef 
FROM pg_indexes 
WHERE schemaname = 'public' 
ORDER BY tablename, indexname;

-- 쿼리 실행 계획 확인 (느린 쿼리 분석)
EXPLAIN ANALYZE SELECT c.company_name, COUNT(o.order_id) 
FROM customers c 
LEFT JOIN orders o ON c.customer_id = o.customer_id 
GROUP BY c.customer_id, c.company_name;
```

### 3. 연결 풀링 설정 (애플리케이션)

```python
# SQLAlchemy 연결 풀 설정 예시
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://texttosql_reader:readonly_secure_password_2024@localhost:5432/northwind"

engine = create_engine(
    DATABASE_URL,
    pool_size=10,          # 기본 연결 풀 크기
    max_overflow=20,       # 최대 추가 연결
    pool_timeout=30,       # 연결 대기 시간 (초)
    pool_recycle=3600,     # 연결 재사용 시간 (초)
    pool_pre_ping=True,    # 연결 유효성 사전 검사
    echo=False             # SQL 로깅 (개발 시에만 True)
)
```

### 4. 쿼리 최적화 가이드라인

```sql
-- ✅ 좋은 쿼리 예시
SELECT c.customer_id, c.company_name, COUNT(o.order_id) as order_count
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE c.country = 'Germany'
GROUP BY c.customer_id, c.company_name
ORDER BY order_count DESC
LIMIT 10;

-- ❌ 피해야 할 쿼리 패턴
-- 1. LIMIT 없는 대량 조회
SELECT * FROM order_details;  -- ❌

-- 2. 카티지안 곱
SELECT * FROM customers, orders;  -- ❌

-- 3. 비효율적인 와일드카드
SELECT * FROM products WHERE product_name LIKE '%a%';  -- ❌
```

---

## 📋 체크리스트

### 초기 설정 체크리스트

- [ ] PostgreSQL 컨테이너 정상 실행 확인
- [ ] Northwind 데이터베이스 생성 및 데이터 로드 완료
- [ ] 읽기 전용 사용자 (`texttosql_reader`) 생성
- [ ] 첫 번째 백업 파일 생성
- [ ] Cron 자동화 작업 설정
- [ ] Text-to-SQL 애플리케이션 연결 테스트
- [ ] SQL 안전성 검증기 적용

### 일일 운영 체크리스트

- [ ] 컨테이너 상태 확인 (`docker ps`)
- [ ] 백업 파일 생성 확인
- [ ] 로그 파일 크기 모니터링
- [ ] 메모리 사용량 확인 (`free -h`)
- [ ] 쿼리 성능 모니터링

### 주간 운영 체크리스트

- [ ] 백업 파일 무결성 테스트
- [ ] 디스크 사용량 확인 (`df -h`)
- [ ] 성능 통계 리뷰
- [ ] 보안 로그 검토
- [ ] 시스템 업데이트 확인

### 월간 운영 체크리스트

- [ ] 전체 시스템 점검
- [ ] 백업 복구 테스트 실시
- [ ] 성능 최적화 검토
- [ ] 보안 설정 검토
- [ ] 문서 업데이트

---

## 🆘 비상 복구

### 복구 레벨 1: 서비스 재시작

```bash
# 컨테이너 재시작
docker restart northwind-postgres

# 상태 확인
sleep 10
./postgres-health-check.sh

# 연결 테스트
docker exec northwind-postgres psql -U texttosql_reader -d northwind -c "SELECT 1;"
```

### 복구 레벨 2: 백업에서 데이터 복구

```bash
# 최신 백업 파일 확인
ls -la /home/wjadmin/Dev/text-to-sql/backups/

# 최신 백업에서 복구
LATEST_BACKUP=$(ls -t /home/wjadmin/Dev/text-to-sql/backups/northwind_backup_*.sql.gz | head -1)
echo "복구할 백업: $LATEST_BACKUP"
./postgres-backup.sh restore "$LATEST_BACKUP"

# 복구 후 검증
docker exec northwind-postgres psql -U postgres -d northwind -c "
SELECT 
    'customers' as table_name, COUNT(*) as count FROM customers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_details', COUNT(*) FROM order_details;
"
```

### 복구 레벨 3: 전체 시스템 재구축

```bash
# 1단계: 모든 리소스 제거
docker stop northwind-postgres
docker rm northwind-postgres
docker volume rm postgres_northwind_data

# 2단계: 시스템 정리
docker system prune -f
docker volume prune -f

# 3단계: 전체 재설정
./setup-northwind.sh --force-recreate
./create-readonly-user.sh

# 4단계: 첫 백업 생성
./postgres-backup.sh backup

# 5단계: 설정 확인
./postgres-health-check.sh
```

### 응급 연락처 및 에스컬레이션

#### 문제 발생 시 수집할 정보

```bash
# 로그 수집 스크립트
#!/bin/bash
LOG_DIR="/tmp/postgres-emergency-$(date +%Y%m%d-%H%M%S)"
mkdir -p $LOG_DIR

echo "응급 로그 수집 중..."

# 시스템 상태
docker ps > $LOG_DIR/containers.txt
docker volume ls > $LOG_DIR/volumes.txt
free -h > $LOG_DIR/memory.txt
df -h > $LOG_DIR/disk.txt

# PostgreSQL 상태
docker logs northwind-postgres > $LOG_DIR/postgres.log 2>&1
docker exec northwind-postgres psql -U postgres -c "\l" > $LOG_DIR/databases.txt 2>&1

# 네트워크 상태
netstat -tulpn | grep 5432 > $LOG_DIR/network.txt

# 압축하여 전달
tar -czf "$LOG_DIR.tar.gz" -C /tmp "$(basename $LOG_DIR)"
echo "응급 로그 파일: $LOG_DIR.tar.gz"
```

---

## 📊 Northwind 데이터베이스 스키마

### 주요 테이블 구조

| 테이블명              | 레코드 수 | 설명      | 주요 컬럼                                |
| ----------------- | ----- | ------- | ------------------------------------ |
| **customers**     | 91    | 고객 정보   | customer_id, company_name, country   |
| **products**      | 77    | 제품 정보   | product_id, product_name, unit_price |
| **orders**        | 196   | 주문 정보   | order_id, customer_id, order_date    |
| **order_details** | 518   | 주문 상세   | order_id, product_id, quantity       |
| **categories**    | 8     | 제품 카테고리 | category_id, category_name           |
| **employees**     | 10    | 직원 정보   | employee_id, first_name, last_name   |
| **suppliers**     | 29    | 공급업체    | supplier_id, company_name            |
| **shippers**      | 3     | 배송업체    | shipper_id, company_name             |

### Text-to-SQL에서 자주 사용되는 쿼리 패턴

```sql
-- 1. 고객별 주문 분석
SELECT c.company_name, COUNT(o.order_id) as order_count,
       SUM(od.unit_price * od.quantity) as total_amount
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
LEFT JOIN order_details od ON o.order_id = od.order_id
GROUP BY c.customer_id, c.company_name
ORDER BY total_amount DESC NULLS LAST;

-- 2. 제품별 매출 분석
SELECT p.product_name, cat.category_name,
       COUNT(od.order_id) as order_count,
       SUM(od.unit_price * od.quantity) as revenue
FROM products p
JOIN categories cat ON p.category_id = cat.category_id
LEFT JOIN order_details od ON p.product_id = od.product_id
GROUP BY p.product_id, p.product_name, cat.category_name
ORDER BY revenue DESC NULLS LAST;

-- 3. 월별 매출 트렌드
SELECT DATE_TRUNC('month', o.order_date) as month,
       COUNT(DISTINCT o.order_id) as orders,
       SUM(od.unit_price * od.quantity) as revenue
FROM orders o
JOIN order_details od ON o.order_id = od.order_id
WHERE o.order_date >= '1996-01-01'
GROUP BY DATE_TRUNC('month', o.order_date)
ORDER BY month;
```

---

## 🔗 관련 파일 및 스크립트

### 관리 스크립트

- `setup-northwind.sh` - PostgreSQL 컨테이너 초기 설정
- `postgres-backup.sh` - 백업 및 복구 관리
- `postgres-health-check.sh` - 헬스체크 및 모니터링
- `create-readonly-user.sh` - 읽기 전용 사용자 생성

### 설정 파일

- `northwind.sql` - Northwind 데이터베이스 스키마 및 데이터
- `연결정보.txt` - 연결 정보 요약
- `postgres-monitoring-cron` - Cron 작업 템플릿

### 애플리케이션 파일

- `sql_safety_validator.py` - SQL 안전성 검증기
- `connection_manager.py` - 데이터베이스 연결 관리자

---

**📅 마지막 업데이트**: 2025년 6월 27일  
**📞 지원**: 문제 발생 시 응급 로그 수집 후 시스템 관리자 연락  
**📖 버전**: v1.0 - PostgreSQL Text-to-SQL 종합 가이드