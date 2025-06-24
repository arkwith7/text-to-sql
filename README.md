# 🚀 Text-to-SQL 프로젝트

자연어를 SQL 쿼리로 변환하는 AI 기반 웹 애플리케이션입니다.

## 📋 프로젝트 개요

- **Frontend**: Vue.js + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python + SQLite (앱 데이터)
- **Cache**: Redis (세션/캐시)
- **Analysis Targets**: PostgreSQL, MySQL 등 (UI에서 동적 연결)
- **AI**: Azure OpenAI (GPT 모델)

## 🏗️ 프로젝트 구조

```
text-to-sql/
├── frontend/              # Vue.js 프론트엔드
├── backend/              # FastAPI 백엔드
│   └── dev-backend.sh    # 개발환경 시작 스크립트
├── postgre/              # PostgreSQL 설정
├── docs/                 # 프로젝트 문서
├── docker-compose.yml    # 운영 환경 (Docker Compose)
├── manage.sh            # 🎯 통합 관리 스크립트 (신규)
└── db-helper.sh         # 컨테이너 수동 관리 유틸리티
```

## 🚀 빠른 시작

### 🎯 통합 관리 스크립트 (권장)

**모든 환경을 하나의 스크립트로 관리:**

```bash
# 도움말 확인
./manage.sh help

# 개발환경 가이드
./manage.sh dev

# 운영환경 시작
./manage.sh prod start

# 전체 상태 확인
./manage.sh status
```

### 📋 지원 명령어

#### 개발환경
- `./manage.sh dev` - 개발환경 가이드 표시

#### 운영환경
- `./manage.sh prod start` - Docker Compose로 운영환경 시작
- `./manage.sh prod stop` - 운영환경 중지
- `./manage.sh prod restart` - 운영환경 재시작
- `./manage.sh prod logs [service]` - 로그 확인

#### 유틸리티
- `./manage.sh status` - 전체 서비스 상태 확인
- `./manage.sh cleanup` - 중지된 컨테이너 정리
- `./manage.sh help` - 도움말 표시

### 🛠️ 개발환경 설정 (레거시)

**기존 방식으로 백엔드 직접 실행:**

```bash
cd backend
./dev-backend.sh
```

#### 🔧 개발 환경 특징

- **백엔드 독립성**: SQLite + Redis로 완전 독립 실행
- **분석 DB 분리**: PostgreSQL 등은 UI에서 동적 연결
- **자동 설정**: 환경 변수 및 컨테이너 자동 구성
- **핫 리로드**: 코드 변경 시 자동 반영

#### 📦 개발 환경 구성

| 서비스     | 저장 위치        | 포트   | 용도                |
| ------- | ------------ | ---- | ----------------- |
| SQLite  | `app_data.db` | -    | 사용자 계정, 채팅 기록     |
| Redis   | `redis-dev`  | 6381 | 캐시/세션 저장소         |
| FastAPI | -            | 8000 | 백엔드 API 서버        |
| **분석 대상** | **UI에서 연결**   | **동적** | **PostgreSQL 등** |

#### 🌐 개발 환경 접속 정보

- **API 서버**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **상태 확인**: http://localhost:8000/health

### 2. 프론트엔드 개발 환경

```bash
cd frontend
npm install
npm run serve
```

- **개발 서버**: http://localhost:3000 (예상)

## 🐳 운영 환경 (Docker Compose)

### 통합 관리 스크립트 사용 (권장)

```bash
# 운영환경 시작
./manage.sh prod start

# 운영환경 중지
./manage.sh prod stop

# 운영환경 재시작
./manage.sh prod restart

# 로그 확인
./manage.sh prod logs           # 전체 로그
./manage.sh prod logs backend   # 백엔드만
./manage.sh prod logs frontend  # 프론트엔드만

# 상태 확인
./manage.sh status

# 정리
./manage.sh cleanup
```

### 레거시 Docker Compose 명령어

```bash
# 전체 스택 실행
docker-compose up -d

# 개별 서비스 실행
docker-compose up -d backend     # 백엔드만
docker-compose up -d frontend    # 프론트엔드만 
docker-compose up -d redis-stack # Redis만

# 중지
docker-compose down
```

### 🔗 운영환경 접속 정보

| 서비스 | URL | 설명 |
|--------|-----|------|
| 프론트엔드 | http://localhost:8080 | Vue.js 웹 인터페이스 |
| 백엔드 API | http://localhost:8070 | FastAPI 서버 |
| API 문서 | http://localhost:8070/docs | Swagger UI |
| Redis | localhost:6380 | 캐시/세션 저장소 |

## ⚙️ 환경 설정

### 필수 환경 변수 (.env)

```bash
# Azure OpenAI 설정
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_DEPLOYMENT_NAME=your_model_name

# 인증 설정
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## 🛠️ 환경 관리

### 📊 상태 모니터링

```bash
# 전체 환경 상태 확인 (개발 + 운영)
./manage.sh status

# 개발환경 정보 표시
./manage.sh dev
```

### 🔧 개발환경 관리

```bash
# 백엔드 직접 실행 (터미널에서)
cd backend && ./dev-backend.sh

# 프론트엔드 직접 실행 (별도 터미널)
cd frontend && npm run dev

# Redis 컨테이너 직접 관리 (레거시)
docker stop redis-dev      # 중지
docker start redis-dev     # 시작
docker rm -f redis-dev     # 완전 제거
```

### 📋 로그 및 디버깅

```bash
# 운영환경 로그
./manage.sh prod logs
./manage.sh prod logs backend

# Redis 로그 직접 확인
docker logs redis-dev

# 개발 백엔드 로그 (실행 중인 터미널에서 확인)
```

### 🗄️ 데이터베이스 접속

```bash
# SQLite 직접 접속 (sqlite3 필요)
sqlite3 app_data.db

# Redis 접속 (개발환경)
docker exec -it redis-dev redis-cli

# Redis 접속 (운영환경)  
docker exec -it redis-stack-prod redis-cli
```

### 🧹 정리 작업

```bash
# 모든 중지된 컨테이너/이미지 정리
./manage.sh cleanup

# 특정 환경만 정리
docker-compose down                    # 운영환경
docker stop redis-dev && docker rm redis-dev  # 개발환경
```

## 📊 포트 구성

### 개발 환경

- FastAPI: 8000
- PostgreSQL: 5433
- Redis: 6381
- Frontend: 3000 (예상)
- **분석 대상 DB**: UI에서 동적 설정

### 운영 환경

- Backend: 8070
- Frontend: 8080
- Redis: 6380
- **분석 대상 DB**: UI에서 동적 설정

## 🚨 문제 해결

### 포트 충돌 시

```bash
# 포트 사용 프로세스 확인
lsof -i :6381
lsof -i :8000

# Redis 개발 컨테이너 정리
docker stop redis-dev
docker rm redis-dev
```

### 개발 데이터 초기화

```bash
# SQLite 데이터 초기화
rm -f app_data.db
./dev-backend.sh  # 자동으로 새 데이터베이스 생성

# Redis 데이터 초기화
docker exec redis-dev redis-cli FLUSHALL
```

## 📁 백엔드 스크립트 정리

### 현재 사용 스크립트

- **`backend/dev-backend.sh`**: 통합 개발 환경 스크립트 (권장)

### 백업된 기존 스크립트

`backend/scripts-backup/` 폴더에 보관:
- `dev-backend.sh` (기존)
- `dev-backend-new.sh` 
- `dev-backend-with-redis.sh`
- `dev-backend-isolated.sh`
- `run_dev.sh`

## 🎯 개발 워크플로우

1. **백엔드 개발 시작**

   ```bash
   cd backend
   ./dev-backend.sh
   ```
2. **프론트엔드 개발 시작**

   ```bash
   cd frontend
   npm run serve
   ```
3. **코드 변경**
   - 백엔드: 자동 리로드 (핫 리로드)
   - 프론트엔드: 자동 리로드
4. **API 테스트**
   - Swagger UI: http://localhost:8000/docs
   - 직접 테스트: http://localhost:8000/api/...

## 🔒 보안 고려사항

- 개발 환경은 운영 환경과 완전 분리
- 개발용 시크릿 키는 프로덕션에서 변경 필요
- `.env` 파일은 버전 관리에서 제외

## 📚 추가 문서

- [데이터베이스 스키마](docs/DB_SCHEMA.md)
- [API 문서](docs/backend_api_list.md)
- [관리자 기능 설계](docs/ADMIN_FEATURES_DETAILED_DESIGN.md)

## 🤝 기여하기

1. 이 저장소를 포크합니다
2. 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
