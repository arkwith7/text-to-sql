# 데이터베이스 지원 현황

## 현재 지원 현황

### ✅ PostgreSQL (완전 지원)

- **패키지**: `asyncpg`
- **기능**: 연결 테스트, 스키마 조회, SQL 실행 모두 지원
- **포트**: 5432 (기본)
- **연결 문자열**: `postgresql://user:password@host:port/database`

## 향후 지원 예정

### 🟡 MySQL / MariaDB

- **필요 패키지**: `aiomysql`, `PyMySQL`
- **포트**: 3306 (기본)
- **연결 문자열**: `mysql://user:password@host:port/database`
- **구현 필요 사항**:
  - `ConnectionService.test_connection()` 메서드에 MySQL 지원 추가
  - `DatabaseManager.get_analysis_db_engine()` 메서드에 MySQL 엔진 생성 로직 추가
  - SQLAlchemy MySQL 드라이버 설정

#### 구현 예시 (MySQL):

```python
# ConnectionService에서
elif db_type in ["mysql", "mariadb"]:
    import aiomysql
    conn = await aiomysql.connect(
        host=conn_data['db_host'],
        port=conn_data['db_port'],
        user=conn_data['db_user'],
        password=db_password,
        db=conn_data['db_name'],
        connect_timeout=5
    )
    await conn.execute("SELECT 1")
    await conn.close()
```

### 🟡 Oracle Database

- **필요 패키지**: `oracledb`, `cx_Oracle`
- **포트**: 1521 (기본)
- **연결 문자열**: `oracle://user:password@host:port/service_name`
- **구현 필요 사항**:
  - Oracle Instant Client 설치 필요
  - Oracle 특화된 연결 로직 구현
  - Oracle SQL 문법 차이점 고려

#### 구현 예시 (Oracle):

```python
# ConnectionService에서
elif db_type in ["oracle", "oracledb"]:
    import oracledb
    conn = await oracledb.connect_async(
        user=conn_data['db_user'],
        password=db_password,
        host=conn_data['db_host'],
        port=conn_data['db_port'],
        service_name=conn_data['db_name']
    )
    cursor = await conn.cursor()
    await cursor.execute("SELECT 1 FROM DUAL")
    await cursor.close()
    await conn.close()
```

### 🟡 Microsoft SQL Server

- **필요 패키지**: `aioodbc`, `pyodbc`
- **포트**: 1433 (기본)
- **연결 문자열**: `mssql+pyodbc://user:password@host:port/database?driver=ODBC+Driver+17+for+SQL+Server`
- **구현 필요 사항**:
  - ODBC 드라이버 설치 필요
  - Windows/Linux 환경별 드라이버 차이점 고려
  - SQL Server 특화된 문법 지원

#### 구현 예시 (SQL Server):

```python
# ConnectionService에서
elif db_type in ["sqlserver", "mssql"]:
    import aioodbc
    dsn = f"Driver={{ODBC Driver 17 for SQL Server}};Server={conn_data['db_host']},{conn_data['db_port']};Database={conn_data['db_name']};Uid={conn_data['db_user']};Pwd={db_password};"
    conn = await aioodbc.connect(dsn=dsn, timeout=5)
    cursor = await conn.cursor()
    await cursor.execute("SELECT 1")
    await cursor.close()
    await conn.close()
```

## 구현 우선순위

1. **MySQL/MariaDB** - 가장 널리 사용되는 오픈소스 데이터베이스
2. **MS SQL Server** - 기업 환경에서 많이 사용
3. **Oracle** - 대기업 환경에서 사용, 복잡성이 높음

## 추가 고려사항

### 1. SQLAlchemy 엔진 생성

각 데이터베이스별로 `get_analysis_db_engine()` 메서드 확장 필요:

```python
async def get_analysis_db_engine(self, connection_id: str, user_id: str):
    # ... 기존 코드 ...
    
    if db_type == 'postgresql':
        analysis_db_url = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    elif db_type == 'mysql':
        analysis_db_url = f"mysql+aiomysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    elif db_type == 'oracle':
        analysis_db_url = f"oracle+oracledb://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    elif db_type == 'sqlserver':
        analysis_db_url = f"mssql+aioodbc://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?driver=ODBC+Driver+17+for+SQL+Server"
    
    return create_async_engine(analysis_db_url, pool_pre_ping=True)
```

### 2. SQL 문법 차이점

각 데이터베이스의 SQL 문법 차이점을 고려한 Agent 로직 필요:
- Oracle: `DUAL` 테이블, `ROWNUM` 등
- SQL Server: `TOP`, `IDENTITY` 등  
- MySQL: `LIMIT`, `AUTO_INCREMENT` 등

### 3. 에러 처리

각 데이터베이스별 특화된 예외 처리 필요:
- PostgreSQL: `asyncpg` 예외
- MySQL: `aiomysql` 예외
- Oracle: `oracledb` 예외
- SQL Server: `pyodbc` 예외

## 설치 방법 (향후)

### MySQL 지원시:

```bash
pip install aiomysql PyMySQL
```

### Oracle 지원시:

```bash
pip install oracledb
# Oracle Instant Client 설치 별도 필요
```

### SQL Server 지원시:

```bash
pip install aioodbc pyodbc
# ODBC Driver 17 for SQL Server 설치 별도 필요
```

 