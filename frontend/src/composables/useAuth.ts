import axios from 'axios';
import { ref, computed } from 'vue';
import type { User, UserCreate, UserLogin, Token, TokenUsageStats } from '@/types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Global auth state
const user = ref<User | null>(null);
const token = ref<string | null>(localStorage.getItem('auth_token'));
const loading = ref(false);
const error = ref<string | null>(null);

// Configure axios with auth header
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth header
api.interceptors.request.use((config) => {
  if (token.value) {
    config.headers.Authorization = `Bearer ${token.value}`;
  }
  return config;
});

// Add response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - call logout function
      const authLogout = () => {
        token.value = null;
        user.value = null;
        localStorage.removeItem('auth_token');
        error.value = null;
      };
      authLogout();
    }
    return Promise.reject(error);
  }
);

export function useAuth() {
  const isAuthenticated = computed(() => !!user.value && !!token.value);

  const register = async (userData: UserCreate): Promise<boolean> => {
    loading.value = true;
    error.value = null;

    try {
      const response = await api.post<Token>('/api/v1/auth/register', userData);
      const tokenData = response.data;
      
      // Store token and user data
      token.value = tokenData.access_token;
      user.value = tokenData.user;
      localStorage.setItem('auth_token', tokenData.access_token);
      
      return true;
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Registration failed';
      console.error('Registration error:', err);
      return false;
    } finally {
      loading.value = false;
    }
  };

  const login = async (credentials: UserLogin): Promise<boolean> => {
    loading.value = true;
    error.value = null;

    try {
      console.log('🔄 로그인 시도 중...');
      const response = await api.post<Token>('/api/v1/auth/login', credentials);
      const tokenData = response.data;
      
      console.log('✅ 로그인 성공:', {
        hasToken: !!tokenData.access_token,
        hasUser: !!tokenData.user,
        userEmail: tokenData.user?.email
      });
      
      // Store token and user data
      token.value = tokenData.access_token;
      user.value = tokenData.user;
      localStorage.setItem('auth_token', tokenData.access_token);
      
      console.log('💾 토큰과 사용자 정보 저장 완료');
      
      return true;
    } catch (err: any) {
      console.error('❌ 로그인 실패:', err);
      error.value = err.response?.data?.detail || 'Login failed';
      return false;
    } finally {
      loading.value = false;
    }
  };

  const logout = () => {
    console.log('🚪 로그아웃 처리 시작');
    
    // Clear all auth state
    token.value = null;
    user.value = null;
    error.value = null;
    
    // Clear localStorage
    localStorage.removeItem('auth_token');
    
    console.log('✅ 로그아웃 완료 - 모든 상태 초기화됨');
  };

  const fetchUserProfile = async (): Promise<boolean> => {
    if (!token.value) {
      console.log('❌ fetchUserProfile: 토큰이 없음');
      return false;
    }

    console.log('🔄 fetchUserProfile 시작', {
      tokenExists: !!token.value,
      tokenPrefix: token.value?.substring(0, 10) + '...'
    });

    loading.value = true;
    error.value = null;

    try {
      const response = await api.get<User>('/api/v1/auth/me');
      console.log('✅ fetchUserProfile 성공:', response.data);
      user.value = response.data;
      return true;
    } catch (err: any) {
      console.error('❌ fetchUserProfile 실패:', {
        status: err.response?.status,
        statusText: err.response?.statusText,
        data: err.response?.data,
        headers: err.response?.headers
      });
      error.value = err.response?.data?.detail || 'Failed to fetch profile';
      return false;
    } finally {
      loading.value = false;
    }
  };

  const fetchUserStats = async (): Promise<TokenUsageStats | null> => {
    if (!token.value) return null;

    loading.value = true;
    error.value = null;

    try {
      const response = await api.get<TokenUsageStats>('/api/v1/auth/stats');
      return response.data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch stats';
      console.error('Stats fetch error:', err);
      return null;
    } finally {
      loading.value = false;
    }
  };

  // Initialize auth state on page load
  const initializeAuth = async () => {
    console.log('🔄 initializeAuth 호출됨', {
      hasToken: !!token.value,
      tokenLength: token.value?.length,
      hasUser: !!user.value
    });
    
    if (token.value && !user.value) {
      console.log('👤 토큰은 있지만 사용자 정보 없음 - 프로필 로드 시도');
      const success = await fetchUserProfile();
      console.log('📊 프로필 로드 결과:', { success, user: user.value });
    }
  };

  return {
    // State
    user: computed(() => user.value),
    token: computed(() => token.value),
    loading: computed(() => loading.value),
    error: computed(() => error.value),
    isAuthenticated,
    
    // Methods
    register,
    login,
    logout,
    fetchUserProfile,
    fetchUserStats,
    initializeAuth,
    
    // API instance for other composables
    api,
  };
}
