<template>
  <div class="admin-db-connections">
    <!-- 연결 추가 버튼 -->
    <div class="action-bar">
      <button @click="showAddModal = true" class="btn-primary">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
        </svg>
        새 연결 추가
      </button>
    </div>

    <!-- 연결 목록 -->
    <div class="connections-grid">
      <div v-for="connection in connections" :key="connection.id" class="connection-card">
        <div class="connection-header">
          <div class="connection-info">
            <h3 class="connection-name">{{ connection.name }}</h3>
            <span class="connection-type">{{ connection.db_type }}</span>
          </div>
          <div class="connection-status">
            <span :class="['status-indicator', connection.status]"></span>
            <span class="status-text">{{ getStatusText(connection.status) }}</span>
          </div>
        </div>
        
        <div class="connection-details">
          <div class="detail-item">
            <span class="detail-label">호스트:</span>
            <span class="detail-value">{{ connection.host }}:{{ connection.port }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">데이터베이스:</span>
            <span class="detail-value">{{ connection.database }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">마지막 테스트:</span>
            <span class="detail-value">{{ formatDate(connection.last_tested) }}</span>
          </div>
        </div>
        
        <div class="connection-actions">
          <button @click="testConnection(connection)" class="btn-outline" :disabled="testingConnections.includes(connection.id)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            {{ testingConnections.includes(connection.id) ? '테스트 중...' : '연결 테스트' }}
          </button>
          <button @click="editConnection(connection)" class="btn-outline">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
            </svg>
            편집
          </button>
          <button @click="confirmDeleteConnection(connection)" class="btn-danger">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
            </svg>
            삭제
          </button>
        </div>
      </div>
    </div>

    <!-- 연결 추가/편집 모달 -->
    <div v-if="showAddModal || editingConnection" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">{{ editingConnection ? '연결 편집' : '새 연결 추가' }}</h3>
          <button @click="closeModal" class="modal-close">×</button>
        </div>
        <form @submit.prevent="saveConnection" class="modal-body">
          <div class="form-grid">
            <div class="form-group">
              <label class="form-label">연결 이름 *</label>
              <input
                v-model="connectionForm.name"
                type="text"
                class="form-input"
                placeholder="예: Production DB"
                required
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">DB 타입 *</label>
              <select v-model="connectionForm.db_type" class="form-select" required>
                <option value="">선택하세요</option>
                <option value="postgresql">PostgreSQL</option>
                <option value="mysql">MySQL</option>
                <option value="mssql">SQL Server</option>
                <option value="sqlite">SQLite</option>
                <option value="oracle">Oracle</option>
              </select>
            </div>
            
            <div class="form-group">
              <label class="form-label">호스트 *</label>
              <input
                v-model="connectionForm.host"
                type="text"
                class="form-input"
                placeholder="localhost 또는 IP 주소"
                required
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">포트 *</label>
              <input
                v-model="connectionForm.port"
                type="number"
                class="form-input"
                placeholder="5432"
                required
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">데이터베이스명 *</label>
              <input
                v-model="connectionForm.database"
                type="text"
                class="form-input"
                placeholder="데이터베이스 이름"
                required
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">사용자명 *</label>
              <input
                v-model="connectionForm.username"
                type="text"
                class="form-input"
                placeholder="사용자명"
                required
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">비밀번호 *</label>
              <input
                v-model="connectionForm.password"
                type="password"
                class="form-input"
                placeholder="비밀번호"
                required
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">설명</label>
              <textarea
                v-model="connectionForm.description"
                class="form-textarea"
                placeholder="연결에 대한 설명 (선택사항)"
                rows="3"
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

interface DbConnection {
  id: string
  name: string
  db_type: string
  host: string
  port: number
  database: string
  username: string
  password?: string
  description?: string
  status: 'connected' | 'disconnected' | 'error'
  last_tested: string
  created_at: string
}

const { token } = useAuth()
const connections = ref<DbConnection[]>([])
const showAddModal = ref(false)
const editingConnection = ref<DbConnection | null>(null)
const testingConnections = ref<string[]>([])

const connectionForm = ref({
  name: '',
  db_type: '',
  host: '',
  port: 5432,
  database: '',
  username: '',
  password: '',
  description: ''
})

const fetchConnections = async () => {
  try {
    // 실제 API 호출 시 구현
    // const response = await fetch('/api/v1/admin/db-connections', {
    //   headers: { 'Authorization': `Bearer ${token.value}` }
    // })
    // if (response.ok) {
    //   connections.value = await response.json()
    // }
    
    // 임시 데이터
    connections.value = [
      {
        id: '1',
        name: 'Production PostgreSQL',
        db_type: 'postgresql',
        host: 'prod-db.example.com',
        port: 5432,
        database: 'analytics',
        username: 'app_user',
        status: 'connected',
        last_tested: '2024-01-20T10:30:00Z',
        created_at: '2024-01-01T00:00:00Z',
        description: '메인 프로덕션 데이터베이스'
      },
      {
        id: '2',
        name: 'Development MySQL',
        db_type: 'mysql',
        host: 'localhost',
        port: 3306,
        database: 'dev_db',
        username: 'dev_user',
        status: 'disconnected',
        last_tested: '2024-01-19T15:20:00Z',
        created_at: '2024-01-15T00:00:00Z',
        description: '개발용 데이터베이스'
      }
    ]
  } catch (error) {
    console.error('Failed to fetch connections:', error)
  }
}

const testConnection = async (connection: DbConnection) => {
  testingConnections.value.push(connection.id)
  
  try {
    // 실제 API 호출 시 구현
    // const response = await fetch(`/api/v1/admin/db-connections/${connection.id}/test`, {
    //   method: 'POST',
    //   headers: { 'Authorization': `Bearer ${token.value}` }
    // })
    
    // 임시 처리
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    const connectionIndex = connections.value.findIndex(c => c.id === connection.id)
    if (connectionIndex !== -1) {
      connections.value[connectionIndex].status = 'connected'
      connections.value[connectionIndex].last_tested = new Date().toISOString()
    }
    
    alert('연결 테스트가 성공했습니다.')
  } catch (error) {
    console.error('Connection test failed:', error)
    alert('연결 테스트에 실패했습니다.')
  } finally {
    testingConnections.value = testingConnections.value.filter(id => id !== connection.id)
  }
}

const editConnection = (connection: DbConnection) => {
  editingConnection.value = connection
  connectionForm.value = {
    name: connection.name,
    db_type: connection.db_type,
    host: connection.host,
    port: connection.port,
    database: connection.database,
    username: connection.username,
    password: '',
    description: connection.description || ''
  }
}

const saveConnection = async () => {
  try {
    const method = editingConnection.value ? 'PUT' : 'POST'
    const url = editingConnection.value
      ? `/api/v1/admin/db-connections/${editingConnection.value.id}`
      : '/api/v1/admin/db-connections'
    
    // 실제 API 호출 시 구현
    // const response = await fetch(url, {
    //   method,
    //   headers: {
    //     'Authorization': `Bearer ${token.value}`,
    //     'Content-Type': 'application/json'
    //   },
    //   body: JSON.stringify(connectionForm.value)
    // })
    
    // if (response.ok) {
    //   await fetchConnections()
    //   closeModal()
    //   alert(editingConnection.value ? '연결이 업데이트되었습니다.' : '새 연결이 추가되었습니다.')
    // }
    
    // 임시 처리
    alert(editingConnection.value ? '연결이 업데이트되었습니다.' : '새 연결이 추가되었습니다.')
    closeModal()
  } catch (error) {
    console.error('Failed to save connection:', error)
    alert('연결 저장에 실패했습니다.')
  }
}

const confirmDeleteConnection = (connection: DbConnection) => {
  if (confirm(`정말로 연결 "${connection.name}"을 삭제하시겠습니까?`)) {
    deleteConnection(connection.id)
  }
}

const deleteConnection = async (connectionId: string) => {
  try {
    // 실제 API 호출 시 구현
    // const response = await fetch(`/api/v1/admin/db-connections/${connectionId}`, {
    //   method: 'DELETE',
    //   headers: { 'Authorization': `Bearer ${token.value}` }
    // })
    
    // if (response.ok) {
    //   connections.value = connections.value.filter(c => c.id !== connectionId)
    //   alert('연결이 삭제되었습니다.')
    // }
    
    // 임시 처리
    connections.value = connections.value.filter(c => c.id !== connectionId)
    alert('연결이 삭제되었습니다.')
  } catch (error) {
    console.error('Failed to delete connection:', error)
    alert('연결 삭제에 실패했습니다.')
  }
}

const closeModal = () => {
  showAddModal.value = false
  editingConnection.value = null
  connectionForm.value = {
    name: '',
    db_type: '',
    host: '',
    port: 5432,
    database: '',
    username: '',
    password: '',
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
  fetchConnections()
})
</script>

<style scoped>
.admin-db-connections {
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

.connections-grid {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
}

.connection-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  padding: 1.5rem;
}

.connection-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.connection-info {
  flex: 1;
}

.connection-name {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.25rem 0;
}

.connection-type {
  background: #f3f4f6;
  color: #374151;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
}

.connection-status {
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

.connection-details {
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
}

.connection-actions {
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
  padding: 0.5rem 1rem;
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

.btn-danger {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: #ef4444;
  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-danger:hover {
  background: #dc2626;
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
  max-width: 600px;
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
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
  min-height: 80px;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  padding: 0.75rem 1.5rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

@media (max-width: 768px) {
  .admin-db-connections {
    padding: 1rem;
  }
  
  .connections-grid {
    grid-template-columns: 1fr;
  }
  
  .connection-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .connection-actions {
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
