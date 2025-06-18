<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center">
        <Activity class="w-5 h-5 text-blue-600 mr-2" />
        <h3 class="text-lg font-semibold text-gray-900">토큰 사용량</h3>
      </div>
      <button
        @click="refresh"
        :disabled="loading"
        class="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50"
        title="새로고침"
      >
        <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading && !hasDashboardData" class="flex items-center justify-center py-8">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
      <div class="flex items-center">
        <AlertCircle class="w-5 h-5 text-red-600 mr-2" />
        <p class="text-red-800">{{ error }}</p>
      </div>
    </div>

    <!-- Token Usage Dashboard -->
    <div v-else-if="hasDashboardData" class="space-y-4">
      <!-- Usage Overview -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Monthly Usage -->
        <div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-blue-900">이번 달 사용량</p>
              <p class="text-2xl font-bold text-blue-600">
                {{ formatNumber(dashboardData.current_month.usage.total_tokens) }}
              </p>
              <p class="text-xs text-blue-700 mt-1">
                {{ dashboardData.current_month.usage.query_count }}회 요청
              </p>
            </div>
            <div class="text-right">
              <div class="text-xs text-blue-600 mb-1">
                {{ currentUsagePercentage }}%
              </div>
              <div class="w-12 h-2 bg-blue-200 rounded-full overflow-hidden">
                <div 
                  class="h-full transition-all duration-300"
                  :class="currentUsagePercentage >= 90 ? 'bg-red-500' : currentUsagePercentage >= 70 ? 'bg-yellow-500' : 'bg-blue-500'"
                  :style="{ width: `${Math.min(currentUsagePercentage, 100)}%` }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Daily Usage -->
        <div class="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-4 border border-green-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-green-900">오늘 사용량</p>
              <p class="text-2xl font-bold text-green-600">
                {{ formatNumber(dashboardData.rate_limit.usage.daily) }}
              </p>
              <p class="text-xs text-green-700 mt-1">
                잔여: {{ formatNumber(dashboardData.current_month.remaining.daily) }}
              </p>
            </div>
            <div class="text-right">
              <div class="text-xs text-green-600 mb-1">
                {{ dailyUsagePercentage }}%
              </div>
              <div class="w-12 h-2 bg-green-200 rounded-full overflow-hidden">
                <div 
                  class="h-full bg-green-500 transition-all duration-300"
                  :style="{ width: `${Math.min(dailyUsagePercentage, 100)}%` }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Rate Limit Status -->
        <div 
          class="rounded-lg p-4 border"
          :class="isRateLimited ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'"
        >
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium" :class="isRateLimited ? 'text-red-900' : 'text-green-900'">
                상태
              </p>
              <p class="text-lg font-bold" :class="isRateLimited ? 'text-red-600' : 'text-green-600'">
                {{ isRateLimited ? '제한됨' : '정상' }}
              </p>
              <p class="text-xs mt-1" :class="isRateLimited ? 'text-red-700' : 'text-green-700'">
                시간당: {{ formatNumber(dashboardData.rate_limit.usage.hourly) }}
              </p>
            </div>
            <div class="text-right">
              <component 
                :is="isRateLimited ? AlertTriangle : CheckCircle" 
                class="w-8 h-8"
                :class="isRateLimited ? 'text-red-500' : 'text-green-500'"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Rate Limit Warning -->
      <div 
        v-if="isRateLimited" 
        class="bg-yellow-50 border border-yellow-200 rounded-lg p-4"
      >
        <div class="flex items-center">
          <AlertTriangle class="w-5 h-5 text-yellow-600 mr-2" />
          <div>
            <p class="text-yellow-800 font-medium">사용량 제한 알림</p>
            <p class="text-yellow-700 text-sm mt-1">
              현재 요청이 제한되었습니다. 잠시 후 다시 시도해주세요.
            </p>
            <div class="mt-2 text-xs text-yellow-600">
              <span v-if="dashboardData.rate_limit.status.daily_exceeded">일일 한도 초과 • </span>
              <span v-if="dashboardData.rate_limit.status.monthly_exceeded">월간 한도 초과 • </span>
              <span v-if="dashboardData.rate_limit.status.hourly_exceeded">시간당 한도 초과</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Usage Trends (Compact View) -->
      <div v-if="Object.keys(dashboardData.trends).length > 0" class="mt-4">
        <h4 class="text-sm font-medium text-gray-900 mb-2">최근 7일 사용량</h4>
        <div class="flex items-end space-x-1 h-16">
          <div 
            v-for="(usage, date) in getRecentTrends()" 
            :key="date"
            class="flex-1 bg-blue-200 rounded-t-sm relative group cursor-pointer"
            :style="{ height: `${Math.max((usage.total_tokens / getMaxDailyUsage()) * 100, 2)}%` }"
            :title="`${date}: ${formatNumber(usage.total_tokens)} 토큰, ${usage.query_count}회 요청`"
          >
            <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-1 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
              {{ formatDate(date) }}<br>
              {{ formatNumber(usage.total_tokens) }} 토큰<br>
              {{ usage.query_count }}회 요청
            </div>
          </div>
        </div>
        <div class="flex justify-between text-xs text-gray-500 mt-1">
          <span>7일 전</span>
          <span>오늘</span>
        </div>
      </div>

      <!-- Models Used -->
      <div v-if="Object.keys(dashboardData.models).length > 0" class="mt-4">
        <h4 class="text-sm font-medium text-gray-900 mb-2">사용된 모델</h4>
        <div class="space-y-2">
          <div 
            v-for="(usage, model) in dashboardData.models" 
            :key="model"
            class="flex items-center justify-between text-sm"
          >
            <span class="text-gray-700">{{ model }}</span>
            <div class="flex items-center space-x-2">
              <span class="text-blue-600 font-medium">{{ formatNumber(usage.total_tokens) }}</span>
              <span class="text-gray-500">({{ usage.query_count }}회)</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Last Updated -->
      <div class="text-xs text-gray-500 text-center pt-2 border-t border-gray-100">
        마지막 업데이트: {{ formatLastUpdated() }}
      </div>
    </div>

    <!-- No Data State -->
    <div v-else class="text-center py-8">
      <Activity class="w-12 h-12 text-gray-400 mx-auto mb-4" />
      <p class="text-gray-500">토큰 사용량 정보가 없습니다</p>
      <button
        @click="refresh"
        class="mt-2 px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        데이터 로드
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { 
  Activity, 
  RefreshCw, 
  AlertCircle, 
  AlertTriangle, 
  CheckCircle 
} from 'lucide-vue-next'
import { useTokenUsage } from '../composables/useTokenUsage'

// Use the token usage composable
const {
  dashboardData,
  loading,
  error,
  hasDashboardData,
  isRateLimited,
  currentUsagePercentage,
  dailyUsagePercentage,
  formatNumber,
  getDashboardData
} = useTokenUsage()

// Load data on component mount
onMounted(() => {
  refresh()
})

// Refresh data
const refresh = async () => {
  try {
    await getDashboardData()
  } catch (err) {
    console.error('Failed to refresh token usage data:', err)
  }
}

// Get recent trends (last 7 days)
const getRecentTrends = () => {
  if (!dashboardData.value?.trends) return {}
  
  const dates = Object.keys(dashboardData.value.trends).sort()
  const recentDates = dates.slice(-7)
  
  const recentTrends: Record<string, any> = {}
  recentDates.forEach(date => {
    recentTrends[date] = dashboardData.value!.trends[date]
  })
  
  return recentTrends
}

// Get maximum daily usage for chart scaling
const getMaxDailyUsage = () => {
  if (!dashboardData.value?.trends) return 1
  
  const usages = Object.values(dashboardData.value.trends).map(usage => usage.total_tokens)
  return Math.max(...usages, 1)
}

// Format date for display
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })
}

// Format last updated time
const formatLastUpdated = () => {
  if (!dashboardData.value?.generated_at) return '알 수 없음'
  
  const date = new Date(dashboardData.value.generated_at)
  return date.toLocaleString('ko-KR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
/* Custom scrollbar for trends */
.trends-container::-webkit-scrollbar {
  height: 4px;
}

.trends-container::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 2px;
}

.trends-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 2px;
}

.trends-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
