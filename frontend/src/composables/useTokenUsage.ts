/**
 * Token usage composable for managing LLM token consumption tracking
 * Provides user-level token usage statistics and rate limiting
 */

import { ref, reactive, computed } from 'vue'
import type { Ref } from 'vue'
import { useAuth } from './useAuth'

// Types
interface TokenUsage {
  total_tokens: number
  prompt_tokens: number
  completion_tokens: number
}

interface TokenUsageStats {
  user_id: string
  summary: TokenUsage & {
    last_updated?: string
  }
  period_stats: TokenUsage & {
    start_date?: string
    end_date?: string
    total_queries: number
    query_count: number
    models_used: string[]
  }
  last_updated?: string
  generated_at: string
  details?: {
    daily_usage: Record<string, { total_tokens: number; query_count: number }>
    model_usage: Record<string, { total_tokens: number; query_count: number }>
  }
}

interface TokenLimits {
  user_id: string
  limits: {
    daily_limit: number
    monthly_limit: number
    rate_limit: number
  }
  current_usage: {
    total: number
    daily: number
    monthly: number
  }
  remaining: {
    daily: number
    monthly: number
  }
  status: {
    daily_exceeded: boolean
    monthly_exceeded: boolean
  }
}

interface RateLimitStatus {
  user_id: string
  allowed: boolean
  limits_status: {
    daily_exceeded: boolean
    monthly_exceeded: boolean
    hourly_exceeded: boolean
  }
  usage: {
    hourly: number
    daily: number
    monthly: number
  }
  limits: {
    daily_limit: number
    monthly_limit: number
    rate_limit: number
  }
}

interface DashboardData {
  user_id: string
  current_month: {
    usage: TokenUsage & { total_queries: number; query_count: number }
    limits: { daily_limit: number; monthly_limit: number; rate_limit: number }
    remaining: { daily: number; monthly: number }
    status: { daily_exceeded: boolean; monthly_exceeded: boolean }
  }
  rate_limit: {
    allowed: boolean
    status: { daily_exceeded: boolean; monthly_exceeded: boolean; hourly_exceeded: boolean }
    usage: { hourly: number; daily: number; monthly: number }
  }
  trends: Record<string, { total_tokens: number; query_count: number }>
  models: Record<string, { total_tokens: number; query_count: number }>
  last_updated?: string
  generated_at: string
}

// Global state
const tokenStats: Ref<TokenUsageStats | null> = ref(null)
const tokenLimits: Ref<TokenLimits | null> = ref(null)
const rateLimitStatus: Ref<RateLimitStatus | null> = ref(null)
const dashboardData: Ref<DashboardData | null> = ref(null)
const loading = ref(false)
const error = ref<string | null>(null)

export function useTokenUsage() {
  const { authFetch, isAuthenticated } = useAuth()

  // API helper function
  const apiCall = async <T>(endpoint: string): Promise<T> => {
    if (!isAuthenticated.value) {
      throw new Error('Authentication required')
    }

    const response = await authFetch(endpoint)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  // Get user token usage statistics
  const getTokenUsage = async (
    startDate?: string,
    endDate?: string,
    includeDetails: boolean = false
  ): Promise<TokenUsageStats> => {
    loading.value = true
    error.value = null

    try {
      const params = new URLSearchParams()
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      if (includeDetails) params.append('include_details', 'true')

      const data = await apiCall<TokenUsageStats>(
        `/api/v1/tokens/usage?${params.toString()}`
      )

      tokenStats.value = data
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to get token usage'
      throw err
    } finally {
      loading.value = false
    }
  }

  // Get user token limits
  const getTokenLimits = async (): Promise<TokenLimits> => {
    loading.value = true
    error.value = null

    try {
      const data = await apiCall<TokenLimits>('/api/v1/tokens/limits')
      tokenLimits.value = data
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to get token limits'
      throw err
    } finally {
      loading.value = false
    }
  }

  // Check rate limit status
  const checkRateLimit = async (): Promise<RateLimitStatus> => {
    try {
      const data = await apiCall<RateLimitStatus>('/api/v1/tokens/rate-limit-check')
      rateLimitStatus.value = data
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to check rate limit'
      throw err
    }
  }

  // Get dashboard data
  const getDashboardData = async (): Promise<DashboardData> => {
    loading.value = true
    error.value = null

    try {
      const data = await apiCall<DashboardData>('/api/v1/tokens/dashboard')
      dashboardData.value = data
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to get dashboard data'
      throw err
    } finally {
      loading.value = false
    }
  }

  // Refresh all token data
  const refreshTokenData = async (): Promise<void> => {
    if (!isAuthenticated.value) return

    await Promise.allSettled([
      getTokenUsage(),
      getTokenLimits(),
      checkRateLimit(),
      getDashboardData()
    ])
  }

  // Computed properties
  const hasTokenData = computed(() => tokenStats.value !== null)
  const hasLimitsData = computed(() => tokenLimits.value !== null)
  const hasDashboardData = computed(() => dashboardData.value !== null)

  const isRateLimited = computed(() => {
    return rateLimitStatus.value ? !rateLimitStatus.value.allowed : false
  })

  const currentUsagePercentage = computed(() => {
    if (!tokenLimits.value) return 0
    const { current_usage, limits } = tokenLimits.value
    return Math.round((current_usage.monthly / limits.monthly_limit) * 100)
  })

  const dailyUsagePercentage = computed(() => {
    if (!tokenLimits.value) return 0
    const { current_usage, limits } = tokenLimits.value
    return Math.round((current_usage.daily / limits.daily_limit) * 100)
  })

  const usageStatusColor = computed(() => {
    const percentage = currentUsagePercentage.value
    if (percentage >= 90) return 'text-red-600'
    if (percentage >= 70) return 'text-yellow-600'
    return 'text-green-600'
  })

  const usageStatusBgColor = computed(() => {
    const percentage = currentUsagePercentage.value
    if (percentage >= 90) return 'bg-red-100'
    if (percentage >= 70) return 'bg-yellow-100'
    return 'bg-green-100'
  })

  // Format numbers for display
  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toString()
  }

  // Clear data
  const clearTokenData = (): void => {
    tokenStats.value = null
    tokenLimits.value = null
    rateLimitStatus.value = null
    dashboardData.value = null
    error.value = null
  }

  return {
    // State
    tokenStats: readonly(tokenStats),
    tokenLimits: readonly(tokenLimits),
    rateLimitStatus: readonly(rateLimitStatus),
    dashboardData: readonly(dashboardData),
    loading: readonly(loading),
    error: readonly(error),

    // Actions
    getTokenUsage,
    getTokenLimits,
    checkRateLimit,
    getDashboardData,
    refreshTokenData,
    clearTokenData,

    // Computed
    hasTokenData,
    hasLimitsData,
    hasDashboardData,
    isRateLimited,
    currentUsagePercentage,
    dailyUsagePercentage,
    usageStatusColor,
    usageStatusBgColor,

    // Utilities
    formatNumber
  }
}
