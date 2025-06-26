<template>
  <div class="admin-users-container">
    <!-- 헤더 -->
    <div class="admin-header">
      <h2 class="admin-title">사용자 관리</h2>
      <button 
        @click="openCreateUserModal" 
        class="btn btn-primary"
        :disabled="loading"
      >
        <i class="fas fa-plus"></i>
        새 사용자 등록
      </button>
    </div>

    <!-- 검색 및 필터 -->
    <div class="search-filter-section">
      <div class="search-box">
        <i class="fas fa-search search-icon"></i>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="사용자 검색 (이름, 이메일, 회사)"
          class="search-input"
          @input="debouncedSearch"
        />
      </div>
      
      <div class="filter-section">
        <select v-model="selectedRole" @change="handleFilterChange" class="filter-select">
          <option value="">모든 역할</option>
          <option value="admin">관리자</option>
          <option value="analyst">일반 사용자</option>
        </select>
        
        <select v-model="selectedStatus" @change="handleFilterChange" class="filter-select">
          <option value="">모든 상태</option>
          <option value="active">활성</option>
          <option value="inactive">비활성</option>
        </select>
      </div>
    </div>

    <!-- 로딩 상태 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner">
        <i class="fas fa-spinner fa-spin"></i>
        <span>사용자 목록을 불러오는 중...</span>
      </div>
    </div>

    <!-- 에러 상태 -->
    <div v-else-if="error" class="error-container">
      <div class="error-message">
        <i class="fas fa-exclamation-triangle"></i>
        <span>{{ error }}</span>
        <button @click="fetchUsers" class="btn btn-secondary btn-sm">다시 시도</button>
      </div>
    </div>

    <!-- 사용자 목록 -->
    <div v-else class="users-content">
      <!-- 사용자 통계 -->
      <div class="users-stats">
        <div class="stat-item">
          <span class="stat-label">전체 사용자:</span>
          <span class="stat-value">{{ totalUsers }}명</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">검색 결과:</span>
          <span class="stat-value">{{ users?.length || 0 }}명</span>
        </div>
      </div>

      <!-- 사용자 테이블 -->
      <div class="users-table-container">
        <table class="users-table">
          <thead>
            <tr>
              <th>이름</th>
              <th>이메일</th>
              <th>회사</th>
              <th>역할</th>
              <th>상태</th>
              <th>가입일</th>
              <th>작업</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!users || users.length === 0">
              <td colspan="7" class="no-data">
                <div class="no-users-message">
                  <i class="fas fa-users"></i>
                  <span>{{ searchQuery ? '검색 결과가 없습니다.' : '사용자가 없습니다.' }}</span>
                </div>
              </td>
            </tr>
            <tr v-for="user in users || []" :key="user.id" class="user-row">
              <td class="user-name">{{ user.full_name }}</td>
              <td class="user-email">{{ user.email }}</td>
              <td class="user-company">{{ user.company || '-' }}</td>
              <td class="user-role">
                <span :class="getRoleClass(user.role)">
                  {{ getRoleLabel(user.role) }}
                </span>
              </td>
              <td class="user-status">
                <span :class="getStatusClass(user.is_active)">
                  {{ user.is_active ? '활성' : '비활성' }}
                </span>
              </td>
              <td class="user-date">{{ formatDate(user.created_at) }}</td>
              <td class="user-actions">
                <button 
                  @click="editUser(user)" 
                  class="btn btn-warning action-btn edit-btn icon-only"
                  title="사용자 정보 수정"
                >
                  <i class="fas fa-edit"></i>
                </button>
                <button 
                  @click="confirmDeleteUser(user)" 
                  class="btn btn-danger action-btn delete-btn icon-only"
                  title="사용자 삭제"
                  :disabled="user.id === currentUser?.id"
                >
                  <i class="fas fa-trash"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- 데이터가 없을 때 -->
        <div v-if="!loading && users.length === 0" class="no-data">
          <i class="fas fa-users"></i>
          <p v-if="searchQuery">검색 결과가 없습니다.</p>
          <p v-else>등록된 사용자가 없습니다.</p>
        </div>
      </div>

      <!-- 페이지네이션 -->
      <div v-if="totalUsers > pageSize" class="pagination-container">
        <div class="pagination-info">
          {{ (currentPage - 1) * pageSize + 1 }} - {{ Math.min(currentPage * pageSize, totalUsers) }} / {{ totalUsers }}
        </div>
        <div class="pagination">
          <button 
            @click="goToPage(1)" 
            :disabled="currentPage === 1"
            class="btn btn-secondary btn-sm"
          >
            <i class="fas fa-angle-double-left"></i>
          </button>
          <button 
            @click="goToPage(currentPage - 1)" 
            :disabled="currentPage === 1"
            class="btn btn-secondary btn-sm"
          >
            <i class="fas fa-angle-left"></i>
          </button>
          
          <span v-for="page in visiblePages" :key="page">
            <button 
              v-if="page !== '...'"
              @click="goToPage(page)" 
              :class="['btn', 'btn-sm', currentPage === page ? 'btn-primary' : 'btn-secondary']"
            >
              {{ page }}
            </button>
            <span v-else class="pagination-dots">...</span>
          </span>
          
          <button 
            @click="goToPage(currentPage + 1)" 
            :disabled="currentPage === totalPages"
            class="btn btn-secondary btn-sm"
          >
            <i class="fas fa-angle-right"></i>
          </button>
          <button 
            @click="goToPage(totalPages)" 
            :disabled="currentPage === totalPages"
            class="btn btn-secondary btn-sm"
          >
            <i class="fas fa-angle-double-right"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- 사용자 생성/수정 모달 -->
    <div v-if="showEditModal" class="modal-overlay" @click="closeEditModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ isEditing ? '사용자 수정' : '새 사용자 등록' }}</h3>
          <button @click="closeEditModal" class="btn-close">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="saveUser" class="user-form">
            <div class="form-group">
              <label for="full_name">이름 *</label>
              <input
                id="full_name"
                v-model="editForm.full_name"
                type="text"
                required
                class="form-control"
                placeholder="사용자 이름을 입력하세요"
              />
            </div>
            
            <div class="form-group">
              <label for="email">이메일 *</label>
              <input
                id="email"
                v-model="editForm.email"
                type="email"
                required
                class="form-control"
                placeholder="이메일을 입력하세요"
              />
            </div>
            
            <div class="form-group" v-if="!isEditing">
              <label for="password">비밀번호 *</label>
              <input
                id="password"
                v-model="editForm.password"
                type="password"
                required
                class="form-control"
                placeholder="비밀번호를 입력하세요 (최소 6자)"
              />
            </div>
            
            <div class="form-group" v-if="isEditing">
              <label for="new_password">새 비밀번호 (선택사항)</label>
              <input
                id="new_password"
                v-model="editForm.password"
                type="password"
                class="form-control"
                placeholder="변경할 비밀번호를 입력하세요 (최소 6자)"
              />
            </div>
            
            <div class="form-group">
              <label for="company">회사</label>
              <input
                id="company"
                v-model="editForm.company"
                type="text"
                class="form-control"
                placeholder="회사명을 입력하세요"
              />
            </div>
            
            <div class="form-group">
              <label for="role">역할 *</label>
              <select
                id="role"
                v-model="editForm.role"
                required
                class="form-control"
              >
                <option value="analyst">일반 사용자</option>
                <option value="admin">관리자</option>
              </select>
            </div>
            
            <div class="form-group" v-if="isEditing">
              <label class="checkbox-label">
                <input
                  type="checkbox"
                  v-model="editForm.is_active"
                />
                <span>활성 상태</span>
              </label>
            </div>
            
            <div class="form-actions">
              <button 
                type="submit" 
                class="btn btn-primary"
                :disabled="submitting"
              >
                <i v-if="submitting" class="fas fa-spinner fa-spin"></i>
                <i v-else class="fas fa-save"></i>
                {{ submitting ? '저장 중...' : (isEditing ? '수정' : '등록') }}
              </button>
              <button 
                type="button" 
                @click="closeEditModal" 
                class="btn btn-secondary"
                :disabled="submitting"
              >
                취소
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 삭제 확인 모달 -->
    <div v-if="showDeleteModal" class="modal-overlay" @click="closeDeleteModal">
      <div class="modal-content modal-sm" @click.stop>
        <div class="modal-header">
          <h3>사용자 삭제 확인</h3>
          <button @click="closeDeleteModal" class="btn-close">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="delete-confirmation">
            <i class="fas fa-exclamation-triangle text-danger"></i>
            <p>정말로 다음 사용자를 삭제하시겠습니까?</p>
            <div class="user-info">
              <strong>{{ userToDelete?.full_name }}</strong><br>
              <span class="text-muted">{{ userToDelete?.email }}</span>
            </div>
            <p class="warning-text">이 작업은 되돌릴 수 없습니다.</p>
          </div>
        </div>
        <div class="modal-footer">
          <button 
            @click="deleteUser" 
            class="btn btn-danger"
            :disabled="deleting"
          >
            <i v-if="deleting" class="fas fa-spinner fa-spin"></i>
            <i v-else class="fas fa-trash"></i>
            {{ deleting ? '삭제 중...' : '삭제' }}
          </button>
          <button 
            @click="closeDeleteModal" 
            class="btn btn-secondary"
            :disabled="deleting"
          >
            취소
          </button>
        </div>
      </div>
    </div>

    <!-- 알림 토스트 -->
    <div v-if="notification.show" :class="['notification', notification.type]">
      <i :class="getNotificationIcon(notification.type)"></i>
      <span>{{ notification.message }}</span>
      <button @click="hideNotification" class="notification-close">
        <i class="fas fa-times"></i>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useAuth } from '@/composables/useAuth'
import { useApi } from '@/composables/useApi'
import type { User } from '@/types/api'

// Composables
const { user: currentUser } = useAuth()
const { getAllUsers, createUser, updateUser, deleteUser: deleteUserApi } = useApi()

// State
const users = ref<User[]>([])
const totalUsers = ref(0)
const loading = ref(false)
const error = ref('')

// Pagination
const currentPage = ref(1)
const pageSize = ref(10)
const totalPages = computed(() => Math.ceil(totalUsers.value / pageSize.value))

// Search & Filter
const searchQuery = ref('')
const selectedRole = ref('')
const selectedStatus = ref('')
const searchTimeout = ref<ReturnType<typeof setTimeout> | null>(null)

// Modals
const showEditModal = ref(false)
const showDeleteModal = ref(false)
const selectedUser = ref<User | null>(null)
const userToDelete = ref<User | null>(null)

// Form
const isEditing = ref(false)
const submitting = ref(false)
const deleting = ref(false)
const editForm = ref({
  full_name: '',
  email: '',
  password: '',
  company: '',
  role: 'analyst',
  is_active: true
})

// Notification
const notification = ref({
  show: false,
  type: 'success',
  message: ''
})

// Computed
const visiblePages = computed(() => {
  const current = currentPage.value
  const total = totalPages.value
  const pages: (number | string)[] = []
  
  if (total <= 7) {
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    if (current <= 4) {
      for (let i = 1; i <= 5; i++) pages.push(i)
      pages.push('...')
      pages.push(total)
    } else if (current >= total - 3) {
      pages.push(1)
      pages.push('...')
      for (let i = total - 4; i <= total; i++) pages.push(i)
    } else {
      pages.push(1)
      pages.push('...')
      for (let i = current - 1; i <= current + 1; i++) pages.push(i)
      pages.push('...')
      pages.push(total)
    }
  }
  
  return pages
})

// Methods
const fetchUsers = async () => {
  try {
    loading.value = true
    error.value = ''
    
    const response = await getAllUsers(
      currentPage.value,
      pageSize.value,
      searchQuery.value || undefined,
      selectedRole.value || undefined,
      selectedStatus.value || undefined
    )
    
    // API 응답 구조 확인 및 안전한 접근
    console.log('API Response:', response) // 디버깅용
    
    if (response && response.users) {
      users.value = response.users
      totalUsers.value = response.total_count || 0
    } else {
      console.error('Unexpected API response structure:', response)
      users.value = []
      totalUsers.value = 0
      error.value = '사용자 데이터 형식이 올바르지 않습니다.'
    }
  } catch (err: any) {
    // Check if it's an authentication error
    if (err.response?.status === 401) {
      error.value = 'Authentication required. Please log in again.'
      // Token expiration will be handled by the auth interceptor
    } else {
      error.value = err.response?.data?.detail || err.message || '사용자 목록을 불러올 수 없습니다.'
    }
    console.error('사용자 목록 조회 실패:', err)
    users.value = []
    totalUsers.value = 0
  } finally {
    loading.value = false
  }
}

const debouncedSearch = () => {
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value)
  }
  searchTimeout.value = setTimeout(() => {
    currentPage.value = 1
    fetchUsers()
  }, 500)
}

const handleFilterChange = () => {
  currentPage.value = 1
  fetchUsers()
}

const goToPage = (page: number | string) => {
  const pageNum = typeof page === 'string' ? parseInt(page) : page
  if (pageNum >= 1 && pageNum <= totalPages.value) {
    currentPage.value = pageNum
    fetchUsers()
  }
}

// Modal methods
const openCreateUserModal = () => {
  isEditing.value = false
  editForm.value = {
    full_name: '',
    email: '',
    password: '',
    company: '',
    role: 'analyst',
    is_active: true
  }
  showEditModal.value = true
}

const editUser = (user: User) => {
  isEditing.value = true
  editForm.value = {
    full_name: user.full_name,
    email: user.email,
    password: '',
    company: user.company || '',
    role: user.role,
    is_active: user.is_active
  }
  selectedUser.value = user
  showEditModal.value = true
}

const closeEditModal = () => {
  showEditModal.value = false
  selectedUser.value = null
  isEditing.value = false
}

const saveUser = async () => {
  try {
    submitting.value = true
    
    if (isEditing.value && selectedUser.value) {
      // 수정
      const updateData: any = {
        full_name: editForm.value.full_name,
        email: editForm.value.email,
        company: editForm.value.company,
        role: editForm.value.role,
        is_active: editForm.value.is_active
      }
      
      if (editForm.value.password) {
        updateData.password = editForm.value.password
      }
      
      await updateUser(selectedUser.value.id, updateData)
      showNotification('success', '사용자 정보가 성공적으로 수정되었습니다.')
    } else {
      // 생성
      await createUser({
        full_name: editForm.value.full_name,
        email: editForm.value.email,
        password: editForm.value.password,
        company: editForm.value.company,
        role: editForm.value.role
      })
      showNotification('success', '새 사용자가 성공적으로 등록되었습니다.')
    }
    
    closeEditModal()
    fetchUsers()
  } catch (err: any) {
    if (err.response?.status === 401) {
      showNotification('error', 'Your session has expired. Please log in again.')
    } else {
      showNotification('error', err.response?.data?.detail || err.message || '사용자 저장에 실패했습니다.')
    }
  } finally {
    submitting.value = false
  }
}

const confirmDeleteUser = (user: User) => {
  userToDelete.value = user
  showDeleteModal.value = true
}

const closeDeleteModal = () => {
  showDeleteModal.value = false
  userToDelete.value = null
}

const deleteUser = async () => {
  if (!userToDelete.value) return
  
  try {
    deleting.value = true
    await deleteUserApi(userToDelete.value.id)
    showNotification('success', '사용자가 성공적으로 삭제되었습니다.')
    closeDeleteModal()
    fetchUsers()
  } catch (err: any) {
    if (err.response?.status === 401) {
      showNotification('error', 'Your session has expired. Please log in again.')
    } else {
      showNotification('error', err.response?.data?.detail || err.message || '사용자 삭제에 실패했습니다.')
    }
  } finally {
    deleting.value = false
  }
}

// Utility methods
const formatDate = (dateString: string | undefined | null) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const getRoleClass = (role: string) => {
  return {
    'role-badge': true,
    'role-admin': role === 'admin',
    'role-user': role === 'analyst'
  }
}

const getRoleLabel = (role: string) => {
  return role === 'admin' ? '관리자' : '일반 사용자'
}

const getStatusClass = (isActive: boolean) => {
  return {
    'status-badge': true,
    'status-active': isActive,
    'status-inactive': !isActive
  }
}

const showNotification = (type: string, message: string) => {
  notification.value = {
    show: true,
    type,
    message
  }
  
  setTimeout(() => {
    hideNotification()
  }, 5000)
}

const hideNotification = () => {
  notification.value.show = false
}

const getNotificationIcon = (type: string) => {
  switch (type) {
    case 'success': return 'fas fa-check-circle'
    case 'error': return 'fas fa-exclamation-circle'
    case 'warning': return 'fas fa-exclamation-triangle'
    default: return 'fas fa-info-circle'
  }
}

// Lifecycle
onMounted(() => {
  fetchUsers()
  
  // Listen for token expiration events
  const handleTokenExpired = (event: CustomEvent) => {
    showNotification('error', event.detail.message || 'Your session has expired. Please log in again.')
  }
  
  window.addEventListener('token-expired', handleTokenExpired as EventListener)
  
  // Cleanup listener on unmount
  onUnmounted(() => {
    window.removeEventListener('token-expired', handleTokenExpired as EventListener)
  })
})
</script>

<style scoped>
.admin-users-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e9ecef;
}

.admin-title {
  margin: 0;
  color: #333;
  font-size: 24px;
  font-weight: 600;
}

.search-filter-section {
  display: flex;
  gap: 20px;
  margin-bottom: 25px;
  flex-wrap: wrap;
}

.search-box {
  position: relative;
  flex: 1;
  min-width: 300px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #6c757d;
}

.search-input {
  width: 100%;
  padding: 10px 12px 10px 40px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
}

.search-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.filter-section {
  display: flex;
  gap: 15px;
}

.filter-select {
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  min-width: 120px;
}

.loading-container {
  text-align: center;
  padding: 60px 20px;
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  color: #6c757d;
}

.loading-spinner i {
  font-size: 24px;
}

.error-container {
  text-align: center;
  padding: 60px 20px;
}

.error-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  color: #dc3545;
}

.users-stats {
  display: flex;
  gap: 30px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-item {
  display: flex;
  gap: 8px;
}

.stat-label {
  color: #6c757d;
  font-weight: 500;
}

.stat-value {
  color: #333;
  font-weight: 600;
}

.users-table-container {
  background: white;
  border-radius: 8px;
  overflow-x: auto;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 1000px;
}

.users-table th {
  background: #f8f9fa;
  padding: 15px 20px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #e9ecef;
  white-space: nowrap;
}

.users-table td {
  padding: 15px 20px;
  border-bottom: 1px solid #e9ecef;
  vertical-align: middle;
}

/* 간단한 컬럼 너비 설정 */
.users-table th:nth-child(1), .users-table td:nth-child(1) { width: 150px; } /* 이름 */
.users-table th:nth-child(2), .users-table td:nth-child(2) { width: 250px; } /* 이메일 */
.users-table th:nth-child(3), .users-table td:nth-child(3) { width: 200px; } /* 회사 */
.users-table th:nth-child(4), .users-table td:nth-child(4) { width: 100px; text-align: center; } /* 역할 */
.users-table th:nth-child(5), .users-table td:nth-child(5) { width: 80px; text-align: center; } /* 상태 */
.users-table th:nth-child(6), .users-table td:nth-child(6) { width: 120px; } /* 가입일 */
.users-table th:nth-child(7), .users-table td:nth-child(7) { width: 100px; text-align: center; } /* 작업 */

.user-row:hover {
  background: #f8f9fa;
}

.user-email {
  color: #007bff;
  word-break: break-all;
}

.user-name {
  font-weight: 500;
}

.user-company {
  color: #666;
}

.role-badge {
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
  display: inline-block;
  min-width: 60px;
  text-align: center;
}

.role-admin {
  background: #dc3545;
  color: white;
}

.role-user {
  background: #28a745;
  color: white;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  display: inline-block;
  min-width: 50px;
  text-align: center;
}

.status-active {
  background: #28a745;
  color: white;
}

.status-inactive {
  background: #6c757d;
  color: white;
}

.user-actions {
  display: flex;
  gap: 6px;
  justify-content: center;
  align-items: center;
}

.action-btn {
  padding: 8px 16px;
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: 80px;
  height: 36px;
  position: relative;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 아이콘 전용 버튼 스타일 */
.action-btn.icon-only {
  padding: 8px;
  min-width: 36px;
  width: 36px;
  gap: 0;
}

.action-btn i {
  font-size: 14px;
  transition: all 0.2s ease;
  font-weight: 900;
  min-width: 16px;
  position: relative;
  font-family: "Font Awesome 6 Free", "Font Awesome 5 Free", "FontAwesome";
}

.action-btn .btn-text {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.5px;
  min-width: 32px;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
}

.action-btn:hover i {
  transform: scale(1.1);
}

.action-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.action-btn:disabled:hover {
  transform: none;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.action-btn:disabled i {
  transform: none;
}

/* Edit Button Specific Styles */
.edit-btn {
  background: linear-gradient(135deg, #ffc107 0%, #ffb300 100%);
  color: #212529;
  border-color: #ffc107;
}

.edit-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #ffb300 0%, #ff8f00 100%);
  border-color: #ffb300;
  color: #000;
}

/* Delete Button Specific Styles */
.delete-btn {
  background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
  color: white;
  border-color: #dc3545;
}

.delete-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #c82333 0%, #a71e2a 100%);
  border-color: #c82333;
}

.delete-btn:disabled {
  background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
  border-color: #dc3545;
}

.btn {
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #545b62;
}

.btn-info {
  background: #17a2b8;
  color: white;
}

.btn-info:hover:not(:disabled) {
  background: #117a8b;
}

.btn-warning {
  background: #ffc107;
  color: #212529;
}

.btn-warning:hover:not(:disabled) {
  background: #e0a800;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #c82333;
}

.btn-sm {
  padding: 6px 8px;
  font-size: 12px;
}

.no-data {
  text-align: center;
  padding: 60px 20px;
  color: #6c757d;
}

.no-data i {
  font-size: 48px;
  margin-bottom: 15px;
  opacity: 0.5;
}

.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
}

.pagination {
  display: flex;
  gap: 5px;
  align-items: center;
}

.pagination-dots {
  padding: 0 8px;
  color: #6c757d;
}

.pagination-info {
  color: #6c757d;
  font-size: 14px;
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
  border-radius: 8px;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.modal-sm {
  max-width: 400px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e9ecef;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.btn-close {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #6c757d;
  padding: 5px;
}

.btn-close:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  padding: 20px;
  border-top: 1px solid #e9ecef;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.user-detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.detail-item label {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.detail-item span {
  color: #6c757d;
}

.user-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-group label {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.form-control {
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.form-control:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.delete-confirmation {
  text-align: center;
}

.delete-confirmation i {
  font-size: 48px;
  margin-bottom: 15px;
}

.user-info {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  margin: 15px 0;
}

.warning-text {
  color: #dc3545;
  font-size: 14px;
  margin-top: 10px;
}

.text-danger {
  color: #dc3545;
}

.text-muted {
  color: #6c757d;
}

/* Notification */
.notification {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 15px 20px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 10px;
  z-index: 1100;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.notification.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.notification.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.notification.warning {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.notification-close {
  background: none;
  border: none;
  cursor: pointer;
  color: inherit;
  opacity: 0.7;
}

.notification-close:hover {
  opacity: 1;
}

/* Action Button Specific Styles */
.btn-warning.action-btn {
  background: #ffc107;
  color: #212529;
  border: 2px solid #ffc107;
}

.btn-warning.action-btn:hover:not(:disabled) {
  background: #e0a800;
  border-color: #e0a800;
  color: #212529;
}

.btn-danger.action-btn {
  background: #dc3545;
  color: white;
  border: 2px solid #dc3545;
}

.btn-danger.action-btn:hover:not(:disabled) {
  background: #c82333;
  border-color: #c82333;
  color: white;
}

.btn-danger.action-btn:disabled {
  background: #dc3545;
  border-color: #dc3545;
  opacity: 0.5;
}

@media (max-width: 768px) {
  .admin-header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .search-filter-section {
    flex-direction: column;
  }
  
  .filter-section {
    flex-wrap: wrap;
  }
  
  .users-stats {
    flex-direction: column;
    gap: 10px;
  }
  
  .users-table {
    font-size: 14px;
    min-width: 800px;
  }
  
  .users-table th,
  .users-table td {
    padding: 10px 12px;
  }
  
  .action-btn.icon-only {
    padding: 6px;
    min-width: 32px;
    width: 32px;
    height: 32px;
  }
  
  .action-btn i {
    font-size: 12px;
  }
  
  .user-detail-grid {
    grid-template-columns: 1fr;
  }
  
  .pagination-container {
    flex-direction: column;
    gap: 15px;
  }
  
  .pagination {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>
