# Smart Business Analytics Assistant

AI-powered natural language to SQL converter with real-time data visualization.

## 🚀 Features

- **Natural Language Processing**: Convert business questions to SQL queries using Azure OpenAI
- **Real-time Visualization**: Automatic chart generation (Bar, Line, Pie charts)
- **Northwind Database**: Complete e-commerce sample dataset
- **AI Insights**: Intelligent analysis and recommendations
- **Modern UI**: Responsive design with Tailwind CSS
- **Landing Page**: Professional landing page showcasing business value and ROI
- **Multi-language Support**: Korean and English interface

## 🏗️ Architecture

- **Frontend**: Vue 3 + TypeScript + Tailwind CSS
- **Backend**: Python FastAPI
- **Database**: PostgreSQL with Northwind data
- **AI**: Azure OpenAI GPT-4o-mini
- **Deployment**: Docker containers

## 📋 Prerequisites

- Docker & Docker Compose
- Azure OpenAI API access
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd /home/wjadmin/Dev/text-to-sql
```

### 2. Configure Environment

Create a `.env` file and add your Azure OpenAI credentials:
```env
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
```

### 3. Start the Application

```bash
# This script intelligently handles all PostgreSQL scenarios
./start-existing-db.sh
```

### 4. Access the Application

- **Landing Page**: http://localhost:3001 (비즈니스 가치 및 제품 소개)
- **Application**: http://localhost:3001/home (로그인 후 메인 애플리케이션)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

> **참고**: 랜딩 페이지(`/`)는 인증 없이 접근 가능하며, 메인 애플리케이션은 로그인이 필요합니다.

## 🎯 Sample Questions

Try these natural language queries:

- "지난 3개월간 가장 많이 팔린 제품 5개는?"
- "부서별 평균 급여를 보여줘"
- "매월 매출 추이를 확인하고 싶어"
- "고객별 주문 횟수 상위 10명"
- "카테고리별 제품 수량"
- "가장 수익성이 높은 제품은?"

## 🛠️ Development

### Development Mode

For active development with hot-reloading:

**1. Backend (Terminal 1)**
```bash
# 스마트 Northwind DB 체크 및 자동 초기화 포함
./dev-backend.sh
```

**2. Frontend (Terminal 2)**
```bash
cd frontend
npm run dev
```

> The backend runs on `http://localhost:8000` and the frontend on `http://localhost:3000`.

### 🛠️ Development Scripts 개선사항

#### dev-backend.sh 스마트 기능

`dev-backend.sh` 스크립트는 다음과 같은 지능형 데이터베이스 관리 기능을 제공합니다:

- **🔍 Northwind DB 자동 감지**: PostgreSQL 컨테이너 시작 시 Northwind 테이블 존재 여부 자동 확인
- **📥 조건부 데이터 로드**: Northwind 테이블이 없는 경우에만 `/postgre/northwind.sql`에서 데이터 자동 로드
- **⚡ 중복 방지**: 이미 초기화된 데이터베이스는 건너뛰어 빠른 시작
- **🔄 모든 시나리오 지원**: 
  - 새 컨테이너 생성 시
  - 기존 중지된 컨테이너 재시작 시  
  - 이미 실행 중인 컨테이너 확인 시

이를 통해 개발자는 데이터베이스 상태에 관계없이 항상 일관된 Northwind 데이터셋으로 작업할 수 있습니다.

### Database Management

Use the helper script to manage the PostgreSQL container:
```bash
# Check status
./db-helper.sh status

# Start/stop

./db-helper.sh start
./db-helper.sh stop

# Create or remove the database

./db-helper.sh create
./db-helper.sh remove
```

### Local Development (without Docker)

#### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

#### Database Only

```bash
# Start only PostgreSQL
./db-helper.sh create
# or
docker-compose up postgres -d
```

## 📒 Jupyter 노트북에서 가상환경 커널 사용법

이 프로젝트의 가상환경(venv)을 주피터 노트북에서 커널로 사용하려면 아래 절차를 따르세요.

1. **가상환경 활성화**

```bash
source venv/bin/activate
```

2. **ipykernel 설치**

```bash
pip install ipykernel
```

3. **커널 등록**

```bash
python -m ipykernel install --user --name text-to-sql-venv --display-name "text-to-sql (venv)"
```

4. **VSCode에서 커널 선택**

- 주피터 노트북 상단의 커널 선택 메뉴에서 `text-to-sql (venv)`를 선택하세요.
- 만약 바로 보이지 않으면 VSCode를 재시작하거나 커널 목록을 새로고침(↻) 하세요.
- **특히, 우측 상단의 Select Kernel을 클릭한 뒤, 나오는 리스트에서 'Jupyter Kernel...'을 선택하면 직접 만든 커널명이 보입니다. 이 커널명을 클릭하면 해당 가상환경이 적용됩니다.**

> 여러 프로젝트를 관리할 때는 각 프로젝트별로 위 과정을 반복하면 됩니다.

## 📊 Database Schema

The application uses the **Northwind** database with these main tables:

- `customers` - Customer information
- `orders` - Order details
- `order_details` - Order line items
- `products` - Product catalog
- `categories` - Product categories
- `suppliers` - Supplier information
- `employees` - Employee data

## 🔧 Configuration

### Environment Variables

| Variable                       | Description                   | Default                 |
| ------------------------------ | ----------------------------- | ----------------------- |
| `AZURE_OPENAI_ENDPOINT`        | Azure OpenAI service endpoint | Required                |
| `AZURE_OPENAI_API_KEY`         | Azure OpenAI API key          | Required                |
| `AZURE_OPENAI_API_VERSION`     | API version                   | `2024-02-15-preview`    |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Model deployment name         | `gpt-4o-mini`           |
| `DATABASE_URL`                 | PostgreSQL connection string  | Auto-configured         |
| `VITE_API_BASE_URL`            | Backend API URL for frontend  | `http://localhost:8000` |

## 📁 Project Structure

```
text-to-sql/
├── README.md                 # This file
├── docker-compose.yml        # Container orchestration
├── .gitignore              # Git ignore rules
│
├── 🚀 Startup Scripts
├── start-existing-db.sh     # Smart PostgreSQL handling (Recommended)
├── dev-backend.sh           # Backend development server
├── db-helper.sh           # Database management helper
│
├── 🔧 Backend (FastAPI)
├── backend/
│   ├── alembic/           # Database migrations
│   ├── main.py            # Main API application
│   ├── models.py          # Database models
│   ├── services.py        # Business logic
│   └── requirements.txt
│
├── 🎨 Frontend (Vue.js)
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── src/
│       ├── main.ts        # Entry point
│       ├── App.vue        # Root component
│       └── ...
│
└── 🗄️ Database
    └── postgre/
        ├── northwind.sql     # Northwind database schema + data
        └── setup-northwind.sh
```

## 🐛 Troubleshooting

### PostgreSQL Container Issues

The smart scripts automatically handle most PostgreSQL scenarios, but here are manual commands if needed:

```bash
# Check container status
./db-helper.sh status

# If container exists but stopped
./db-helper.sh start

# If container doesn't exist
./db-helper.sh create

# If you want to start fresh
./db-helper.sh remove
./db-helper.sh create
```

### Common Issues

1. **Container startup fails**

   ```bash
   docker-compose down
   ./start-existing-db.sh
   ```

2. **Northwind 데이터베이스 수동 초기화**

   ```bash
   # 컨테이너가 실행 중인 상태에서
   docker exec -i northwind-postgres psql -U postgres -d northwind < ./postgre/northwind.sql
   
   # 또는 dev-backend.sh를 다시 실행 (자동으로 체크 및 초기화)
   ./dev-backend.sh
   ```

3. **Port 5432 already in use**

   ```bash
   # Check what's using the port
   sudo lsof -i :5432

   # Or stop conflicting containers
   docker stop $(docker ps -q --filter "publish=5432")
   ```
4. **Azure OpenAI API errors**
   - Verify your API key and endpoint in `.env`
   - Check deployment name matches your Azure setup
   - Ensure you have sufficient quota
5. **Frontend build errors**

   ```bash
   # Clear node modules and reinstall
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```
6. **Backend dependency errors**

   ```bash
   # Rebuild backend container
   docker-compose build --no-cache backend
   ```

### Container Management

```bash
# View all project containers
docker ps -a --filter "name=text-to-sql"
docker ps -a --filter "name=northwind"

# Stop all project containers
docker stop text-to-sql-backend text-to-sql-frontend northwind-postgres

# Remove all project containers
docker rm text-to-sql-backend text-to-sql-frontend northwind-postgres

# View logs for specific services
docker-compose logs backend
docker-compose logs frontend
./db-helper.sh logs

# Follow logs in real-time
docker-compose logs -f
```

### Database Connection Issues

```bash
# Test database connection from host
docker exec northwind-postgres psql -U postgres -d northwind -c "SELECT COUNT(*) FROM customers;"

# Import Northwind data manually if needed (하지만 dev-backend.sh가 자동으로 처리)
docker exec -i northwind-postgres psql -U postgres -d northwind < ./postgre/northwind.sql

# Access database shell
docker exec -it northwind-postgres psql -U postgres -d northwind
```

## 📈 API Endpoints

- `GET /` - Health check
- `GET /schema` - Database schema information
- `POST /query` - Execute natural language query
- `GET /docs` - API documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with the provided scripts
5. Submit a pull request

## 💡 Tips & Best Practices

### For Developers

- Use `./start-existing-db.sh` for development - it's the smartest option
- Use `./db-helper.sh status` to quickly check database state
- Backend logs: `docker-compose logs -f backend`
- Frontend logs: `docker-compose logs -f frontend`
- Database logs: `./db-helper.sh logs`

### For Production

- Use environment-specific `.env` files
- Consider using external managed PostgreSQL
- Configure proper logging and monitoring
- Set up CI/CD with the provided Docker configurations

### For Demos

- Sample questions are built into the frontend
- API documentation is available at `/docs` endpoint

## 📝 License

This project is for demonstration purposes.
