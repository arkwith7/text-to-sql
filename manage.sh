#!/bin/bash

# Text-to-SQL Project Management Script
# 개발/운영 환경 통합 관리 도구
#
# 🎯 주요 기능:
# - 개발환경과 운영환경 통합 관리
# - Docker Compose 기반 서비스 제어
# - 백엔드 개발 스크립트 실행
# - 프로젝트 전체 상태 모니터링
#
# 📋 사용법:
#   ./manage.sh [command]
#
# 🔧 지원 명령어:
#   dev             - 개발환경 시작 (backend/dev-backend.sh 실행)
#   prod start      - 운영환경 시작 (Docker Compose)
#   prod stop       - 운영환경 중지
#   prod restart    - 운영환경 재시작
#   prod logs       - 운영환경 로그 확인
#   status          - 전체 서비스 상태 확인
#   cleanup         - 중지된 컨테이너 정리
#   help            - 도움말 표시

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}🚀 Text-to-SQL Project Manager${NC}"
    echo "================================"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker가 설치되지 않았습니다."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker가 실행되지 않았습니다."
        exit 1
    fi
}

check_env_file() {
    if [ ! -f ".env" ]; then
        print_warning ".env 파일이 없습니다."
        if [ -f ".env.example" ]; then
            cp ".env.example" ".env"
            print_success ".env.example에서 .env 파일을 생성했습니다."
            print_warning "Azure OpenAI 설정을 .env 파일에서 구성해주세요."
        else
            print_error ".env.example 파일도 없습니다."
            exit 1
        fi
    fi
}

start_dev() {
    print_header
    echo "🛠️  개발환경을 시작합니다..."
    echo
    
    check_env_file
    
    # 백엔드 개발 스크립트 실행
    if [ -f "backend/dev-backend.sh" ]; then
        echo "📂 백엔드 개발 서버를 시작합니다..."
        echo "   실행 명령: cd backend && ./dev-backend.sh"
        echo
        print_success "개발환경 백엔드가 시작됩니다."
        echo
        echo "🔗 개발환경 접속 정보:"
        echo "   🌐 프론트엔드: http://localhost:3000 (수동 시작 필요)"
        echo "   🔗 백엔드 API: http://localhost:8000"
        echo "   📖 API 문서: http://localhost:8000/docs"
        echo "   🗄️ SQLite: ./app_data.db"
        echo "   📱 Redis: localhost:6381"
        echo
        echo "📝 다음 단계:"
        echo "   1. 새 터미널에서: cd backend && ./dev-backend.sh"
        echo "   2. 또 다른 터미널에서: cd frontend && npm run dev"
    else
        print_error "backend/dev-backend.sh 파일을 찾을 수 없습니다."
        exit 1
    fi
}

start_prod() {
    print_header
    echo "🐳 운영환경을 시작합니다..."
    echo
    
    check_docker
    check_env_file
    
    # Docker Compose로 운영환경 시작
    docker-compose up -d
    
    echo "⏳ 서비스가 시작될 때까지 잠시 기다립니다..."
    sleep 5
    
    show_status
}

stop_prod() {
    print_header
    echo "🛑 운영환경을 중지합니다..."
    echo
    
    check_docker
    docker-compose down
    
    print_success "운영환경이 중지되었습니다."
}

restart_prod() {
    print_header
    echo "🔄 운영환경을 재시작합니다..."
    echo
    
    stop_prod
    echo
    start_prod
}

show_logs() {
    print_header
    echo "📋 운영환경 로그를 확인합니다..."
    echo
    
    check_docker
    
    if [ -z "$3" ]; then
        echo "전체 서비스 로그:"
        docker-compose logs --tail=50 -f
    else
        echo "$3 서비스 로그:"
        docker-compose logs --tail=50 -f "$3"
    fi
}

show_status() {
    print_header
    echo "📊 현재 서비스 상태:"
    echo
    
    check_docker
    
    # Docker Compose 서비스 상태
    echo "🐳 운영환경 (Docker Compose):"
    if docker-compose ps | grep -q "Up"; then
        docker-compose ps
        echo
        
        # 서비스 접속 테스트
        echo "🔗 서비스 접속 테스트:"
        
        # Frontend
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 | grep -q "200"; then
            print_success "프론트엔드: http://localhost:8080"
        else
            print_warning "프론트엔드: http://localhost:8080 (응답 없음)"
        fi
        
        # Backend
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:8070/health | grep -q "200"; then
            print_success "백엔드: http://localhost:8070"
        else
            print_warning "백엔드: http://localhost:8070 (응답 없음)"
        fi
    else
        print_warning "운영환경이 실행되지 않았습니다."
    fi
    
    echo
    
    # 개발환경 관련 컨테이너
    echo "🛠️  개발환경 Redis:"
    if docker ps --format "{{.Names}}" | grep -q "redis-dev"; then
        print_success "redis-dev 컨테이너가 실행 중입니다."
        echo "   🔗 Redis: localhost:6379"
        echo "   🔗 RedisInsight: http://localhost:8001"
    else
        print_warning "개발환경 Redis가 실행되지 않았습니다."
    fi
    
    echo
    
    # 개발환경 백엔드 프로세스 확인
    echo "🐍 개발환경 백엔드:"
    if pgrep -f "uvicorn main:app.*--port 8000" > /dev/null; then
        print_success "개발 백엔드가 실행 중입니다 (포트 8000)"
    else
        print_warning "개발 백엔드가 실행되지 않았습니다."
    fi
    
    # 프론트엔드 개발 서버 확인
    echo
    echo "🌐 프론트엔드 개발 서버:"
    if pgrep -f "vite.*--port 3000" > /dev/null; then
        print_success "프론트엔드 개발 서버가 실행 중입니다 (포트 3000)"
    else
        print_warning "프론트엔드 개발 서버가 실행되지 않았습니다."
    fi
}

cleanup() {
    print_header
    echo "🧹 중지된 컨테이너를 정리합니다..."
    echo
    
    check_docker
    
    # 중지된 컨테이너 삭제
    docker container prune -f
    
    # 사용하지 않는 이미지 삭제
    docker image prune -f
    
    # 사용하지 않는 네트워크 삭제
    docker network prune -f
    
    print_success "정리가 완료되었습니다."
}

show_help() {
    print_header
    echo
    echo "📋 사용 가능한 명령어:"
    echo
    echo "개발환경:"
    echo "  dev              개발환경 가이드 표시"
    echo
    echo "운영환경:"
    echo "  prod start       운영환경 시작 (Docker Compose)"
    echo "  prod stop        운영환경 중지"
    echo "  prod restart     운영환경 재시작"
    echo "  prod logs [service]  로그 확인 (service: backend, frontend, redis-stack)"
    echo
    echo "유틸리티:"
    echo "  status           전체 서비스 상태 확인"
    echo "  cleanup          중지된 컨테이너 정리"
    echo "  help             이 도움말 표시"
    echo
    echo "📁 프로젝트 구조:"
    echo "  🛠️  개발환경: SQLite + Redis (포트 6381) + 백엔드 (8000) + 프론트엔드 (3000)"
    echo "  🐳 운영환경: Docker Compose (프론트엔드:8080, 백엔드:8070, Redis:6380)"
    echo
    echo "💡 일반적인 워크플로우:"
    echo "  1. 개발: ./manage.sh dev"
    echo "  2. 배포: ./manage.sh prod start"
    echo "  3. 상태 확인: ./manage.sh status"
}

# Main command processing
case "${1:-help}" in
    "dev")
        start_dev
        ;;
    "prod")
        case "${2:-help}" in
            "start")
                start_prod
                ;;
            "stop")
                stop_prod
                ;;
            "restart")
                restart_prod
                ;;
            "logs")
                show_logs "$@"
                ;;
            *)
                echo "사용법: ./manage.sh prod [start|stop|restart|logs]"
                exit 1
                ;;
        esac
        ;;
    "status")
        show_status
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        echo "알 수 없는 명령어: $1"
        echo "도움말을 보려면: ./manage.sh help"
        exit 1
        ;;
esac
