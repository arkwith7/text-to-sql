# MS SQL Server AdventureWorks 샘플 데이터베이스

이 디렉토리에는 Text-to-SQL 프로젝트에서 사용할 MS SQL Server AdventureWorks 샘플 데이터베이스 설정이 포함되어 있습니다.

## 🗄️ AdventureWorks 데이터베이스

AdventureWorks는 Microsoft에서 제공하는 공식 샘플 데이터베이스로, 가상의 자전거 제조회사 데이터를 포함합니다.

### 포함된 데이터베이스

- **AdventureWorks**: 표준 OLTP 샘플 데이터베이스
- **AdventureWorksDW**: 데이터 웨어하우스 샘플
- **AdventureWorksLT**: 경량화된 샘플 데이터베이스

## 🚀 빠른 시작

### 1. MS SQL Server 시작

```bash
cd mssql
./setup-adventureworks.sh start
```

### 2. 상태 확인

```bash
./setup-adventureworks.sh status
```

### 3. 연결 정보

- **서버**: localhost,1433
- **사용자**: sa
- **패스워드**: Adventure123!
- **데이터베이스**: AdventureWorks, AdventureWorksDW, AdventureWorksLT

## 📋 사용 가능한 명령어

| 명령어 | 설명 |
|--------|------|
| `start` | MS SQL Server AdventureWorks 시작 |
| `stop` | MS SQL Server AdventureWorks 중지 |
| `restart` | MS SQL Server AdventureWorks 재시작 |
| `remove` | 컨테이너 완전 제거 |
| `status` | 현재 상태 확인 |
| `logs` | 로그 확인 |
| `help` | 도움말 표시 |

## 🔍 샘플 쿼리

### 기본 테이블 조회

```sql
USE AdventureWorks;

-- 직원 정보
SELECT TOP 10 * FROM Person.Person;

-- 제품 정보
SELECT TOP 10 * FROM Production.Product;

-- 주문 정보
SELECT TOP 10 * FROM Sales.SalesOrderHeader;
```

### 조인 쿼리 예시

```sql
-- 고객별 주문 금액
SELECT 
    p.FirstName + ' ' + p.LastName AS CustomerName,
    COUNT(soh.SalesOrderID) AS OrderCount,
    SUM(soh.TotalDue) AS TotalAmount
FROM Sales.SalesOrderHeader soh
INNER JOIN Sales.Customer c ON soh.CustomerID = c.CustomerID
INNER JOIN Person.Person p ON c.PersonID = p.BusinessEntityID
GROUP BY p.FirstName, p.LastName
ORDER BY TotalAmount DESC;
```

## 🌐 Text-to-SQL 앱에서 사용

Text-to-SQL 웹 앱에서 다음 연결 정보를 사용하여 AdventureWorks 데이터베이스에 연결할 수 있습니다:

```
데이터베이스 유형: Microsoft SQL Server
호스트: localhost
포트: 1433
데이터베이스: AdventureWorks
사용자명: sa
패스워드: Adventure123!
```

## 🛠️ 관리

### 컨테이너 직접 관리

```bash
# Docker 명령으로 직접 관리
docker ps                           # 실행 중인 컨테이너 확인
docker logs mssql-adventureworks    # 로그 확인
docker exec -it mssql-adventureworks bash  # 컨테이너 내부 접속
```

### SQL 명령 실행

```bash
# sqlcmd로 직접 연결
docker exec -it mssql-adventureworks /opt/mssql-tools/bin/sqlcmd \
    -S localhost -U sa -P 'Adventure123!' \
    -Q "SELECT @@VERSION"
```

## 📚 참고 자료

- [Microsoft AdventureWorks 공식 문서](https://docs.microsoft.com/en-us/sql/samples/adventureworks-install-configure)
- [Docker Hub: chriseaton/adventureworks](https://hub.docker.com/r/chriseaton/adventureworks)
- [AdventureWorks 스키마 다이어그램](https://docs.microsoft.com/en-us/sql/samples/adventureworks-install-configure?view=sql-server-ver15#schema-diagrams)