<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <!-- Debug Information (임시) - 토큰이 있지만 사용자 정보가 없을 때만 표시 -->
    <div v-if="!user && token && !loading" class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
      <p class="text-yellow-800">
        🔍 디버그: 사용자 정보가 로드되지 않았습니다. 
        토큰 상태: {{ !!token }}, 로딩 상태: {{ loading }}, 오류: {{ error }}
      </p>
      <button 
        @click="retryLoadUser"
        class="mt-2 px-3 py-1 bg-yellow-600 text-white rounded text-sm hover:bg-yellow-700"
      >
        사용자 정보 다시 로드
      </button>
    </div>

    <!-- Profile Header -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-4">
          <div class="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white text-xl font-bold">
            {{ user?.full_name?.charAt(0).toUpperCase() || '?' }}
          </div>
          <div>
            <h2 class="text-2xl font-bold text-gray-900">{{ user?.full_name || '사용자 이름 없음' }}</h2>
            <p class="text-gray-600">{{ user?.email || '이메일 없음' }}</p>
          </div>
        </div>
        <button
          @click="logout"
          class="flex items-center px-4 py-2 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded-lg transition-colors"
        >
          <LogOut class="w-4 h-4 mr-2" />
          로그아웃
        </button>
      </div>

      <!-- User Details Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              이름
            </label>
            <p class="text-gray-900 font-medium">{{ user?.full_name || '정보 없음' }}</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              이메일
            </label>
            <p class="text-gray-900 font-medium">{{ user?.email || '정보 없음' }}</p>
          </div>
        </div>

        <div class="space-y-4">
          <div v-if="user?.company">
            <label class="block text-sm font-medium text-gray-700 mb-1">
              회사
            </label>
            <p class="text-gray-900 font-medium">{{ user.company }}</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              가입일
            </label>
            <p class="text-gray-900 font-medium">{{ user?.created_at ? formatDate(user.created_at) : '정보 없음' }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Usage Statistics -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-lg font-semibold text-gray-900">사용량 통계</h3>
        <button
          @click="loadStats"
          :disabled="loading"
          class="flex items-center px-3 py-2 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50"
        >
          <RotateCcw class="w-4 h-4 mr-1" :class="loading ? 'animate-spin' : ''" />
          새로고침
        </button>
      </div>
      
      <div v-if="stats" class="space-y-6">
        <!-- Stats Grid -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
            <div class="flex items-center">
              <div class="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center text-white mr-3">
                <Search class="w-5 h-5" />
              </div>
              <div>
                <p class="text-sm font-medium text-blue-900">총 쿼리 수</p>
                <p class="text-2xl font-bold text-blue-700">{{ stats.total_queries?.toLocaleString() || 0 }}</p>
              </div>
            </div>
          </div>
          
          <div class="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
            <div class="flex items-center">
              <div class="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center text-white mr-3">
                <Zap class="w-5 h-5" />
              </div>
              <div>
                <p class="text-sm font-medium text-green-900">토큰 사용량</p>
                <p class="text-2xl font-bold text-green-700">{{ stats.total_tokens?.toLocaleString() || 0 }}</p>
              </div>
            </div>
          </div>
          
          <div class="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
            <div class="flex items-center">
              <div class="w-10 h-10 bg-purple-500 rounded-lg flex items-center justify-center text-white mr-3">
                <Clock class="w-5 h-5" />
              </div>
              <div>
                <p class="text-sm font-medium text-purple-900">마지막 쿼리</p>
                <p class="text-sm font-bold text-purple-700">
                  {{ stats.last_query_at ? formatDate(stats.last_query_at) : '없음' }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Token Usage Chart -->
        <div class="bg-gray-50 rounded-lg p-6">
          <h4 class="text-md font-semibold text-gray-900 mb-4">토큰 사용량 상세</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Input Tokens -->
            <div class="bg-white rounded-lg p-4 border border-gray-200">
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-gray-700">입력 토큰</span>
                <span class="text-xs text-gray-500">{{ ((stats.input_tokens || 0) / (stats.total_tokens || 1) * 100).toFixed(1) }}%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-2 mb-2">
                <div 
                  class="bg-blue-500 h-2 rounded-full" 
                  :style="`width: ${(stats.input_tokens || 0) / (stats.total_tokens || 1) * 100}%`"
                ></div>
              </div>
              <p class="text-lg font-semibold text-gray-900">{{ (stats.input_tokens || 0).toLocaleString() }}</p>
            </div>

            <!-- Output Tokens -->
            <div class="bg-white rounded-lg p-4 border border-gray-200">
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-gray-700">출력 토큰</span>
                <span class="text-xs text-gray-500">{{ ((stats.output_tokens || 0) / (stats.total_tokens || 1) * 100).toFixed(1) }}%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-2 mb-2">
                <div 
                  class="bg-green-500 h-2 rounded-full" 
                  :style="`width: ${(stats.output_tokens || 0) / (stats.total_tokens || 1) * 100}%`"
                ></div>
              </div>
              <p class="text-lg font-semibold text-gray-900">{{ (stats.output_tokens || 0).toLocaleString() }}</p>
            </div>
          </div>
        </div>

        <!-- Recent Activity -->
        <div class="bg-gray-50 rounded-lg p-6">
          <h4 class="text-md font-semibold text-gray-900 mb-4">최근 활동</h4>
          <div class="space-y-3">
            <div class="flex items-center justify-between py-2 px-3 bg-white rounded-lg border border-gray-200">
              <div class="flex items-center">
                <div class="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                <span class="text-sm text-gray-700">마지막 로그인</span>
              </div>
              <span class="text-sm font-medium text-gray-900">{{ formatDate(new Date().toISOString()) }}</span>
            </div>
            
            <div class="flex items-center justify-between py-2 px-3 bg-white rounded-lg border border-gray-200">
              <div class="flex items-center">
                <div class="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
                <span class="text-sm text-gray-700">마지막 쿼리 실행</span>
              </div>
              <span class="text-sm font-medium text-gray-900">
                {{ stats.last_query_at ? formatDate(stats.last_query_at) : '없음' }}
              </span>
            </div>
            
            <div class="flex items-center justify-between py-2 px-3 bg-white rounded-lg border border-gray-200">
              <div class="flex items-center">
                <div class="w-2 h-2 bg-purple-500 rounded-full mr-3"></div>
                <span class="text-sm text-gray-700">계정 생성</span>
              </div>
              <span class="text-sm font-medium text-gray-900">
                {{ user?.created_at ? formatDate(user.created_at) : '정보 없음' }}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      <div v-else-if="loading" class="flex flex-col items-center justify-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
        <p class="text-gray-600">사용량 통계를 불러오는 중...</p>
      </div>
      
      <div v-else class="text-center py-12">
        <div class="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
          <AlertCircle class="w-6 h-6 text-gray-400" />
        </div>
        <p class="text-gray-600 mb-4">사용량 통계를 불러올 수 없습니다</p>
        <button
          @click="loadStats"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          다시 시도
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { 
  LogOut, 
  Search, 
  Zap, 
  Clock, 
  RotateCcw, 
  AlertCircle 
} from 'lucide-vue-next';
import { useAuth } from '@/composables/useAuth';
import type { TokenUsageStats } from '@/types/api';

const router = useRouter();
const { user, token, error, logout: authLogout, fetchUserProfile, fetchUserStats, loading, initializeAuth } = useAuth();

const stats = ref<TokenUsageStats | null>(null);

// 디버깅용 computed 속성들
const debugInfo = computed(() => ({
  hasUser: !!user.value,
  hasToken: !!token.value,
  isLoading: loading.value,
  errorMessage: error.value,
  userEmail: user.value?.email,
  userName: user.value?.full_name
}));

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const loadStats = async () => {
  const userStats = await fetchUserStats();
  if (userStats) {
    stats.value = userStats;
  }
};

// 사용자 정보 재로드 함수 (디버깅용)
const retryLoadUser = async () => {
  console.log('🔄 사용자 정보 재로드 시도...', {
    hasToken: !!token.value,
    tokenLength: token.value?.length
  });
  
  const success = await fetchUserProfile();
  console.log('📊 사용자 정보 로드 결과:', {
    success,
    user: user.value,
    error: error.value
  });
};

// 로그아웃 처리 함수
const logout = async () => {
  console.log('🚪 로그아웃 버튼 클릭됨');
  
  try {
    // 인증 상태 초기화
    authLogout();
    
    // 로그인 페이지로 리다이렉션
    console.log('📍 로그인 페이지로 리다이렉션');
    await router.push('/login');
  } catch (error) {
    console.error('❌ 로그아웃 처리 중 오류:', error);
  }
};

onMounted(async () => {
  console.log('📱 UserProfile 컴포넌트 마운트됨', debugInfo.value);
  
  // 토큰이 없으면 바로 로그인 페이지로 리다이렉션
  if (!token.value) {
    console.log('🔒 토큰이 없어서 로그인 페이지로 리다이렉션');
    await router.push('/login');
    return;
  }
  
  // 인증 상태 초기화
  await initializeAuth();
  
  // 사용자 정보가 여전히 없으면 다시 로드 시도
  if (!user.value && token.value) {
    console.log('👤 사용자 정보가 없어서 다시 로드 시도');
    await retryLoadUser();
  }
  
  // 여전히 사용자 정보가 없으면 로그인 페이지로 이동
  if (!user.value) {
    console.log('🔒 사용자 정보 로드 실패 - 로그인 페이지로 리다이렉션');
    await router.push('/login');
    return;
  }
  
  // 사용량 통계 로드
  await loadStats();
});
</script>
