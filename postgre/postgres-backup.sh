#!/bin/bash
# PostgreSQL 백업 및 복구 자동화 스크립트
# 매일 자동 백업을 통해 데이터 손실 방지

BACKUP_DIR="/home/wjadmin/Dev/text-to-sql/backups"
POSTGRES_CONTAINER_NAME="northwind-postgres"
DB_USER="postgres"
DB_NAME="northwind"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 백업 디렉토리 생성
mkdir -p $BACKUP_DIR

# 백업 함수
backup_database() {
    echo "🗄️  PostgreSQL 백업 시작..."
    
    # 컨테이너가 실행 중인지 확인
    if ! docker ps --format "{{.Names}}" | grep -q "^${POSTGRES_CONTAINER_NAME}$"; then
        echo "❌ PostgreSQL 컨테이너가 실행되지 않음"
        return 1
    fi
    
    # 백업 실행
    if docker exec $POSTGRES_CONTAINER_NAME pg_dump -U $DB_USER -d $DB_NAME > "$BACKUP_DIR/northwind_backup_$TIMESTAMP.sql"; then
        echo "✅ 백업 완료: northwind_backup_$TIMESTAMP.sql"
        
        # 백업 파일 압축
        gzip "$BACKUP_DIR/northwind_backup_$TIMESTAMP.sql"
        echo "✅ 백업 파일 압축 완료"
        
        # 7일 이상 된 백업 파일 삭제
        find $BACKUP_DIR -name "northwind_backup_*.sql.gz" -mtime +7 -delete
        echo "🧹 오래된 백업 파일 정리 완료"
        
        return 0
    else
        echo "❌ 백업 실패"
        return 1
    fi
}

# 복구 함수
restore_database() {
    local backup_file=$1
    
    if [ -z "$backup_file" ]; then
        echo "사용법: $0 restore <백업파일>"
        echo "사용 가능한 백업 파일:"
        ls -la $BACKUP_DIR/northwind_backup_*.sql.gz 2>/dev/null || echo "백업 파일이 없습니다"
        return 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        echo "❌ 백업 파일을 찾을 수 없습니다: $backup_file"
        return 1
    fi
    
    echo "🔄 데이터베이스 복구 시작..."
    
    # 압축 파일이면 압축 해제
    if [[ "$backup_file" == *.gz ]]; then
        temp_file="/tmp/northwind_restore_temp.sql"
        gunzip -c "$backup_file" > "$temp_file"
        backup_file="$temp_file"
    fi
    
    # 컨테이너에 백업 파일 복사
    if docker cp "$backup_file" $POSTGRES_CONTAINER_NAME:/restore.sql; then
        # 기존 데이터베이스 삭제 및 재생성
        docker exec $POSTGRES_CONTAINER_NAME psql -U $DB_USER -c "DROP DATABASE IF EXISTS $DB_NAME;"
        docker exec $POSTGRES_CONTAINER_NAME psql -U $DB_USER -c "CREATE DATABASE $DB_NAME;"
        
        # 백업 데이터 복구
        if docker exec $POSTGRES_CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -f /restore.sql; then
            echo "✅ 데이터베이스 복구 완료"
            
            # 임시 파일 정리
            [ -f "/tmp/northwind_restore_temp.sql" ] && rm "/tmp/northwind_restore_temp.sql"
            docker exec $POSTGRES_CONTAINER_NAME rm /restore.sql
            
            return 0
        else
            echo "❌ 데이터베이스 복구 실패"
            return 1
        fi
    else
        echo "❌ 백업 파일을 컨테이너로 복사 실패"
        return 1
    fi
}

# 메인 실행
case "$1" in
    "backup")
        backup_database
        ;;
    "restore")
        restore_database "$2"
        ;;
    "auto")
        # 자동 백업 (cron 작업용)
        backup_database
        # 추가로 헬스체크도 수행
        /home/wjadmin/Dev/text-to-sql/postgre/postgres-health-check.sh
        ;;
    *)
        echo "사용법: $0 {backup|restore|auto}"
        echo ""
        echo "commands:"
        echo "  backup  - 현재 데이터베이스를 백업합니다"
        echo "  restore - 백업 파일로부터 데이터베이스를 복구합니다"
        echo "  auto    - 자동 백업 (cron 작업용)"
        echo ""
        echo "예시:"
        echo "  $0 backup"
        echo "  $0 restore $BACKUP_DIR/northwind_backup_20241227_120000.sql.gz"
        exit 1
        ;;
esac
