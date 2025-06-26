<template>
  <div class="admin-llm">
    <!-- 추가 버튼 -->
    <div class="action-bar">
      <button @click="showAddModal = true" class="btn-primary">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
        </svg>
        새 LLM 연결 추가
      </button>
    </div>

    <!-- LLM 연결 목록 -->
    <div class="llm-connections-grid">
      <div v-for="connection in llmConnections" :key="connection.id" class="llm-card">
        <div class="llm-header">
          <div class="llm-info">
            <h3 class="llm-name">{{ connection.name }}</h3>
            <span class="llm-provider">{{ connection.provider }}</span>
          </div>
          <div class="llm-status">
            <span :class="['status-indicator', connection.status]"></span>
            <span class="status-text">{{ getStatusText(connection.status) }}</span>
          </div>
        </div>
        
        <div class="llm-details">
          <div class="detail-item">
            <span class="detail-label">모델:</span>
            <span class="detail-value">{{ connection.model }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">API 엔드포인트:</span>
            <span class="detail-value">{{ connection.endpoint }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">최대 토큰:</span>
            <span class="detail-value">{{ connection.max_tokens?.toLocaleString() || 'N/A' }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Temperature:</span>
            <span class="detail-value">{{ connection.temperature || 'N/A' }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">마지막 테스트:</span>
            <span class="detail-value">{{ formatDate(connection.last_tested) }}</span>
          </div>
          <div v-if="connection.is_default" class="default-badge">
            기본 모델
          </div>
        </div>
        
        <div class="llm-actions">
          <button @click="testLlmConnection(connection)" class="btn-outline" :disabled="testingConnections.includes(connection.id)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            {{ testingConnections.includes(connection.id) ? '테스트 중...' : '연결 테스트' }}
          </button>
          <button @click="editLlmConnection(connection)" class="btn-outline">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
            </svg>
            편집
          </button>
          <button @click="setAsDefault(connection)" class="btn-secondary" :disabled="connection.is_default">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.196-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"></path>
            </svg>
            {{ connection.is_default ? '기본 모델' : '기본으로 설정' }}
          </button>
          <button @click="confirmDeleteLlm(connection)" class="btn-danger" :disabled="connection.is_default">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
            </svg>
            삭제
          </button>
        </div>
      </div>
    </div>

    <!-- LLM 연결 추가/편집 모달 -->
    <div v-if="showAddModal || editingConnection" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">{{ editingConnection ? 'LLM 연결 편집' : '새 LLM 연결 추가' }}</h3>
          <button @click="closeModal" class="modal-close">×</button>
        </div>
        <form @submit.prevent="saveLlmConnection" class="modal-body">
          <div class="form-grid">
            <div class="form-group">
              <label class="form-label">연결 이름 *</label>
              <input
                v-model="llmForm.name"
                type="text"
                class="form-input"
                placeholder="예: OpenAI GPT-4"
                required
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">제공업체 *</label>
              <select v-model="llmForm.provider" class="form-select" required @change="updateProviderDefaults">
                <option value="">선택하세요</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="google">Google</option>
                <option value="azure">Azure OpenAI</option>
                <option value="local">Local Model</option>
              </select>
            </div>
            
            <div class="form-group">
              <label class="form-label">모델 *</label>
              <input
                v-model="llmForm.model"
                type="text"
                class="form-input"
                placeholder="예: gpt-4, claude-3, gemini-pro"
                required
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">API 키 *</label>
              <input
                v-model="llmForm.api_key"
                type="password"
                class="form-input"
                placeholder="API 키를 입력하세요"
                required
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">API 엔드포인트</label>
              <input
                v-model="llmForm.endpoint"
                type="url"
                class="form-input"
                placeholder="https://api.openai.com/v1"
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">최대 토큰</label>
              <input
                v-model.number="llmForm.max_tokens"
                type="number"
                class="form-input"
                placeholder="4000"
                min="1"
                max="128000"
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">Temperature</label>
              <input
                v-model.number="llmForm.temperature"
                type="number"
                class="form-input"
                placeholder="0.7"
                min="0"
                max="2"
                step="0.1"
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">설명</label>
              <textarea
                v-model="llmForm.description"
                class="form-textarea"
                placeholder="연결에 대한 설명 (선택사항)"
                rows="2"
              ></textarea>
            </div>
          </div>
          
          <div class="form-actions">
            <button type="button" @click="closeModal" class="btn-secondary">취소</button>
            <button type="submit" class="btn-primary">{{ editingConnection ? '업데이트' : '추가' }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuth } from '@/composables/useAuth'

interface LlmConnection {
  id: string
  name: string
  provider: string
  model: string
  api_key?: string
  endpoint: string
  max_tokens?: number
  temperature?: number
  description?: string
  status: 'connected' | 'disconnected' | 'error'
  is_default: boolean
  last_tested: string
  created_at: string
}

const { token } = useAuth()
const llmConnections = ref<LlmConnection[]>([])
const showAddModal = ref(false)
const editingConnection = ref<LlmConnection | null>(null)
const testingConnections = ref<string[]>([])

const llmForm = ref({
  name: '',
  provider: '',
  model: '',
  api_key: '',
  endpoint: '',
  max_tokens: 4000,
  temperature: 0.7,
  description: ''
})

const providerDefaults = {
  openai: {
    endpoint: 'https://api.openai.com/v1',
    model: 'gpt-4',
    max_tokens: 4000
  },
  anthropic: {
    endpoint: 'https://api.anthropic.com',
    model: 'claude-3-sonnet-20240229',
    max_tokens: 4000
  },
  google: {
    endpoint: 'https://generativelanguage.googleapis.com/v1',
    model: 'gemini-pro',
    max_tokens: 2048
  },
  azure: {
    endpoint: 'https://your-resource.openai.azure.com',
    model: 'gpt-4',
    max_tokens: 4000
  }
}

const fetchLlmConnections = async () => {
  try {
    // 실제 API 호출 시 구현
    // const response = await fetch('/api/v1/admin/llm-connections', {
    //   headers: { 'Authorization': `Bearer ${token.value}` }
    // })
    // if (response.ok) {
    //   llmConnections.value = await response.json()
    // }
    
    // 임시 데이터
    llmConnections.value = [
      {
        id: '1',
        name: 'OpenAI GPT-4',
        provider: 'openai',
        model: 'gpt-4',
        endpoint: 'https://api.openai.com/v1',
        max_tokens: 4000,
        temperature: 0.7,
        status: 'connected',
        is_default: true,
        last_tested: '2024-01-20T10:30:00Z',
        created_at: '2024-01-01T00:00:00Z',
        description: '메인 GPT-4 모델'
      },
      {
        id: '2',
        name: 'Claude 3 Sonnet',
        provider: 'anthropic',
        model: 'claude-3-sonnet-20240229',
        endpoint: 'https://api.anthropic.com',
        max_tokens: 4000,
        temperature: 0.5,
        status: 'connected',
        is_default: false,
        last_tested: '2024-01-19T15:20:00Z',
        created_at: '2024-01-10T00:00:00Z',
        description: '백업 Claude 모델'
      },
      {
        id: '3',
        name: 'Local Llama',
        provider: 'local',
        model: 'llama-2-7b',
        endpoint: 'http://localhost:8080/v1',
        max_tokens: 2048,
        temperature: 0.8,
        status: 'disconnected',
        is_default: false,
        last_tested: '2024-01-18T12:00:00Z',
        created_at: '2024-01-15T00:00:00Z',
        description: '로컬 실행 모델'
      }
    ]
  } catch (error) {
    console.error('Failed to fetch LLM connections:', error)
  }
}

const testLlmConnection = async (connection: LlmConnection) => {
  testingConnections.value.push(connection.id)
  
  try {
    // 실제 API 호출 시 구현
    // const response = await fetch(`/api/v1/admin/llm-connections/${connection.id}/test`, {
    //   method: 'POST',
    //   headers: { 'Authorization': `Bearer ${token.value}` }
    // })
    
    // 임시 처리
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    const connectionIndex = llmConnections.value.findIndex(c => c.id === connection.id)
    if (connectionIndex !== -1) {
      llmConnections.value[connectionIndex].status = 'connected'
      llmConnections.value[connectionIndex].last_tested = new Date().toISOString()
    }
    
    alert('LLM 연결 테스트가 성공했습니다.')
  } catch (error) {
    console.error('LLM connection test failed:', error)
    alert('LLM 연결 테스트에 실패했습니다.')
  } finally {
    testingConnections.value = testingConnections.value.filter(id => id !== connection.id)
  }
}

const editLlmConnection = (connection: LlmConnection) => {
  editingConnection.value = connection
  llmForm.value = {
    name: connection.name,
    provider: connection.provider,
    model: connection.model,
    api_key: '',
    endpoint: connection.endpoint,
    max_tokens: connection.max_tokens || 4000,
    temperature: connection.temperature || 0.7,
    description: connection.description || ''
  }
}

const updateProviderDefaults = () => {
  const provider = llmForm.value.provider as keyof typeof providerDefaults
  if (providerDefaults[provider]) {
    const defaults = providerDefaults[provider]
    llmForm.value.endpoint = defaults.endpoint
    llmForm.value.model = defaults.model
    llmForm.value.max_tokens = defaults.max_tokens
  }
}

const saveLlmConnection = async () => {
  try {
    const method = editingConnection.value ? 'PUT' : 'POST'
    const url = editingConnection.value
      ? `/api/v1/admin/llm-connections/${editingConnection.value.id}`
      : '/api/v1/admin/llm-connections'
    
    // 실제 API 호출 시 구현
    // const response = await fetch(url, {
    //   method,
    //   headers: {
    //     'Authorization': `Bearer ${token.value}`,
    //     'Content-Type': 'application/json'
    //   },
    //   body: JSON.stringify(llmForm.value)
    // })
    
    // if (response.ok) {
    //   await fetchLlmConnections()
    //   closeModal()
    //   alert(editingConnection.value ? 'LLM 연결이 업데이트되었습니다.' : '새 LLM 연결이 추가되었습니다.')
    // }
    
    // 임시 처리
    alert(editingConnection.value ? 'LLM 연결이 업데이트되었습니다.' : '새 LLM 연결이 추가되었습니다.')
    closeModal()
  } catch (error) {
    console.error('Failed to save LLM connection:', error)
    alert('LLM 연결 저장에 실패했습니다.')
  }
}

const setAsDefault = async (connection: LlmConnection) => {
  try {
    // 실제 API 호출 시 구현
    // const response = await fetch(`/api/v1/admin/llm-connections/${connection.id}/set-default`, {
    //   method: 'POST',
    //   headers: { 'Authorization': `Bearer ${token.value}` }
    // })
    
    // if (response.ok) {
    //   await fetchLlmConnections()
    //   alert('기본 모델이 설정되었습니다.')
    // }
    
    // 임시 처리
    llmConnections.value.forEach(c => c.is_default = false)
    connection.is_default = true
    alert('기본 모델이 설정되었습니다.')
  } catch (error) {
    console.error('Failed to set default:', error)
    alert('기본 모델 설정에 실패했습니다.')
  }
}

const confirmDeleteLlm = (connection: LlmConnection) => {
  if (confirm(`정말로 LLM 연결 "${connection.name}"을 삭제하시겠습니까?`)) {
    deleteLlmConnection(connection.id)
  }
}

const deleteLlmConnection = async (connectionId: string) => {
  try {
    // 실제 API 호출 시 구현
    // const response = await fetch(`/api/v1/admin/llm-connections/${connectionId}`, {
    //   method: 'DELETE',
    //   headers: { 'Authorization': `Bearer ${token.value}` }
    // })
    
    // if (response.ok) {
    //   llmConnections.value = llmConnections.value.filter(c => c.id !== connectionId)
    //   alert('LLM 연결이 삭제되었습니다.')
    // }
    
    // 임시 처리
    llmConnections.value = llmConnections.value.filter(c => c.id !== connectionId)
    alert('LLM 연결이 삭제되었습니다.')
  } catch (error) {
    console.error('Failed to delete LLM connection:', error)
    alert('LLM 연결 삭제에 실패했습니다.')
  }
}

const closeModal = () => {
  showAddModal.value = false
  editingConnection.value = null
  llmForm.value = {
    name: '',
    provider: '',
    model: '',
    api_key: '',
    endpoint: '',
    max_tokens: 4000,
    temperature: 0.7,
    description: ''
  }
}

const getStatusText = (status: string): string => {
  switch (status) {
    case 'connected': return '연결됨'
    case 'disconnected': return '연결 안됨'
    case 'error': return '오류'
    default: return '알 수 없음'
  }
}

const formatDate = (dateString: string): string => {
  if (!dateString) return '없음'
  return new Date(dateString).toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  fetchLlmConnections()
})
</script>

<style scoped>
.admin-llm {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.page-header {
  margin-bottom: 2rem;
}

.action-bar {
  margin-bottom: 2rem;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: #3b82f6;
  color: white;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary:hover {
  background: #2563eb;
}

.llm-connections-grid {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
}

.llm-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  padding: 1.5rem;
  position: relative;
}

.llm-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.llm-info {
  flex: 1;
}

.llm-name {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.25rem 0;
}

.llm-provider {
  background: #f3f4f6;
  color: #374151;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
}

.llm-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-indicator.connected {
  background: #10b981;
}

.status-indicator.disconnected {
  background: #f59e0b;
}

.status-indicator.error {
  background: #ef4444;
}

.status-text {
  font-size: 0.875rem;
  color: #6b7280;
}

.default-badge {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: #3b82f6;
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 500;
}

.llm-details {
  margin-bottom: 1rem;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f3f4f6;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  font-weight: 500;
  color: #374151;
}

.detail-value {
  color: #6b7280;
  font-family: monospace;
  font-size: 0.875rem;
}

.llm-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: transparent;
  color: #3b82f6;
  padding: 0.5rem 0.75rem;
  border: 1px solid #3b82f6;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-outline:hover:not(:disabled) {
  background: #3b82f6;
  color: white;
}

.btn-outline:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: #f59e0b;
  color: white;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-secondary:hover:not(:disabled) {
  background: #d97706;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-danger {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: #ef4444;
  color: white;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}

.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 700px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6b7280;
}

.modal-body {
  padding: 1.5rem;
}

.form-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-label {
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
}

.form-input,
.form-select,
.form-textarea {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.875rem;
}

.form-textarea {
  resize: vertical;
  min-height: 60px;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

@media (max-width: 768px) {
  .admin-llm {
    padding: 1rem;
  }
  
  .llm-connections-grid {
    grid-template-columns: 1fr;
  }
  
  .llm-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .llm-actions {
    justify-content: center;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .form-actions {
    flex-direction: column;
  }
}
</style>
