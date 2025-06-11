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

Copy the example environment file and update with your Azure OpenAI credentials:

```bash
cp .env.example .env
```

Edit `.env` file:
```env
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
```

### 3. Start the Application (Recommended)

**The smart way - handles all PostgreSQL scenarios automatically:**

```bash
# This script intelligently handles:
# - Running PostgreSQL containers
# - Stopped PostgreSQL containers  
# - Missing PostgreSQL containers
./start-existing-db.sh
```

**Alternative methods:**

```bash
# Fresh installation (stops existing containers)
./start-fresh.sh

# Original Docker Compose method
docker-compose up --build
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

### Smart Scripts

The project includes intelligent scripts that handle different scenarios:

#### Main Application Scripts

```bash
# Recommended: Smart PostgreSQL handling
./start-existing-db.sh
# - Detects existing PostgreSQL containers
# - Starts stopped containers automatically  
# - Creates new container if none exists
# - Preserves existing data

# Fresh installation (clean slate)
./start-fresh.sh
# - Stops all existing containers
# - Creates everything from scratch
# - Loads fresh Northwind data

# Legacy method
./start.sh
# - Original script (less intelligent)
```

#### Development Mode (Recommended for coding)

**Step 1: Setup development environment**
```bash
./dev-setup.sh
# - Prepares database and environment
# - Shows status and next steps
```

**Step 2: Start backend (Terminal 1)**
```bash
./dev-backend.sh
# - Creates Python virtual environment
# - Installs dependencies automatically
# - Runs FastAPI with auto-reload
# - Available at http://localhost:8000
```

**Step 3: Start frontend (Terminal 2)**  
```bash
./dev-frontend.sh
# - Installs Node.js dependencies
# - Runs Vue.js with hot reload
# - Available at http://localhost:3000
```

**Benefits of development mode:**
- ✅ Real-time code changes (auto-reload/hot-reload)
- ✅ Direct debugging with IDE breakpoints
- ✅ Better error messages and logging
- ✅ Independent restart of backend/frontend
- ✅ No container rebuild needed for code changes

#### Database Management Helper

```bash
# Check PostgreSQL container status
./db-helper.sh status

# Start/stop container
./db-helper.sh start
./db-helper.sh stop

# Create new container with Northwind data
./db-helper.sh create

# Remove container completely
./db-helper.sh remove

# View container logs
./db-helper.sh logs

# Help information
./db-helper.sh help
```

### Local Development (without Docker)

#### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
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
├── .env.example             # Environment template
├── .gitignore              # Git ignore rules
│
├── 🚀 Startup Scripts
├── start-existing-db.sh     # Smart PostgreSQL handling (Recommended)
├── start-fresh.sh          # Fresh installation
├── start.sh               # Legacy startup script  
├── db-helper.sh           # Database management helper
│
├── 🔧 Backend (FastAPI)
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py            # Main API application
│
├── 🎨 Frontend (Vue.js)
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── components/    # Reusable components
│       ├── composables/   # Vue composables
│       ├── types/        # TypeScript types
│       └── views/        # Page components
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
2. **Port 5432 already in use**

   ```bash
   # Check what's using the port
   sudo lsof -i :5432

   # Or stop conflicting containers
   docker stop $(docker ps -q --filter "publish=5432")
   ```
3. **Azure OpenAI API errors**
   - Verify your API key and endpoint in `.env`
   - Check deployment name matches your Azure setup
   - Ensure you have sufficient quota
4. **Frontend build errors**

   ```bash
   # Clear node modules and reinstall
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```
5. **Backend dependency errors**

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

# Import Northwind data manually if needed
docker exec -i northwind-postgres psql -U postgres < ./postgre/northwind.sql

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

- Use `./start-fresh.sh` for clean demonstrations
- Sample questions are built into the frontend
- API documentation is available at `/docs` endpoint

## 📝 License

This project is for demonstration purposes.
