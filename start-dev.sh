#!/bin/bash

# Start Development Environment
# 통합 개발환경 시작 스크립트
#
# 🎯 주요 기능:
# - 개발환경 전용 Redis 컨테이너 시작
# - 백엔드 개발 서버 시작 (localhost:8000)
# - 프론트엔드 개발 서버 시작 (localhost:3000)
#
# 📋 사용법:
#   ./start-dev.sh
#
# 🔧 포트 사용:
#   - Frontend: http://localhost:3000
#   - Backend: http://localhost:8000
#   - Redis: localhost:6379
#   - RedisInsight: http://localhost:8001

echo "🚀 Starting Text-to-SQL Development Environment..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    if [ -f ".env.example" ]; then
        cp ".env.example" ".env"
        echo "📝 Please edit .env file with your Azure OpenAI credentials before continuing."
        exit 1
    else
        echo "❌ .env.example file not found. Please create .env file manually."
        exit 1
    fi
fi

# Start Redis development container
echo "🐳 Starting Redis development container..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
timeout=30
while [ $timeout -gt 0 ]; do
    if docker exec redis-dev redis-cli ping &>/dev/null; then
        echo "✅ Redis is ready"
        break
    fi
    sleep 1
    timeout=$((timeout - 1))
done

if [ $timeout -eq 0 ]; then
    echo "⚠️  Redis container started but not responding to ping"
fi

echo ""
echo "🎯 Development Environment Started:"
echo "   🔗 Frontend: http://localhost:3000"
echo "   🔗 Backend API: http://localhost:8000"
echo "   🔗 API Docs: http://localhost:8000/docs"
echo "   🔗 Redis: localhost:6379"
echo "   🔗 RedisInsight: http://localhost:8001"
echo ""
echo "📝 Next Steps:"
echo "   1. Start backend: cd backend && ./dev-backend.sh"
echo "   2. Start frontend: cd frontend && npm run dev"
echo ""
echo "💡 To stop development environment: ./stop-dev.sh"
