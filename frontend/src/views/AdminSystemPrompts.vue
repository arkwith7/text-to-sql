<template>
  <div class="admin-prompts">
    <!-- 현재 활성 프롬프트 -->
    <div class="current-prompt-section">
      <h2 class="text-xl font-semibold mb-4">현재 활성 프롬프트</h2>
      <div class="prompt-card active">
        <div class="prompt-header">
          <h3 class="prompt-title">{{ currentPrompt.name || '기본 프롬프트' }}</h3>
          <span class="prompt-version">v{{ currentPrompt.version || '1.0' }}</span>
        </div>
        <div class="prompt-content">
          <pre>{{ currentPrompt.content || '시스템 프롬프트를 불러오는 중...' }}</pre>
        </div>
        <div class="prompt-meta">
          <span class="meta-item">생성일: {{ formatDate(currentPrompt.created_at) }}</span>
          <span class="meta-item">수정일: {{ formatDate(currentPrompt.updated_at) }}</span>
        </div>
      </div>
    </div>

    <!-- 프롬프트 편집기 -->
    <div class="prompt-editor-section">
      <h2 class="text-xl font-semibold mb-4">프롬프트 편집</h2>
      <div class="editor-card">
        <div class="editor-header">
          <input
            v-model="editingPrompt.name"
            type="text"
            placeholder="프롬프트 이름"
            class="prompt-name-input"
          />
          <input
            v-model="editingPrompt.version"
            type="text"
            placeholder="버전 (예: 1.1)"
            class="prompt-version-input"
          />
        </div>
        <textarea
          v-model="editingPrompt.content"
          class="prompt-textarea"
          placeholder="시스템 프롬프트를 입력하세요..."
          rows="10"
        ></textarea>
        <div class="editor-actions">
          <button @click="previewPrompt" class="btn-secondary">미리보기</button>
          <button @click="savePrompt" class="btn-primary" :disabled="!editingPrompt.content">
            {{ editingPrompt.id ? '업데이트' : '저장' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 프롬프트 히스토리 -->
    <div class="prompt-history-section">
      <h2 class="text-xl font-semibold mb-4">프롬프트 히스토리</h2>
      <div class="history-list">
        <div v-for="prompt in promptHistory" :key="prompt.id" class="history-item">
          <div class="history-header">
            <h4 class="history-title">{{ prompt.name }}</h4>
            <span class="history-version">v{{ prompt.version }}</span>
            <span class="history-date">{{ formatDate(prompt.created_at) }}</span>
          </div>
          <div class="history-content">
            <p class="content-preview">{{ truncateText(prompt.content, 100) }}</p>
          </div>
          <div class="history-actions">
            <button @click="viewPrompt(prompt)" class="btn-outline">보기</button>
            <button @click="editPrompt(prompt)" class="btn-outline">편집</button>
            <button @click="activatePrompt(prompt)" class="btn-primary" :disabled="prompt.is_active">
              {{ prompt.is_active ? '활성' : '활성화' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 프롬프트 미리보기 모달 -->
    <div v-if="previewModal" class="modal-overlay" @click="closePreview">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">프롬프트 미리보기</h3>
          <button @click="closePreview" class="modal-close">×</button>
        </div>
        <div class="modal-body">
          <div class="preview-content">
            <pre>{{ previewContent }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuth } from '@/composables/useAuth'

interface SystemPrompt {
  id?: string
  name: string
  content: string
  version: string
  is_active: boolean
  created_at: string
  updated_at: string
}

const { token } = useAuth()
const currentPrompt = ref<SystemPrompt>({
  id: '',
  name: '기본 프롬프트',
  content: '',
  version: '1.0',
  is_active: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString()
})

const editingPrompt = ref<SystemPrompt>({
  name: '',
  content: '',
  version: '',
  is_active: false,
  created_at: '',
  updated_at: ''
})

const promptHistory = ref<SystemPrompt[]>([])
const previewModal = ref(false)
const previewContent = ref('')

const fetchCurrentPrompt = async () => {
  try {
    // 실제 API 호출 시 구현
    // const response = await fetch('/api/v1/admin/system-prompts/current', {
    //   headers: { 'Authorization': `Bearer ${token.value}` }
    // })
    // if (response.ok) {
    //   currentPrompt.value = await response.json()
    // }
    
    // 임시 데이터
    currentPrompt.value = {
      id: '1',
      name: 'SQL 변환 프롬프트',
      content: `You are an expert SQL analyst. Your task is to convert natural language questions into accurate SQL queries.

Rules:
1. Always analyze the database schema first
2. Generate syntactically correct SQL for the given database type
3. Include appropriate JOINs when querying multiple tables
4. Use proper WHERE clauses for filtering
5. Format the output clearly with explanations

When responding:
- First, explain your understanding of the question
- Then provide the SQL query
- Finally, explain the query logic`,
      version: '2.1',
      is_active: true,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-20T14:30:00Z'
    }
  } catch (error) {
    console.error('Failed to fetch current prompt:', error)
  }
}

const fetchPromptHistory = async () => {
  try {
    // 실제 API 호출 시 구현
    // const response = await fetch('/api/v1/admin/system-prompts', {
    //   headers: { 'Authorization': `Bearer ${token.value}` }
    // })
    // if (response.ok) {
    //   promptHistory.value = await response.json()
    // }
    
    // 임시 데이터
    promptHistory.value = [
      {
        id: '1',
        name: 'SQL 변환 프롬프트',
        content: 'You are an expert SQL analyst...',
        version: '2.1',
        is_active: true,
        created_at: '2024-01-20T14:30:00Z',
        updated_at: '2024-01-20T14:30:00Z'
      },
      {
        id: '2',
        name: 'SQL 변환 프롬프트',
        content: 'You are a SQL expert who converts natural language to SQL...',
        version: '2.0',
        is_active: false,
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z'
      }
    ]
  } catch (error) {
    console.error('Failed to fetch prompt history:', error)
  }
}

const savePrompt = async () => {
  try {
    const method = editingPrompt.value.id ? 'PUT' : 'POST'
    const url = editingPrompt.value.id 
      ? `/api/v1/admin/system-prompts/${editingPrompt.value.id}`
      : '/api/v1/admin/system-prompts'
    
    // 실제 API 호출 시 구현
    // const response = await fetch(url, {
    //   method,
    //   headers: {
    //     'Authorization': `Bearer ${token.value}`,
    //     'Content-Type': 'application/json'
    //   },
    //   body: JSON.stringify(editingPrompt.value)
    // })
    
    // if (response.ok) {
    //   await fetchPromptHistory()
    //   resetEditor()
    //   alert('프롬프트가 저장되었습니다.')
    // }
    
    // 임시 처리
    alert('프롬프트가 저장되었습니다.')
    resetEditor()
  } catch (error) {
    console.error('Failed to save prompt:', error)
    alert('프롬프트 저장에 실패했습니다.')
  }
}

const previewPrompt = () => {
  previewContent.value = editingPrompt.value.content
  previewModal.value = true
}

const closePreview = () => {
  previewModal.value = false
  previewContent.value = ''
}

const viewPrompt = (prompt: SystemPrompt) => {
  previewContent.value = prompt.content
  previewModal.value = true
}

const editPrompt = (prompt: SystemPrompt) => {
  editingPrompt.value = { ...prompt }
}

const activatePrompt = async (prompt: SystemPrompt) => {
  try {
    // 실제 API 호출 시 구현
    // const response = await fetch(`/api/v1/admin/system-prompts/${prompt.id}/activate`, {
    //   method: 'POST',
    //   headers: { 'Authorization': `Bearer ${token.value}` }
    // })
    
    // if (response.ok) {
    //   await fetchCurrentPrompt()
    //   await fetchPromptHistory()
    //   alert('프롬프트가 활성화되었습니다.')
    // }
    
    // 임시 처리
    alert('프롬프트가 활성화되었습니다.')
  } catch (error) {
    console.error('Failed to activate prompt:', error)
    alert('프롬프트 활성화에 실패했습니다.')
  }
}

const resetEditor = () => {
  editingPrompt.value = {
    name: '',
    content: '',
    version: '',
    is_active: false,
    created_at: '',
    updated_at: ''
  }
}

const formatDate = (dateString: string): string => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

onMounted(() => {
  fetchCurrentPrompt()
  fetchPromptHistory()
})
</script>

<style scoped>
.admin-prompts {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.page-header {
  margin-bottom: 2rem;
}

.current-prompt-section,
.prompt-editor-section,
.prompt-history-section {
  margin-bottom: 3rem;
}

.prompt-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  padding: 1.5rem;
}

.prompt-card.active {
  border-color: #3b82f6;
  box-shadow: 0 1px 3px rgba(59, 130, 246, 0.1);
}

.prompt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.prompt-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.prompt-version {
  background: #3b82f6;
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 500;
}

.prompt-content {
  margin-bottom: 1rem;
}

.prompt-content pre {
  background: #f9fafb;
  padding: 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  line-height: 1.5;
  white-space: pre-wrap;
  overflow-x: auto;
}

.prompt-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.editor-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  padding: 1.5rem;
}

.editor-header {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.prompt-name-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.875rem;
}

.prompt-version-input {
  width: 150px;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.875rem;
}

.prompt-textarea {
  width: 100%;
  padding: 1rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.875rem;
  line-height: 1.5;
  resize: vertical;
  min-height: 200px;
  font-family: 'Monaco', 'Menlo', monospace;
}

.editor-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1rem;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  padding: 0.75rem 1.5rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

.btn-outline {
  background: transparent;
  color: #3b82f6;
  padding: 0.5rem 1rem;
  border: 1px solid #3b82f6;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-outline:hover {
  background: #3b82f6;
  color: white;
}

.history-list {
  display: grid;
  gap: 1rem;
}

.history-item {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  padding: 1.5rem;
}

.history-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.history-title {
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.history-version {
  background: #f3f4f6;
  color: #374151;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

.history-date {
  color: #6b7280;
  font-size: 0.75rem;
  margin-left: auto;
}

.history-content {
  margin-bottom: 1rem;
}

.content-preview {
  color: #6b7280;
  font-size: 0.875rem;
  margin: 0;
}

.history-actions {
  display: flex;
  gap: 0.5rem;
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
  max-width: 800px;
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

.preview-content pre {
  background: #f9fafb;
  padding: 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  line-height: 1.5;
  white-space: pre-wrap;
  overflow-x: auto;
}

@media (max-width: 768px) {
  .admin-prompts {
    padding: 1rem;
  }
  
  .editor-header {
    flex-direction: column;
  }
  
  .prompt-version-input {
    width: 100%;
  }
  
  .editor-actions {
    flex-direction: column;
  }
  
  .history-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .history-date {
    margin-left: 0;
  }
}
</style>
