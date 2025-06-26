<template>
  <div class="admin-dashboard">
    <!-- 통계 카드 섹션 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">
          <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
          </svg>
        </div>
        <div class="stat-content">
          <h3 class="stat-title">총 사용자</h3>
          <p class="stat-value">{{ stats.totalUsers || 0 }}</p>
          <p class="stat-change">활성 사용자: {{ stats.activeUsers || 0 }}</p>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">
          <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
          </svg>
        </div>
        <div class="stat-content">
          <h3 class="stat-title">총 쿼리 수</h3>
          <p class="stat-value">{{ stats.totalQueries || 0 }}</p>
          <p class="stat-change">오늘: {{ stats.todayQueries || 0 }}</p>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">
          <svg class="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path>
          </svg>
        </div>
        <div class="stat-content">
          <h3 class="stat-title">토큰 사용량</h3>
          <p class="stat-value">{{ formatNumber(stats.totalTokens) || 0 }}</p>
          <p class="stat-change">이번 달: {{ formatNumber(stats.monthlyTokens) || 0 }}</p>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">
          <svg class="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>
          </svg>
        </div>
        <div class="stat-content">
          <h3 class="stat-title">시스템 상태</h3>
          <p class="stat-value">{{ systemStatus }}</p>
          <p class="stat-change">마지막 확인: {{ lastChecked }}</p>
        </div>
      </div>
    </div>

    <!-- 빠른 액션 버튼 -->
    <div class="quick-actions">
      <h2 class="text-xl font-semibold text-gray-900 mb-4">빠른 작업</h2>
      <div class="action-buttons">
        <button @click="$emit('navigate-to', 'admin-users')" class="action-button">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
          </svg>
          사용자 관리
        </button>
        
        <button @click="$emit('navigate-to', 'admin-prompts')" class="action-button">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          프롬프트 관리
        </button>
        
        <button @click="$emit('navigate-to', 'admin-db-connections')" class="action-button">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"></path>
          </svg>
          DB 연결 관리
        </button>
        
        <button @click="clearCache" class="action-button" :disabled="loading">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
          {{ loading ? '처리중...' : '캐시 삭제' }}
        </button>
      </div>
    </div>

    <!-- 최근 활동 -->
    <div class="recent-activity">
      <h2 class="text-xl font-semibold text-gray-900 mb-4">최근 활동</h2>
      <div class="activity-list">
        <div v-if="recentActivities.length === 0" class="text-gray-500 text-center py-4">
          최근 활동이 없습니다.
        </div>
        <div v-else v-for="activity in recentActivities" :key="activity.id" class="activity-item">
          <div class="activity-content">
            <p class="activity-text">{{ activity.description }}</p>
            <span class="activity-time">{{ formatTime(activity.timestamp) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuth } from '@/composables/useAuth'

// Define emits
const emit = defineEmits<{
  'navigate-to': [tabName: string]
}>()

interface AdminStats {
  totalUsers: number
  activeUsers: number
  totalQueries: number
  todayQueries: number
  totalTokens: number
  monthlyTokens: number
}

interface Activity {
  id: string
  description: string
  timestamp: string
}

const { token } = useAuth()
const stats = ref<AdminStats>({
  totalUsers: 0,
  activeUsers: 0,
  totalQueries: 0,
  todayQueries: 0,
  totalTokens: 0,
  monthlyTokens: 0
})
const loading = ref(false)
const recentActivities = ref<Activity[]>([])

const systemStatus = computed(() => 'ONLINE')
const lastChecked = computed(() => new Date().toLocaleTimeString())

const fetchAdminStats = async () => {
  try {
    const response = await fetch('/api/v1/auth/admin/stats', {
      headers: {
        'Authorization': `Bearer ${token.value}`,
        'Content-Type': 'application/json'
      }
    })
    if (response.ok) {
      const data = await response.json()
      stats.value = data
    }
  } catch (error) {
    console.error('Failed to fetch admin stats:', error)
  }
}

const clearCache = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/v1/admin/system/cache/clear', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token.value}`,
        'Content-Type': 'application/json'
      }
    })
    if (response.ok) {
      alert('캐시가 성공적으로 삭제되었습니다.')
    } else {
      alert('캐시 삭제에 실패했습니다.')
    }
  } catch (error) {
    console.error('Failed to clear cache:', error)
    alert('캐시 삭제 중 오류가 발생했습니다.')
  } finally {
    loading.value = false
  }
}

const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const formatTime = (timestamp: string): string => {
  return new Date(timestamp).toLocaleString('ko-KR')
}

onMounted(() => {
  fetchAdminStats()
})
</script>

<style scoped>
.admin-dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.dashboard-header {
  margin-bottom: 2rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  flex-shrink: 0;
  padding: 0.75rem;
  border-radius: 8px;
  background: #f3f4f6;
}

.stat-content {
  flex: 1;
}

.stat-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
  margin: 0 0 0.25rem 0;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 0.25rem 0;
}

.stat-change {
  font-size: 0.75rem;
  color: #6b7280;
  margin: 0;
}

.quick-actions {
  margin-bottom: 2rem;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.action-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: #2563eb;
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: background-color 0.2s;
}

.action-button:hover:not(:disabled) {
  background: #1d4ed8;
}

.action-button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.recent-activity {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
}

.activity-list {
  max-height: 300px;
  overflow-y: auto;
}

.activity-item {
  padding: 0.75rem 0;
  border-bottom: 1px solid #f3f4f6;
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.activity-text {
  margin: 0;
  color: #374151;
}

.activity-time {
  font-size: 0.75rem;
  color: #6b7280;
}

@media (max-width: 768px) {
  .admin-dashboard {
    padding: 1rem;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .action-button {
    justify-content: center;
  }
}
</style>
