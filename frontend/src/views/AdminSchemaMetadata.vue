<template>
  <div class="admin-schema">
    <!-- DB 선택 -->
    <div class="db-selector">
      <select v-model="selectedDb" @change="fetchSchemas" class="db-select">
        <option value="">데이터베이스를 선택하세요</option>
        <option v-for="db in databases" :key="db.id" :value="db.id">
          {{ db.name }} ({{ db.db_type }})
        </option>
      </select>
      <button @click="refreshSchemas" class="btn-secondary" :disabled="!selectedDb">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
        </svg>
        스키마 새로고침
      </button>
    </div>

    <!-- 스키마 정보 -->
    <div v-if="selectedDb && schemas.length > 0" class="schema-content">
      <div class="schema-stats">
        <div class="stat-item">
          <span class="stat-label">총 테이블 수:</span>
          <span class="stat-value">{{ schemas.length }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">총 컬럼 수:</span>
          <span class="stat-value">{{ totalColumns }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">마지막 업데이트:</span>
          <span class="stat-value">{{ lastUpdated }}</span>
        </div>
      </div>

      <!-- 테이블 목록 -->
      <div class="tables-section">
        <h2 class="section-title">테이블 목록</h2>
        <div class="tables-grid">
          <div v-for="table in schemas" :key="table.table_name" class="table-card">
            <div class="table-header">
              <h3 class="table-name">{{ table.table_name }}</h3>
              <span class="column-count">{{ table.columns.length }} 컬럼</span>
            </div>
            
            <div class="columns-list">
              <div v-for="column in table.columns" :key="column.name" class="column-item">
                <span class="column-name">{{ column.name }}</span>
                <span class="column-type">{{ column.type }}</span>
                <span v-if="!column.nullable" class="column-required">필수</span>
              </div>
            </div>
            
            <div class="table-actions">
              <button @click="viewTableDetails(table)" class="btn-outline">상세 보기</button>
              <button @click="updateTableMetadata(table)" class="btn-outline">메타데이터 업데이트</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 빈 상태 -->
    <div v-else-if="selectedDb && schemas.length === 0" class="empty-state">
      <p>선택한 데이터베이스에서 스키마 정보를 찾을 수 없습니다.</p>
      <button @click="refreshSchemas" class="btn-primary">다시 시도</button>
    </div>

    <!-- 테이블 상세 모달 -->
    <div v-if="selectedTable" class="modal-overlay" @click="closeTableModal">
      <div class="modal-content table-detail-modal" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">{{ selectedTable.table_name }} 상세 정보</h3>
          <button @click="closeTableModal" class="modal-close">×</button>
        </div>
        <div class="modal-body">
          <div class="table-info">
            <h4 class="info-title">컬럼 정보</h4>
            <div class="columns-table">
              <table>
                <thead>
                  <tr>
                    <th>컬럼명</th>
                    <th>타입</th>
                    <th>NULL 허용</th>
                    <th>설명</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="column in selectedTable.columns" :key="column.name">
                    <td class="column-name-cell">{{ column.name }}</td>
                    <td class="column-type-cell">{{ column.type }}</td>
                    <td class="column-nullable-cell">
                      <span :class="['nullable-badge', column.nullable ? 'yes' : 'no']">
                        {{ column.nullable ? 'Yes' : 'No' }}
                      </span>
                    </td>
                    <td class="column-description-cell">
                      <input 
                        v-model="column.description" 
                        type="text" 
                        placeholder="컬럼 설명 추가..."
                        class="description-input"
                      />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeTableModal" class="btn-secondary">닫기</button>
          <button @click="saveTableMetadata" class="btn-primary">메타데이터 저장</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuth } from '@/composables/useAuth'

interface Column {
  name: string
  type: string
  nullable: boolean
  description?: string
}

interface Table {
  table_name: string
  columns: Column[]
}

interface Database {
  id: string
  name: string
  db_type: string
}

const { token } = useAuth()
const databases = ref<Database[]>([])
const selectedDb = ref('')
const schemas = ref<Table[]>([])
const selectedTable = ref<Table | null>(null)

const totalColumns = computed(() => {
  return schemas.value.reduce((total, table) => total + table.columns.length, 0)
})

const lastUpdated = computed(() => {
  return new Date().toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
})

const fetchDatabases = async () => {
  try {
    // 임시 데이터
    databases.value = [
      { id: '1', name: 'Production DB', db_type: 'postgresql' },
      { id: '2', name: 'Analytics DB', db_type: 'mysql' },
      { id: '3', name: 'Test DB', db_type: 'sqlite' }
    ]
  } catch (error) {
    console.error('Failed to fetch databases:', error)
  }
}

const fetchSchemas = async () => {
  if (!selectedDb.value) {
    schemas.value = []
    return
  }

  try {
    // 실제 API 호출 시 구현
    // const response = await fetch(`/api/v1/schema?db_id=${selectedDb.value}`, {
    //   headers: { 'Authorization': `Bearer ${token.value}` }
    // })
    // if (response.ok) {
    //   const data = await response.json()
    //   schemas.value = data.tables
    // }

    // 임시 데이터
    schemas.value = [
      {
        table_name: 'users',
        columns: [
          { name: 'id', type: 'integer', nullable: false },
          { name: 'email', type: 'varchar(255)', nullable: false },
          { name: 'full_name', type: 'varchar(100)', nullable: false },
          { name: 'created_at', type: 'timestamp', nullable: false },
          { name: 'updated_at', type: 'timestamp', nullable: false }
        ]
      },
      {
        table_name: 'queries',
        columns: [
          { name: 'id', type: 'integer', nullable: false },
          { name: 'user_id', type: 'integer', nullable: false },
          { name: 'question', type: 'text', nullable: false },
          { name: 'sql_query', type: 'text', nullable: false },
          { name: 'created_at', type: 'timestamp', nullable: false }
        ]
      },
      {
        table_name: 'connections',
        columns: [
          { name: 'id', type: 'integer', nullable: false },
          { name: 'name', type: 'varchar(100)', nullable: false },
          { name: 'db_type', type: 'varchar(50)', nullable: false },
          { name: 'host', type: 'varchar(255)', nullable: false },
          { name: 'port', type: 'integer', nullable: false }
        ]
      }
    ]
  } catch (error) {
    console.error('Failed to fetch schemas:', error)
  }
}

const refreshSchemas = async () => {
  await fetchSchemas()
  alert('스키마 정보가 새로고침되었습니다.')
}

const updateTableMetadata = async (table: Table) => {
  try {
    // 실제 API 호출 시 구현
    alert(`${table.table_name} 테이블의 메타데이터를 업데이트했습니다.`)
  } catch (error) {
    console.error('Failed to update metadata:', error)
    alert('메타데이터 업데이트에 실패했습니다.')
  }
}

const viewTableDetails = (table: Table) => {
  selectedTable.value = { ...table }
}

const closeTableModal = () => {
  selectedTable.value = null
}

const saveTableMetadata = async () => {
  try {
    // 실제 API 호출 시 구현
    alert('메타데이터가 저장되었습니다.')
    closeTableModal()
  } catch (error) {
    console.error('Failed to save metadata:', error)
    alert('메타데이터 저장에 실패했습니다.')
  }
}

onMounted(() => {
  fetchDatabases()
})
</script>

<style scoped>
.admin-schema {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.page-header {
  margin-bottom: 2rem;
}

.db-selector {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  align-items: center;
}

.db-select {
  flex: 1;
  max-width: 300px;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.875rem;
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: #f3f4f6;
  color: #374151;
  padding: 0.75rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover:not(:disabled) {
  background: #e5e7eb;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.schema-stats {
  display: flex;
  gap: 2rem;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.stat-label {
  font-size: 0.875rem;
  color: #6b7280;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.tables-grid {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
}

.table-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  padding: 1.5rem;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.table-name {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.column-count {
  background: #f3f4f6;
  color: #374151;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
}

.columns-list {
  margin-bottom: 1rem;
  max-height: 200px;
  overflow-y: auto;
}

.column-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f3f4f6;
}

.column-item:last-child {
  border-bottom: none;
}

.column-name {
  font-weight: 500;
  color: #374151;
  min-width: 100px;
}

.column-type {
  color: #6b7280;
  font-size: 0.875rem;
  font-family: monospace;
  flex: 1;
}

.column-required {
  background: #fef2f2;
  color: #991b1b;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

.table-actions {
  display: flex;
  gap: 0.5rem;
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

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #6b7280;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 1rem;
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

.table-detail-modal {
  max-width: 900px;
  width: 95%;
}

.modal-content {
  background: white;
  border-radius: 12px;
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

.info-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.columns-table {
  overflow-x: auto;
}

.columns-table table {
  width: 100%;
  border-collapse: collapse;
}

.columns-table th {
  background: #f9fafb;
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
}

.columns-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #f3f4f6;
}

.column-name-cell {
  font-weight: 500;
}

.column-type-cell {
  font-family: monospace;
  color: #6b7280;
}

.nullable-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.nullable-badge.yes {
  background: #fef3c7;
  color: #92400e;
}

.nullable-badge.no {
  background: #fee2e2;
  color: #991b1b;
}

.description-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 0.875rem;
}

.modal-footer {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  padding: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

@media (max-width: 768px) {
  .admin-schema {
    padding: 1rem;
  }
  
  .schema-stats {
    flex-direction: column;
    gap: 1rem;
  }
  
  .tables-grid {
    grid-template-columns: 1fr;
  }
  
  .db-selector {
    flex-direction: column;
    align-items: stretch;
  }
  
  .db-select {
    max-width: none;
  }
}
</style>
