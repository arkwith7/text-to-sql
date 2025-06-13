# 로깅 시스템 가이드

Text-to-SQL AI Agent의 포괄적인 로깅 시스템 사용법과 구조에 대한 가이드입니다.

## 📊 로깅 시스템 구조

### 로그 파일 구조
```
logs/
├── app.log                 # 전체 애플리케이션 로그 (JSON 형식)
├── error.log              # 에러 전용 로그
├── api_requests.log       # API 요청/응답 로그
├── sql_queries.log        # SQL 쿼리 실행 로그
├── chat_sessions.log      # 채팅 세션 관련 로그
├── authentication.log     # 인증 관련 로그
└── report_YYYYMMDD_HHMMSS.json  # 분석 리포트
```

### 로그 포맷
모든 로그는 JSON 형식으로 저장되며 다음 필드를 포함합니다:

```json
{
    "timestamp": "2024-01-15T14:30:45.123456",
    "level": "INFO",
    "logger": "backend.api.v1.endpoints.chat",
    "message": "SQL 쿼리 실행 완료",
    "module": "chat",
    "function": "process_chat_query",
    "line": 456,
    "user_id": "user123",
    "session_id": "session456",
    "request_id": "req789",
    "sql_query": "SELECT * FROM products",
    "execution_time": 0.234
}
```

## 🔧 설정

### 환경 변수
```bash
# 로깅 레벨 설정
LOG_LEVEL=INFO

# 파일 로깅 활성화
LOG_TO_FILE=true

# 로그 파일 최대 크기 (MB)
LOG_FILE_MAX_SIZE_MB=10

# 백업 파일 개수
LOG_FILE_BACKUP_COUNT=5

# JSON 로깅 활성화
ENABLE_JSON_LOGGING=true

# 각 로그 타입 활성화/비활성화
LOG_SQL_QUERIES=true
LOG_API_REQUESTS=true
LOG_CHAT_MESSAGES=true
LOG_AUTH_EVENTS=true

# 로그 보관 기간 (일)
LOG_RETENTION_DAYS=30

# 성능 관련 설정
LOG_SLOW_QUERIES=true
SLOW_QUERY_THRESHOLD_SECONDS=1.0
LOG_PERFORMANCE_METRICS=true

# 민감한 데이터 마스킹 패턴
SENSITIVE_DATA_PATTERNS=["password", "token", "secret", "key"]
```

## 🚀 로그 관리 도구 사용법

편의 스크립트 `manage_logs.py`를 사용하여 로그를 관리할 수 있습니다:

### 기본 사용법
```bash
# 로그 파일 상태 확인
python manage_logs.py status

# 최근 24시간 로그 분석
python manage_logs.py analyze

# 상세 분석 정보 포함
python manage_logs.py analyze --hours 48 --detailed

# 실시간 로그 모니터링
python manage_logs.py tail --type app

# 특정 로그 타입 모니터링
python manage_logs.py tail --type sql --lines 100

# 종합 리포트 생성
python manage_logs.py report --hours 24 --output daily_report.json

# 오래된 로그 정리 (30일 이전)
python manage_logs.py cleanup --days 30

# 삭제 전 확인 (dry-run)
python manage_logs.py cleanup --days 30 --dry-run
```

### 고급 분석
```bash
# 특정 기간 에러 분석
python -c "
from utils.log_analyzer import LogAnalyzer
analyzer = LogAnalyzer()
errors = analyzer.analyze_errors(hours=72)
print(f'총 에러: {errors[\"total_errors\"]}개')
for module, count in errors['error_by_module'].items():
    print(f'{module}: {count}개')
"

# API 성능 분석
python -c "
from utils.log_analyzer import LogAnalyzer
analyzer = LogAnalyzer()
api_perf = analyzer.analyze_api_performance(hours=24)
print(f'평균 응답시간: {api_perf[\"avg_response_time_ms\"]:.1f}ms')
print(f'느린 요청: {len(api_perf[\"slow_requests\"])}개')
"
```

## 📈 로깅 모범 사례

### 1. 구조화된 로깅
```python
import logging
from utils.logging_config import RequestLogger, SQLLogger, ChatLogger, AuthLogger

logger = logging.getLogger(__name__)

# 기본 로깅
logger.info("작업 완료", extra={
    'user_id': user_id,
    'operation': 'create_user',
    'duration': execution_time
})

# 특화된 로거 사용
RequestLogger.log_request(
    request_id=request_id,
    method="POST",
    path="/api/v1/users",
    user_id=user_id,
    body={"email": "user@example.com"}
)

SQLLogger.log_query_execution(
    query="SELECT * FROM users WHERE id = ?",
    execution_time=0.123,
    result_count=1,
    user_id=user_id,
    success=True
)
```

### 2. 에러 로깅
```python
try:
    # 위험한 작업
    result = await some_operation()
except Exception as e:
    logger.error(
        f"작업 실패: {str(e)}",
        extra={
            'user_id': user_id,
            'operation': 'some_operation',
            'error_details': str(e)
        },
        exc_info=True  # 스택 트레이스 포함
    )
```

### 3. 성능 로깅
```python
import time

start_time = time.time()
try:
    result = await expensive_operation()
    execution_time = time.time() - start_time
    
    logger.info(
        f"작업 완료 - 시간: {execution_time:.3f}s",
        extra={
            'operation': 'expensive_operation',
            'execution_time': execution_time,
            'result_size': len(result)
        }
    )
finally:
    # 항상 실행 시간 기록
    pass
```

## 🔍 로그 분석 예시

### 1. 에러 패턴 분석
```bash
# 최근 24시간 에러 분석
python manage_logs.py analyze --hours 24

# 결과 예시:
# 📈 에러 분석:
#   - 총 에러: 12개
#   - 모듈별 에러:
#     * sql_agent: 5개
#     * auth_service: 3개
#     * chat: 4개
```

### 2. 성능 모니터링
```bash
# API 성능 분석
python manage_logs.py analyze --detailed

# 결과 예시:
# 🚀 API 성능 분석:
#   - 총 요청: 1,234개
#   - 평균 응답시간: 145.3ms
#   - 최대 응답시간: 2,456ms
#   - 느린 요청: 8개
#
# ⏱️ 느린 API 요청:
#   - /api/v1/chat/sessions/123/query: 2456ms
#   - /api/v1/auth/login: 1892ms
```

### 3. 사용자 활동 분석
```python
from utils.log_analyzer import LogAnalyzer

analyzer = LogAnalyzer()
user_activity = analyzer.analyze_user_activity(hours=24)

print(f"활성 사용자: {user_activity['total_active_users']}명")
print(f"총 로그인: {user_activity['total_logins']}회")
print(f"총 채팅 메시지: {user_activity['total_chat_messages']}개")

# 가장 활성적인 사용자 확인
for user_id, activity in user_activity['top_active_users'].items():
    print(f"사용자 {user_id}: {activity['chat_messages']}개 메시지, {activity['login_count']}회 로그인")
```

## 🔧 문제 해결

### 로그 파일이 생성되지 않는 경우
1. `logs/` 디렉토리 존재 확인
2. 디렉토리 쓰기 권한 확인
3. `LOG_TO_FILE=true` 설정 확인

### 로그 파일이 너무 큰 경우
1. `LOG_FILE_MAX_SIZE_MB` 값 조정
2. `LOG_FILE_BACKUP_COUNT` 증가
3. 자동 정리 스케줄 설정:
   ```bash
   # crontab에 추가 (매일 자정 30일 이전 로그 정리)
   0 0 * * * cd /path/to/backend && python manage_logs.py cleanup --days 30
   ```

### 성능 영향 최소화
1. 프로덕션에서는 `LOG_LEVEL=INFO` 또는 `WARNING` 사용
2. `DEBUG_SQL_QUERIES=false` 설정
3. `LOG_REQUEST_BODY=false` (민감한 정보 포함 시)

## 📊 대시보드 및 모니터링

### 로그 기반 대시보드 생성
```python
# 일일 리포트 생성 예시
from utils.log_analyzer import LogAnalyzer
import json

analyzer = LogAnalyzer()
daily_report = analyzer.generate_report(hours=24)

# 주요 메트릭 추출
metrics = {
    'total_errors': daily_report['error_analysis']['total_errors'],
    'avg_response_time': daily_report['api_performance']['avg_response_time_ms'],
    'total_queries': daily_report['sql_analysis']['total_queries'],
    'active_users': daily_report['user_activity']['total_active_users']
}

print(json.dumps(metrics, indent=2))
```

### 알림 설정
```python
# 에러 임계값 초과 시 알림
def check_error_threshold():
    analyzer = LogAnalyzer()
    errors = analyzer.analyze_errors(hours=1)
    
    if errors['total_errors'] > 10:  # 1시간에 10개 이상 에러
        send_alert(f"높은 에러율 감지: {errors['total_errors']}개/시간")
```

## 🔐 보안 고려사항

1. **민감한 데이터 마스킹**: 비밀번호, 토큰 등 자동 마스킹
2. **로그 파일 권한**: 읽기 전용으로 설정
3. **로그 전송**: 필요시 TLS로 암호화된 연결 사용
4. **보관 기간**: 규정에 따른 적절한 보관 기간 설정

## 📝 로그 분석 자동화

### 주간 리포트 생성 스크립트
```bash
#!/bin/bash
# weekly_report.sh

cd /path/to/backend

# 주간 리포트 생성
python manage_logs.py report --hours 168 --output "reports/weekly_$(date +%Y%m%d).json"

# 이전 주와 비교
python -c "
import json
from datetime import datetime, timedelta

# 현재 주간 리포트 로드
with open('reports/weekly_$(date +%Y%m%d).json') as f:
    current = json.load(f)

print(f'이번 주 에러: {current[\"error_analysis\"][\"total_errors\"]}개')
print(f'이번 주 평균 응답시간: {current[\"api_performance\"][\"avg_response_time_ms\"]:.1f}ms')
"
```

이 로깅 시스템을 통해 Text-to-SQL AI Agent의 모든 활동을 체계적으로 추적하고 분석할 수 있습니다. 