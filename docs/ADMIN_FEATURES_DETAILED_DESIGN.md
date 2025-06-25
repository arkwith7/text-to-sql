# 관리자 기능 상세 설계서

## Text-to-SQL 시스템 통제권 기반 관리자 기능 설계 및 구현 가이드

---

## 1. 개요

### 1.1 목적

한국어 자연어 질의를 통한 Text-to-SQL 서비스의 사용자 만족도 향상을 위해 시스템 통제권 관점에서 5대 핵심 관리자 기능을 사용자 기능과 분리하여 구현합니다.

### 1.2 범위

- 시스템 프롬프트 관리
- 분석대상 데이터베이스 접속정보 관리
- 분석대상 데이터베이스 스키마 메타데이터 관리
- 사용자정보 및 권한 관리
- LLM(거대언어모델) 접속정보 관리

### 1.3 설계 원칙

- **보안 우선**: 민감한 정보의 안전한 관리
- **확장성**: 새로운 기능 추가 용이성
- **사용성**: 직관적인 관리자 인터페이스
- **호환성**: 기존 시스템과의 원활한 통합

---

## 2. 시스템 아키텍처

### 2.1 전체 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    관리자 기능 계층                          │
├─────────────────────────────────────────────────────────────┤
│  프롬프트 관리  │  DB 관리  │  스키마 관리  │  사용자 관리  │ LLM 관리  │
├─────────────────────────────────────────────────────────────┤
│                     API 인증 및 권한 계층                    │
├─────────────────────────────────────────────────────────────┤
│                       데이터 계층                           │
├─────────────────────────────────────────────────────────────┤
│                     사용자 기능 계층                         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 관리자 기능 분리 구조

```
관리자 전용:
- /api/v1/admin/* (관리자 권한 필요)
- AdminDashboard (프론트엔드)
- 시스템 설정 관리

사용자 기능:
- /api/v1/user/* (일반 사용자)
- UserDashboard (프론트엔드) 
- 쿼리 실행 및 결과 조회
```

---

## 3. 데이터베이스 설계

### 3.1 관리자 기능 테이블 구조

#### 3.1.1 시스템 프롬프트 관리 (system_prompts)

```sql
CREATE TABLE system_prompts (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    prompt_name VARCHAR(100) NOT NULL UNIQUE,
    prompt_content TEXT NOT NULL,
    prompt_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    language VARCHAR(10) NOT NULL DEFAULT 'ko',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    description TEXT,
    variables JSON,  -- 프롬프트 내 변수 정의
    created_by VARCHAR(36) NOT NULL,
    updated_by VARCHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (updated_by) REFERENCES users(id),
    INDEX idx_prompt_active (is_active),
    INDEX idx_prompt_name (prompt_name)
);
```

#### 3.1.2 스키마 메타데이터 확장 (schema_metadata)

```sql
CREATE TABLE schema_metadata (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    connection_id VARCHAR(36) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    table_korean_name VARCHAR(200),
    table_description TEXT,
    table_business_context TEXT,
    column_name VARCHAR(100),
    column_korean_name VARCHAR(200),
    column_description TEXT,
    column_business_meaning TEXT,
    data_type VARCHAR(50),
    is_sensitive BOOLEAN DEFAULT FALSE,
    sample_values JSON,  -- 예시 값들
    validation_rules JSON,  -- 데이터 검증 규칙
    created_by VARCHAR(36) NOT NULL,
    updated_by VARCHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (connection_id) REFERENCES database_connections(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (updated_by) REFERENCES users(id),
    UNIQUE KEY unique_schema_column (connection_id, table_name, column_name),
    INDEX idx_connection_table (connection_id, table_name),
    INDEX idx_korean_names (table_korean_name, column_korean_name)
);
```

#### 3.1.3 LLM 접속정보 관리 (llm_connections)

```sql
CREATE TABLE llm_connections (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    connection_name VARCHAR(100) NOT NULL UNIQUE,
    provider VARCHAR(50) NOT NULL,  -- 'azure_openai', 'openai', 'anthropic'
    model_name VARCHAR(100) NOT NULL,
    endpoint_url VARCHAR(500),
    api_key_encrypted TEXT NOT NULL,
    api_version VARCHAR(20),
    deployment_name VARCHAR(100),
    max_tokens INTEGER DEFAULT 4000,
    temperature FLOAT DEFAULT 0.0,
    cost_per_1k_prompt_tokens DECIMAL(10,6),
    cost_per_1k_completion_tokens DECIMAL(10,6),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    fallback_models JSON,  -- 대체 모델 목록
    rate_limits JSON,  -- 속도 제한 설정
    created_by VARCHAR(36) NOT NULL,
    updated_by VARCHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (updated_by) REFERENCES users(id),
    INDEX idx_provider_model (provider, model_name),
    INDEX idx_active_default (is_active, is_default)
);
```

#### 3.1.4 사용자 권한 확장 (user_permissions)

```sql
CREATE TABLE user_permissions (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36) NOT NULL,
    permission_type VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),  -- 'database', 'table', 'schema'
    resource_id VARCHAR(36),
    permission_value JSON,  -- 세부 권한 설정
    granted_by VARCHAR(36) NOT NULL,
    expires_at TIMESTAMP NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES users(id),
    UNIQUE KEY unique_user_permission (user_id, permission_type, resource_type, resource_id),
    INDEX idx_user_permissions (user_id, is_active),
    INDEX idx_resource_permissions (resource_type, resource_id)
);
```

#### 3.1.5 관리자 중앙 DB 접속정보 (managed_database_connections)

```sql
CREATE TABLE managed_database_connections (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    connection_name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    db_type VARCHAR(50) NOT NULL DEFAULT 'postgresql',
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    database_name VARCHAR(100) NOT NULL,
    username VARCHAR(100) NOT NULL,
    password_encrypted TEXT NOT NULL,
    connection_string_template TEXT,
    pool_settings JSON,  -- 연결 풀 설정
    ssl_settings JSON,   -- SSL 설정
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_public BOOLEAN NOT NULL DEFAULT FALSE,  -- 모든 사용자 접근 가능
    allowed_users JSON,  -- 허용된 사용자 목록
    connection_limits JSON,  -- 연결 제한 설정
    created_by VARCHAR(36) NOT NULL,
    updated_by VARCHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (updated_by) REFERENCES users(id),
    INDEX idx_connection_active (is_active),
    INDEX idx_connection_public (is_public)
);
```

### 3.2 기존 테이블 확장

#### 3.2.1 users 테이블 확장

```sql
ALTER TABLE users 
ADD COLUMN daily_token_limit INTEGER DEFAULT 10000,
ADD COLUMN monthly_token_limit INTEGER DEFAULT 300000,
ADD COLUMN query_complexity_limit INTEGER DEFAULT 5,  -- 1-10 scale
ADD COLUMN allowed_functions JSON,  -- 허용된 기능 목록
ADD COLUMN ui_preferences JSON,  -- UI 설정
ADD COLUMN timezone VARCHAR(50) DEFAULT 'Asia/Seoul';
```

#### 3.2.2 system_config 테이블 활용 확장

기존 system_config 테이블을 활용하여 다음 설정들을 관리:
- `SYSTEM_PROMPT_MAIN`: 메인 시스템 프롬프트
- `LLM_DEFAULT_MODEL`: 기본 LLM 모델
- `TOKEN_USAGE_LIMITS`: 토큰 사용 제한 설정
- `SCHEMA_AUTO_UPDATE`: 스키마 자동 업데이트 설정

---

## 4. API 설계

### 4.1 관리자 API 엔드포인트

#### 4.1.1 시스템 프롬프트 관리 API

```python
# /api/v1/admin/system-prompts
@router.get("/system-prompts")
@requires_role(UserRole.ADMIN)
async def get_system_prompts(
    active_only: bool = True,
    limit: int = 50,
    offset: int = 0
) -> List[SystemPromptResponse]:
    """시스템 프롬프트 목록 조회"""

@router.post("/system-prompts")
@requires_role(UserRole.ADMIN) 
async def create_system_prompt(
    prompt: SystemPromptCreate
) -> SystemPromptResponse:
    """새 시스템 프롬프트 생성"""

@router.put("/system-prompts/{prompt_id}")
@requires_role(UserRole.ADMIN)
async def update_system_prompt(
    prompt_id: str,
    prompt: SystemPromptUpdate
) -> SystemPromptResponse:
    """시스템 프롬프트 수정"""

@router.post("/system-prompts/{prompt_id}/activate")
@requires_role(UserRole.ADMIN)
async def activate_system_prompt(prompt_id: str):
    """시스템 프롬프트 활성화"""
```

#### 4.1.2 스키마 메타데이터 관리 API

```python
# /api/v1/admin/schema-metadata
@router.get("/schema-metadata")
@requires_role(UserRole.ADMIN)
async def get_schema_metadata(
    connection_id: Optional[str] = None,
    table_name: Optional[str] = None
) -> List[SchemaMetadataResponse]:
    """스키마 메타데이터 조회"""

@router.post("/schema-metadata/bulk-update")
@requires_role(UserRole.ADMIN)
async def bulk_update_schema_metadata(
    metadata_list: List[SchemaMetadataUpdate]
) -> BulkUpdateResponse:
    """스키마 메타데이터 일괄 업데이트"""

@router.post("/schema-metadata/auto-generate")
@requires_role(UserRole.ADMIN)
async def auto_generate_korean_names(
    connection_id: str,
    use_llm: bool = True
) -> GenerationResponse:
    """LLM을 활용한 한국어 명칭 자동 생성"""
```

#### 4.1.3 LLM 접속정보 관리 API

```python
# /api/v1/admin/llm-connections
@router.get("/llm-connections")
@requires_role(UserRole.ADMIN)
async def get_llm_connections() -> List[LLMConnectionResponse]:
    """LLM 접속정보 목록 조회"""

@router.post("/llm-connections")
@requires_role(UserRole.ADMIN)
async def create_llm_connection(
    connection: LLMConnectionCreate
) -> LLMConnectionResponse:
    """새 LLM 접속정보 생성"""

@router.post("/llm-connections/{connection_id}/test")
@requires_role(UserRole.ADMIN)
async def test_llm_connection(
    connection_id: str
) -> ConnectionTestResponse:
    """LLM 연결 테스트"""
```

#### 4.1.4 관리형 DB 접속정보 API

```python
# /api/v1/admin/managed-databases
@router.get("/managed-databases")
@requires_role(UserRole.ADMIN)
async def get_managed_databases() -> List[ManagedDatabaseResponse]:
    """관리형 데이터베이스 목록 조회"""

@router.post("/managed-databases")
@requires_role(UserRole.ADMIN)
async def create_managed_database(
    db_config: ManagedDatabaseCreate
) -> ManagedDatabaseResponse:
    """새 관리형 데이터베이스 생성"""

@router.post("/managed-databases/{db_id}/assign-users")
@requires_role(UserRole.ADMIN)
async def assign_users_to_database(
    db_id: str,
    user_assignments: UserAssignmentRequest
) -> AssignmentResponse:
    """사용자에게 데이터베이스 접근 권한 할당"""
```

### 4.2 Pydantic 모델

#### 4.2.1 시스템 프롬프트 모델

```python
class SystemPromptCreate(BaseModel):
    prompt_name: str = Field(..., max_length=100)
    prompt_content: str = Field(..., min_length=10)
    prompt_version: str = Field(default="1.0", max_length=20)
    language: str = Field(default="ko", max_length=10)
    description: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None

class SystemPromptUpdate(BaseModel):
    prompt_content: Optional[str] = None
    prompt_version: Optional[str] = None
    description: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class SystemPromptResponse(BaseModel):
    id: str
    prompt_name: str
    prompt_content: str
    prompt_version: str
    language: str
    is_active: bool
    description: Optional[str]
    variables: Optional[Dict[str, Any]]
    created_by: str
    created_at: datetime
    updated_at: datetime
```

#### 4.2.2 스키마 메타데이터 모델

```python
class SchemaMetadataUpdate(BaseModel):
    connection_id: str
    table_name: str
    table_korean_name: Optional[str] = None
    table_description: Optional[str] = None
    table_business_context: Optional[str] = None
    column_name: Optional[str] = None
    column_korean_name: Optional[str] = None
    column_description: Optional[str] = None
    column_business_meaning: Optional[str] = None
    is_sensitive: Optional[bool] = None
    sample_values: Optional[List[str]] = None

class SchemaMetadataResponse(BaseModel):
    id: str
    connection_id: str
    table_name: str
    table_korean_name: Optional[str]
    table_description: Optional[str]
    column_name: Optional[str]
    column_korean_name: Optional[str]
    column_description: Optional[str]
    data_type: Optional[str]
    is_sensitive: bool
    updated_at: datetime
```

---

## 5. 서비스 계층 설계

### 5.1 시스템 프롬프트 서비스

```python
class SystemPromptService:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def get_active_prompt(self, prompt_name: str = "MAIN") -> Optional[SystemPrompt]:
        """활성화된 시스템 프롬프트 조회"""
        
    async def create_prompt(self, prompt_data: SystemPromptCreate, created_by: str) -> SystemPrompt:
        """새 시스템 프롬프트 생성"""
        
    async def update_prompt(self, prompt_id: str, prompt_data: SystemPromptUpdate, updated_by: str) -> SystemPrompt:
        """시스템 프롬프트 업데이트"""
        
    async def activate_prompt(self, prompt_id: str) -> bool:
        """시스템 프롬프트 활성화 (기존 활성 프롬프트 비활성화)"""
        
    async def get_prompt_variables(self, prompt_id: str) -> Dict[str, Any]:
        """프롬프트 변수 조회"""
```

### 5.2 스키마 메타데이터 서비스

```python
class SchemaMetadataService:
    def __init__(self, db_session: Session, llm_service: LLMService):
        self.db = db_session
        self.llm_service = llm_service
    
    async def get_enriched_schema(self, connection_id: str) -> Dict[str, Any]:
        """한국어 명칭이 포함된 스키마 정보 조회"""
        
    async def auto_generate_korean_names(self, connection_id: str) -> Dict[str, str]:
        """LLM을 활용한 한국어 명칭 자동 생성"""
        
    async def bulk_update_metadata(self, metadata_list: List[SchemaMetadataUpdate]) -> BulkUpdateResult:
        """스키마 메타데이터 일괄 업데이트"""
        
    async def validate_business_context(self, table_name: str, context: str) -> ValidationResult:
        """비즈니스 컨텍스트 유효성 검증"""
```

### 5.3 LLM 연결 관리 서비스

```python
class LLMConnectionService:
    def __init__(self, db_session: Session, encryption_service: EncryptionService):
        self.db = db_session
        self.encryption = encryption_service
    
    async def create_connection(self, connection_data: LLMConnectionCreate) -> LLMConnection:
        """새 LLM 연결 생성 (API 키 암호화)"""
        
    async def test_connection(self, connection_id: str) -> TestResult:
        """LLM 연결 테스트"""
        
    async def get_active_connection(self, model_preference: Optional[str] = None) -> LLMConnection:
        """활성화된 LLM 연결 조회"""
        
    async def calculate_cost_estimate(self, prompt_tokens: int, completion_tokens: int, model_name: str) -> float:
        """비용 예측 계산"""
```

---

## 6. 프론트엔드 설계

### 6.1 관리자 대시보드 구조

```
AdminDashboard/
├── SystemPromptManagement/
│   ├── PromptList.vue
│   ├── PromptEditor.vue
│   └── PromptVersionHistory.vue
├── SchemaManagement/
│   ├── SchemaOverview.vue
│   ├── TableMetadataEditor.vue
│   └── KoreanNameGenerator.vue
├── DatabaseManagement/
│   ├── ConnectionList.vue
│   ├── ConnectionWizard.vue
│   └── UserAssignment.vue
├── LLMManagement/
│   ├── ModelConfiguration.vue
│   ├── CostMonitoring.vue
│   └── PerformanceMetrics.vue
└── UserManagement/
    ├── UserList.vue
    ├── PermissionEditor.vue
    └── UsageAnalytics.vue
```

### 6.2 주요 컴포넌트

#### 6.2.1 시스템 프롬프트 편집기

```vue
<template>
  <div class="prompt-editor">
    <div class="editor-header">
      <h3>시스템 프롬프트 편집</h3>
      <div class="actions">
        <button @click="previewPrompt">미리보기</button>
        <button @click="savePrompt" :disabled="!isValid">저장</button>
      </div>
    </div>
    
    <div class="editor-content">
      <div class="editor-panel">
        <textarea 
          v-model="promptContent" 
          class="prompt-textarea"
          placeholder="시스템 프롬프트를 입력하세요..."
        ></textarea>
      </div>
      
      <div class="variables-panel">
        <h4>프롬프트 변수</h4>
        <div v-for="(variable, key) in variables" :key="key" class="variable-item">
          <input v-model="variable.name" placeholder="변수명">
          <input v-model="variable.description" placeholder="설명">
          <select v-model="variable.type">
            <option value="text">텍스트</option>
            <option value="number">숫자</option>
            <option value="boolean">불린</option>
          </select>
        </div>
      </div>
    </div>
    
    <div class="version-info">
      <label>버전: <input v-model="version" placeholder="1.0"></label>
      <label>설명: <input v-model="description" placeholder="변경 사항 설명"></label>
    </div>
  </div>
</template>
```

#### 6.2.2 스키마 메타데이터 관리

```vue
<template>
  <div class="schema-metadata-manager">
    <div class="table-selector">
      <select v-model="selectedConnection" @change="loadTables">
        <option v-for="conn in connections" :key="conn.id" :value="conn.id">
          {{ conn.display_name }}
        </option>
      </select>
      
      <select v-model="selectedTable" @change="loadColumns">
        <option v-for="table in tables" :key="table.name" :value="table.name">
          {{ table.korean_name || table.name }}
        </option>
      </select>
    </div>
    
    <div class="metadata-editor">
      <div class="table-metadata">
        <h4>테이블 정보</h4>
        <input v-model="tableMetadata.korean_name" placeholder="한국어 테이블명">
        <textarea v-model="tableMetadata.description" placeholder="테이블 설명"></textarea>
        <textarea v-model="tableMetadata.business_context" placeholder="비즈니스 컨텍스트"></textarea>
      </div>
      
      <div class="columns-metadata">
        <h4>컬럼 정보</h4>
        <div v-for="column in columns" :key="column.name" class="column-item">
          <div class="column-header">
            <strong>{{ column.name }}</strong>
            <span class="data-type">{{ column.data_type }}</span>
          </div>
          <input v-model="column.korean_name" placeholder="한국어 컬럼명">
          <textarea v-model="column.description" placeholder="컬럼 설명"></textarea>
          <input v-model="column.business_meaning" placeholder="비즈니스 의미">
          <label>
            <input type="checkbox" v-model="column.is_sensitive">
            민감 정보
          </label>
        </div>
      </div>
      
      <div class="actions">
        <button @click="autoGenerateKoreanNames">한국어명 자동 생성</button>
        <button @click="saveMetadata" :disabled="!hasChanges">저장</button>
      </div>
    </div>
  </div>
</template>
```

### 6.3 라우터 설정

```typescript
// src/router/admin.ts
const adminRoutes = [
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true, role: 'ADMIN' },
    children: [
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue')
      },
      {
        path: 'system-prompts',
        name: 'SystemPrompts',
        component: () => import('@/views/admin/SystemPrompts.vue')
      },
      {
        path: 'schema-metadata',
        name: 'SchemaMetadata', 
        component: () => import('@/views/admin/SchemaMetadata.vue')
      },
      {
        path: 'databases',
        name: 'DatabaseManagement',
        component: () => import('@/views/admin/DatabaseManagement.vue')
      },
      {
        path: 'llm-connections',
        name: 'LLMConnections',
        component: () => import('@/views/admin/LLMConnections.vue')
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: () => import('@/views/admin/UserManagement.vue')
      }
    ]
  }
];
```

---

## 7. 보안 및 권한 관리

### 7.1 RBAC 구현

```python
class PermissionChecker:
    @staticmethod
    def check_admin_permission(user: User, action: str, resource: str = None) -> bool:
        """관리자 권한 검사"""
        if user.role != UserRole.ADMIN:
            return False
            
        # 세분화된 권한 검사
        sensitive_actions = ['delete_user', 'modify_llm_config', 'access_sensitive_data']
        if action in sensitive_actions:
            return user.permissions.get(action, False)
            
        return True
    
    @staticmethod 
    def check_resource_permission(user: User, resource_type: str, resource_id: str, action: str) -> bool:
        """리소스별 권한 검사"""
        user_permissions = UserPermissionService.get_user_permissions(user.id)
        
        for permission in user_permissions:
            if (permission.resource_type == resource_type and 
                permission.resource_id == resource_id and
                action in permission.permission_value.get('allowed_actions', [])):
                return True
                
        return False
```

### 7.2 데이터 암호화

```python
class EncryptionService:
    def __init__(self, encryption_key: str):
        self.cipher_suite = Fernet(encryption_key.encode())
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """민감한 데이터 암호화"""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """민감한 데이터 복호화"""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_db_password(self, password: str) -> str:
        """DB 패스워드 암호화"""
        return self.encrypt_sensitive_data(password)
    
    def encrypt_api_key(self, api_key: str) -> str:
        """API 키 암호화"""
        return self.encrypt_sensitive_data(api_key)
```

### 7.3 감사 로그

```python
class AuditLogger:
    @staticmethod
    async def log_admin_action(
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str = None,
        old_values: Dict = None,
        new_values: Dict = None,
        success: bool = True,
        error_message: str = None
    ):
        """관리자 작업 로그 기록"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            success=success,
            error_message=error_message
        )
        
        # 민감한 정보 마스킹
        if old_values:
            audit_log.old_values = mask_sensitive_fields(old_values)
        if new_values:
            audit_log.new_values = mask_sensitive_fields(new_values)
            
        db.add(audit_log)
        await db.commit()
```

---

## 8. 구현 단계별 계획

### 8.1 Phase 1: 기반 구축 (2-3주)

1. **데이터베이스 스키마 생성**
   - 새 테이블 생성 및 기존 테이블 확장
   - 마이그레이션 스크립트 작성
2. **기본 API 구현**
   - 시스템 프롬프트 관리 API
   - LLM 접속정보 관리 API
3. **권한 시스템 강화**
   - 세분화된 RBAC 구현
   - 감사 로그 시스템 구축

### 8.2 Phase 2: 핵심 기능 (3-4주)

1. **스키마 메타데이터 관리**
   - 한국어 명칭 관리 시스템
   - LLM 기반 자동 생성 기능
2. **관리자 대시보드 개발**
   - 프론트엔드 컴포넌트 구현
   - 관리자 전용 UI/UX 설계
3. **DB 접속정보 중앙 관리**
   - 관리형 데이터베이스 연결 시스템
   - 사용자별 접근 권한 관리

### 8.3 Phase 3: 고급 기능 및 최적화 (2-3주)

1. **성능 최적화**
   - 캐싱 시스템 구현
   - 대용량 데이터 처리 최적화
2. **모니터링 및 알림**
   - 시스템 상태 모니터링
   - 이상 상황 알림 시스템
3. **사용자 경험 개선**
   - 직관적인 UI 개선
   - 도움말 및 가이드 시스템

---

## 9. 테스트 전략

### 9.1 단위 테스트

```python
class TestSystemPromptService:
    def test_create_prompt(self):
        """시스템 프롬프트 생성 테스트"""
        
    def test_activate_prompt(self):
        """시스템 프롬프트 활성화 테스트"""
        
    def test_prompt_variables(self):
        """프롬프트 변수 처리 테스트"""

class TestSchemaMetadataService:
    def test_korean_name_generation(self):
        """한국어 명칭 생성 테스트"""
        
    def test_bulk_update(self):
        """일괄 업데이트 테스트"""
```

### 9.2 통합 테스트

```python
class TestAdminWorkflow:
    def test_complete_schema_setup(self):
        """완전한 스키마 설정 워크플로우 테스트"""
        # 1. DB 연결 생성
        # 2. 스키마 메타데이터 설정
        # 3. 사용자 권한 할당
        # 4. 쿼리 실행 테스트
        
    def test_llm_configuration_workflow(self):
        """LLM 설정 워크플로우 테스트"""
        # 1. LLM 연결 생성
        # 2. 연결 테스트
        # 3. 기본 모델 설정
        # 4. 쿼리 실행 테스트
```

### 9.3 보안 테스트

```python
class TestSecurity:
    def test_admin_authorization(self):
        """관리자 권한 검증 테스트"""
        
    def test_data_encryption(self):
        """데이터 암호화 테스트"""
        
    def test_audit_logging(self):
        """감사 로그 기록 테스트"""
```

---

## 10. 운영 및 유지보수

### 10.1 모니터링

```python
class AdminMetricsCollector:
    @staticmethod
    def collect_usage_metrics():
        """관리자 기능 사용량 수집"""
        
    @staticmethod
    def collect_performance_metrics():
        """시스템 성능 지표 수집"""
        
    @staticmethod
    def collect_security_metrics():
        """보안 관련 지표 수집"""
```

### 10.2 백업 및 복구

```python
class ConfigBackupService:
    @staticmethod
    def backup_system_config():
        """시스템 설정 백업"""
        
    @staticmethod
    def backup_schema_metadata():
        """스키마 메타데이터 백업"""
        
    @staticmethod
    def restore_from_backup(backup_file: str):
        """백업에서 복구"""
```

### 10.3 업그레이드 전략

1. **하위 호환성 유지**: 기존 API 및 데이터 구조 호환성 보장
2. **점진적 마이그레이션**: 단계별 기능 업그레이드
3. **롤백 계획**: 문제 발생 시 즉시 이전 버전으로 롤백

---

## 11. 예상 효과 및 ROI

### 11.1 즉시 효과

- **보안 강화**: 민감한 시스템 설정의 안전한 관리
- **운영 효율성**: 실시간 시스템 설정 변경 가능
- **사용자 만족도**: 한국어 친화적 스키마 정보 제공

### 11.2 중장기 효과

- **확장성**: 새로운 LLM 모델 및 데이터베이스 쉬운 추가
- **비용 최적화**: LLM 사용량 모니터링 및 제어
- **서비스 품질**: 최적화된 프롬프트를 통한 응답 품질 향상

### 11.3 ROI 측정 지표

- 시스템 설정 변경 시간 단축: 기존 대비 80% 감소
- 사용자 쿼리 성공률 향상: 한국어 스키마 정보 제공으로 15-20% 향상
- 운영 비용 절감: LLM 토큰 사용량 최적화로 월 비용 10-15% 절감

---

## 12. 결론

이 설계서에 따라 구현할 경우, Text-to-SQL 시스템의 관리자 기능이 사용자 기능과 완전히 분리되어 보안성과 운영 효율성을 크게 향상시킬 수 있습니다. 특히 한국어 스키마 메타데이터 관리를 통해 사용자의 자연어 질의 경험을 획기적으로 개선할 수 있을 것으로 기대됩니다.

단계적 구현을 통해 기존 시스템의 안정성을 유지하면서도 새로운 관리자 기능을 점진적으로 추가할 수 있으며, 각 단계마다 명확한 성과 측정이 가능합니다.
