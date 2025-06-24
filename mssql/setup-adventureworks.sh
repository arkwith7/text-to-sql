#!/bin/bash

# MS SQL Server AdventureWorks 샘플 데이터베이스 설정 스크립트
# chriseaton/docker-adventureworks 이미지 사용
#
# 🎯 기능:
# - AdventureWorks 샘플 데이터베이스가 미리 로드된 MS SQL Server 실행
# - 별도 데이터베이스 설정 없이 바로 사용 가능
# - Text-to-SQL 분석 대상 데이터베이스로 활용

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="mssql-adventureworks"
DB_PASSWORD="Adventure123!"
HOST_PORT="1433"
CONTAINER_PORT="1433"
DOCKER_IMAGE="chriseaton/adventureworks:latest"

# Helper functions
print_header() {
    echo -e "${BLUE}🗄️  MS SQL Server AdventureWorks Setup${NC}"
    echo "========================================="
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

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
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

check_existing_container() {
    if docker ps -a --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        return 0  # Container exists
    else
        return 1  # Container doesn't exist
    fi
}

check_running_container() {
    if docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        return 0  # Container is running
    else
        return 1  # Container is not running
    fi
}

start_mssql() {
    print_header
    echo "🚀 MS SQL Server AdventureWorks를 시작합니다..."
    echo

    check_docker

    if check_existing_container; then
        if check_running_container; then
            print_warning "MS SQL Server AdventureWorks가 이미 실행 중입니다."
            show_connection_info
            return
        else
            print_info "기존 컨테이너를 시작합니다..."
            docker start ${CONTAINER_NAME}
        fi
    else
        print_info "새로운 MS SQL Server AdventureWorks 컨테이너를 생성합니다..."
        echo "🔧 설정:"
        echo "   - 이미지: ${DOCKER_IMAGE}"
        echo "   - 컨테이너: ${CONTAINER_NAME}"
        echo "   - 포트: ${HOST_PORT}:${CONTAINER_PORT}"
        echo "   - SA 패스워드: ${DB_PASSWORD}"
        echo

        docker run -d \
            --name ${CONTAINER_NAME} \
            -p ${HOST_PORT}:${CONTAINER_PORT} \
            -e 'ACCEPT_EULA=Y' \
            -e "MSSQL_SA_PASSWORD=${DB_PASSWORD}" \
            ${DOCKER_IMAGE}
    fi

    echo "⏳ MS SQL Server가 시작될 때까지 기다립니다..."
    sleep 10

    # Health check
    echo "🔍 서버 상태를 확인합니다..."
    for i in {1..12}; do
        if docker exec ${CONTAINER_NAME} /opt/mssql-tools/bin/sqlcmd \
            -S localhost -U sa -P "${DB_PASSWORD}" \
            -Q "SELECT @@VERSION" &> /dev/null; then
            print_success "MS SQL Server가 성공적으로 시작되었습니다!"
            break
        fi
        
        if [ $i -eq 12 ]; then
            print_error "MS SQL Server 시작 시간이 초과되었습니다."
            exit 1
        fi
        
        echo "   시도 $i/12 - 5초 후 재시도..."
        sleep 5
    done

    show_connection_info
}

stop_mssql() {
    print_header
    echo "🛑 MS SQL Server AdventureWorks를 중지합니다..."
    echo

    if check_running_container; then
        docker stop ${CONTAINER_NAME}
        print_success "MS SQL Server AdventureWorks가 중지되었습니다."
    else
        print_warning "MS SQL Server AdventureWorks가 실행되지 않았습니다."
    fi
}

remove_mssql() {
    print_header
    echo "🗑️  MS SQL Server AdventureWorks 컨테이너를 제거합니다..."
    echo

    if check_existing_container; then
        if check_running_container; then
            print_info "실행 중인 컨테이너를 먼저 중지합니다..."
            docker stop ${CONTAINER_NAME}
        fi
        
        docker rm ${CONTAINER_NAME}
        print_success "MS SQL Server AdventureWorks 컨테이너가 제거되었습니다."
    else
        print_warning "MS SQL Server AdventureWorks 컨테이너가 존재하지 않습니다."
    fi
}

restart_mssql() {
    print_header
    echo "🔄 MS SQL Server AdventureWorks를 재시작합니다..."
    echo

    stop_mssql
    echo
    start_mssql
}

show_status() {
    print_header
    echo "📊 MS SQL Server AdventureWorks 상태:"
    echo

    if check_running_container; then
        print_success "컨테이너가 실행 중입니다."
        echo
        echo "컨테이너 상세 정보:"
        docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
        echo
        show_connection_info
    elif check_existing_container; then
        print_warning "컨테이너가 중지되어 있습니다."
        echo
        echo "컨테이너 정보:"
        docker ps -a --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
    else
        print_warning "MS SQL Server AdventureWorks 컨테이너가 없습니다."
        print_info "다음 명령으로 시작할 수 있습니다: $0 start"
    fi
}

show_connection_info() {
    echo "🔗 연결 정보:"
    echo "   📍 서버: localhost,${HOST_PORT}"
    echo "   👤 사용자: sa"
    echo "   🔑 패스워드: ${DB_PASSWORD}"
    echo "   🗄️  데이터베이스: AdventureWorks, AdventureWorksDW, AdventureWorksLT"
    echo
    echo "💡 연결 테스트:"
    echo "   sqlcmd -S localhost,${HOST_PORT} -U sa -P '${DB_PASSWORD}'"
    echo
    echo "🔍 샘플 쿼리:"
    echo "   USE AdventureWorks;"
    echo "   SELECT TOP 10 * FROM Person.Person;"
    echo
    echo "🌐 Text-to-SQL 앱에서 사용할 연결 정보:"
    echo "   호스트: localhost"
    echo "   포트: ${HOST_PORT}"
    echo "   데이터베이스: AdventureWorks (또는 AdventureWorksDW, AdventureWorksLT)"
    echo "   사용자명: sa"
    echo "   패스워드: ${DB_PASSWORD}"
}

show_logs() {
    print_header
    echo "📋 MS SQL Server AdventureWorks 로그:"
    echo

    if check_existing_container; then
        docker logs ${CONTAINER_NAME}
    else
        print_warning "MS SQL Server AdventureWorks 컨테이너가 없습니다."
    fi
}

show_help() {
    print_header
    echo
    echo "📋 사용 가능한 명령어:"
    echo
    echo "  start      MS SQL Server AdventureWorks 시작"
    echo "  stop       MS SQL Server AdventureWorks 중지"
    echo "  restart    MS SQL Server AdventureWorks 재시작"
    echo "  remove     MS SQL Server AdventureWorks 컨테이너 제거"
    echo "  status     현재 상태 확인"
    echo "  logs       로그 확인"
    echo "  help       이 도움말 표시"
    echo
    echo "🗄️  AdventureWorks 데이터베이스 정보:"
    echo "   • AdventureWorks: 표준 OLTP 샘플 데이터베이스"
    echo "   • AdventureWorksDW: 데이터 웨어하우스 샘플"
    echo "   • AdventureWorksLT: 경량화된 샘플 데이터베이스"
    echo
    echo "📝 사용 예시:"
    echo "   $0 start          # 서버 시작"
    echo "   $0 status         # 상태 확인"
    echo "   $0 stop           # 서버 중지"
}

# Main command processing
case "${1:-help}" in
    "start")
        start_mssql
        ;;
    "stop")
        stop_mssql
        ;;
    "restart")
        restart_mssql
        ;;
    "remove")
        remove_mssql
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        echo "알 수 없는 명령어: $1"
        echo "도움말을 보려면: $0 help"
        exit 1
        ;;
esac
