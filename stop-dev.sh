#!/bin/bash

# Stop Development Environment
# 개발환경 정리 스크립트

echo "🛑 Stopping Text-to-SQL Development Environment..."

# Stop Redis development container
echo "🐳 Stopping Redis development container..."
docker-compose -f docker-compose.dev.yml down

echo "✅ Development environment stopped"
echo ""
echo "💡 To start again: ./start-dev.sh"
