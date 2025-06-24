# 시스템 통제권 기반 관리자 기능 구현 계획

## 개요

### 목적
한국어 자연어 질의를 통한 Text-to-SQL 서비스의 사용자 만족도 향상을 위해 시스템 통제권 관점에서 5대 핵심 관리자 기능을 사용자 기능과 분리하여 구현합니다.

### 범위
현재 시스템에서 관리자가 통제해야 할 5대 핵심 기능:

1. **시스템 프롬프트 관리**
2. **분석대상 데이터베이스 접속정보 관리**
3. **분석대상 데이터베이스 스키마 메타데이터 관리** (한국어 명칭/설명 포함)
4. **사용자정보 및 권한 관리**
5. **LLM(거대언어모델) 접속정보 관리**

## 현재 시스템 분석

### 기존 기반 시설
✅ **이미 구축된 요소들:**
- RBAC 시스템 (`UserRole.ADMIN`, `UserRole.ANALYST`)
- 관리자 엔드포인트 (`/api/v1/admin/*`)
- 데이터베이스 모델 (`SystemConfig`, `DatabaseConnection`, `DatabaseSchema`)
- 토큰 사용량 추적 (`QueryAnalytics`)
- 감사 로그 시스템 (`AuditLog`)

### 확장이 필요한 영역
🔄 **개선/확장 필요:**
- 시스템 프롬프트: 현재 하드코딩 → 동적 관리
- LLM 설정: `.env` 파일 → 데이터베이스 관리
- 스키마 정보: 영문만 → 한국어 명칭/설명 추가
- DB 접속정보: 사용자별 → 중앙 관리 + 권한 할당

## 5대 관리자 기능별 구현 계획

### 1. 시스템 프롬프트 관리

**현재 상태**: `backend/core/agents/langchain_agent.py`에 하드코딩
```python
self.system_prompt = """
당신은 SQL 쿼리 생성 전문가입니다...
"""
```

**목표**: 동적 관리 및 버전 제어
- 웹 인터페이스를 통한 프롬프트 편집
- 버전 관리 및 롤백 기능
- A/B 테스트를 위한 다중 프롬프트 지원

**구현 방법**:
```python
# SystemConfig 테이블 활용
system_prompt = await SystemConfigService.get_config("SYSTEM_PROMPT_MAIN")
```

### 2. 분석대상 데이터베이스 접속정보 관리

**현재 상태**: `DatabaseConnection` 모델 존재 (사용자별 개별 관리)

**목표**: 관리자 중앙 관리 + 사용자별 접근 권한 할당
- 관리자가 승인된 DB만 사용자에게 제공
- 연결 풀 관리 및 성능 최적화
- 보안 강화 (접속 정보 암호화)

**구현 방법**:
```python
# 새로운 ManagedDatabaseConnection 모델
class ManagedDatabaseConnection:
    is_managed: bool = True  # 관리자 관리 여부
    assigned_users: List[str]  # 할당된 사용자
    connection_limits: dict  # 연결 제한
```

### 3. 스키마 메타데이터 관리

**현재 상태**: `DatabaseSchema` 모델에 기본 스키마 정보만 저장

**목표**: 한국어 친화적 스키마 정보 제공
- 테이블/컬럼 한국어 명칭
- 비즈니스 컨텍스트 설명
- LLM 기반 자동 번역 기능

**구현 방법**:
```python
# DatabaseSchema 확장
class SchemaMetadata:
    table_korean_name: str
    table_description: str
    column_korean_name: str
    column_business_meaning: str
    sample_values: List[str]
```

### 4. 사용자정보 및 권한 관리

**현재 상태**: 80% 완성 (기본 RBAC 구현됨)

**목표**: 세분화된 권한 체계
- 테이블별 접근 권한
- 일일/월간 토큰 사용 한도
- 쿼리 복잡도 제한

**구현 방법**:
```python
# User 테이블 확장
ALTER TABLE users ADD COLUMN daily_token_limit INTEGER DEFAULT 10000;
ALTER TABLE users ADD COLUMN allowed_tables JSON;
```

### 5. LLM 접속정보 관리

**현재 상태**: `.env` 파일에서 관리
```
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
```

**목표**: 동적 관리 및 다중 모델 지원
- 여러 LLM 프로바이더 동시 관리
- 모델별 비용 추적
- 자동 fallback 기능

**구현 방법**:
```python
# 새로운 LLMConnection 테이블
class LLMConnection:
    provider: str  # 'azure_openai', 'openai', 'anthropic'
    model_configs: dict
    cost_per_token: float
    is_active: bool
```

## 단계별 구현 로드맵

### Phase 1: 기반 확장 (2-3주)
**목표**: 기존 시스템 확장 및 기본 관리자 기능 구현

**작업 내용**:
1. **데이터베이스 스키마 확장**
   - `system_prompts` 테이블 생성
   - `llm_connections` 테이블 생성
   - `user_permissions` 테이블 생성

2. **기본 API 구현**
   ```python
   # 시스템 프롬프트 API
   POST /api/v1/admin/system-prompts
   GET /api/v1/admin/system-prompts
   PUT /api/v1/admin/system-prompts/{id}
   
   # LLM 연결 API
   POST /api/v1/admin/llm-connections
   GET /api/v1/admin/llm-connections
   ```

3. **권한 시스템 강화**
   - 세분화된 RBAC 구현
   - 관리자 작업 감사 로그

**성공 지표**:
- 시스템 프롬프트 웹에서 수정 가능
- LLM 설정 동적 변경 가능
- 모든 관리자 작업 로그 기록

### Phase 2: 스키마 메타데이터 관리 (3-4주)
**목표**: 한국어 친화적 스키마 정보 시스템 구축

**작업 내용**:
1. **스키마 메타데이터 확장**
   ```sql
   CREATE TABLE schema_metadata (
       table_korean_name VARCHAR(200),
       table_description TEXT,
       column_korean_name VARCHAR(200),
       column_business_meaning TEXT,
       sample_values JSON
   );
   ```

2. **LLM 기반 자동 번역**
   ```python
   async def auto_generate_korean_names(schema_info):
       prompt = f"다음 테이블과 컬럼에 적절한 한국어 명칭을 제안해주세요: {schema_info}"
       korean_names = await llm_service.generate(prompt)
       return korean_names
   ```

3. **관리자 UI 개발**
   - 스키마 메타데이터 편집 인터페이스
   - 일괄 번역 기능
   - 미리보기 및 검증 기능

**성공 지표**:
- 모든 테이블/컬럼에 한국어 명칭 설정 가능
- 사용자 쿼리 시 한국어 스키마 정보 활용
- 쿼리 성공률 15-20% 향상

### Phase 3: 고급 관리 기능 (2-3주)
**목표**: 통합 관리 대시보드 및 고급 기능 구현

**작업 내용**:
1. **중앙 DB 관리 시스템**
   ```python
   # 관리형 DB 연결
   class ManagedDatabaseService:
       async def assign_database_to_users(db_id, user_ids)
       async def set_connection_limits(db_id, limits)
       async def monitor_connection_usage()
   ```

2. **통합 관리 대시보드**
   ```vue
   <AdminDashboard>
     <SystemMetrics />
     <UserActivity />
     <CostAnalytics />
     <SecurityAlerts />
   </AdminDashboard>
   ```

3. **모니터링 및 알림**
   - 실시간 시스템 상태 모니터링
   - 비용 임계값 알림
   - 보안 이벤트 감지

**성공 지표**:
- 모든 관리자 기능 통합 대시보드에서 관리
- 실시간 모니터링 및 알림 시스템 동작
- 관리자 업무 효율성 50% 향상

## 기대 효과

### 즉시 효과 (Phase 1 완료 시)
- **보안 강화**: 민감한 설정 정보의 안전한 관리
- **운영 효율성**: 시스템 설정 변경 시간 80% 단축
- **유지보수성**: 코드 수정 없이 설정 변경 가능

### 중기 효과 (Phase 2 완료 시)
- **사용자 만족도**: 한국어 스키마 정보로 쿼리 성공률 향상
- **서비스 품질**: 더 정확하고 직관적인 쿼리 결과
- **확장성**: 새로운 데이터베이스 추가 시간 70% 단축

### 장기 효과 (Phase 3 완료 시)
- **비용 최적화**: LLM 사용량 제어로 월 운영비 10-15% 절감
- **확장성**: 새로운 LLM 모델 추가 용이성
- **경쟁력**: 한국어 Text-to-SQL 서비스의 차별화 요소 확보

## 위험 요소 및 대응 방안

### 주요 위험 요소
1. **기존 기능 호환성**: 현재 동작하는 기능에 영향
2. **데이터 마이그레이션**: 기존 데이터 손실 위험
3. **성능 저하**: 새로운 기능으로 인한 시스템 부하
4. **복잡성 증가**: 관리해야 할 설정 항목 증가

### 대응 방안
1. **점진적 마이그레이션**
   - 기존 기능 유지하며 단계적 전환
   - Feature Flag 활용으로 안전한 배포

2. **철저한 테스트**
   - 각 단계별 회귀 테스트
   - 부하 테스트 및 성능 검증

3. **백업 및 롤백 계획**
   - 모든 설정 변경 사항 백업
   - 1-click 롤백 기능 구현

4. **문서화 및 교육**
   - 상세한 운영 가이드 작성
   - 관리자 교육 프로그램 운영

## 성공 측정 지표

### 기술적 지표
- 시스템 설정 변경 시간: 기존 대비 80% 단축
- 쿼리 성공률: 15-20% 향상
- 시스템 가용성: 99.9% 이상 유지

### 비즈니스 지표
- 사용자 만족도: NPS 점수 20% 향상
- 운영 효율성: 관리자 업무 시간 50% 단축
- 비용 절감: LLM 비용 10-15% 절감

### 품질 지표
- 버그 발생률: 기존 대비 30% 감소
- 보안 사고: 0건 유지
- 시스템 응답 시간: 기존 수준 유지

## 결론

제안된 5대 관리자 기능 구현은 현재 시스템의 자연스러운 진화 단계로, 다음과 같은 이유로 **매우 실현 가능하고 가치 있는 투자**입니다:

### 실현 가능성
- 기존 시스템의 견고한 기반 활용
- 단계적 구현으로 리스크 최소화
- 검증된 기술 스택 사용

### 전략적 가치
- 한국어 Text-to-SQL 서비스의 차별화
- 운영 효율성 및 보안 강화
- 미래 확장성 확보

### ROI 예상
- 개발 투자: 7-10주 (개발자 2-3명)
- 예상 효과: 운영비 절감 + 사용자 만족도 향상 + 시장 경쟁력 확보

이는 **확장이 아닌 진화**로, Text-to-SQL 서비스를 한 단계 발전시킬 수 있는 핵심 프로젝트입니다.
