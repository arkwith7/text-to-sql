import axios from 'axios';
import { ref, computed, watch } from 'vue';
import { logger } from '@/utils/logger';
import type { User, UserCreate, UserLogin, Token, TokenUsageStats, ModelStatsResponse } from '@/types/api';

// Environment-aware API configuration
// 개발환경: Vite proxy를 통해 상대경로 사용 (프록시가 localhost:8000으로 전달)
// 배포환경: VITE_API_BASE_URL 환경변수 사용 (Docker Compose에서 8070 포트)
const API_BASE_URL = import.meta.env.DEV
  ? ''  // 개발환경: Vite proxy 사용
  : import.meta.env.VITE_API_BASE_URL || 'http://localhost:8070';  // 배포환경: 8070 포트

// Debug API configuration
logger.debug('API 설정 정보:', {
  isDev: import.meta.env.DEV,
  envVar: import.meta.env.VITE_API_BASE_URL,
  resolvedURL: API_BASE_URL,
  mode: import.meta.env.MODE
});

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
  const currentToken = token.value;
  
  logger.debug('Request interceptor 실행:', {
    url: config.url,
    method: config.method?.toUpperCase(),
    hasToken: !!currentToken,
    tokenPrefix: currentToken ? currentToken.substring(0, 20) + '...' : 'none'
  });
  
  if (currentToken) {
    config.headers.Authorization = `Bearer ${currentToken}`;
    logger.debug('Authorization 헤더 추가됨', {
      url: config.url,
      authHeaderSet: !!config.headers.Authorization
    });
  } else {
    logger.warn('토큰이 없어서 Authorization 헤더를 추가하지 못함', {
      url: config.url,
      tokenValue: currentToken
    });
  }
  
  return config;
});

// Add response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Only clear auth state for authentication-related endpoints
      const url = error.config?.url || '';
      const isAuthEndpoint = url.includes('/auth/') || url.includes('/api/v1/auth/me');
      
      logger.debug('401 Error 감지:', {
        url,
        isAuthEndpoint,
        shouldLogout: isAuthEndpoint
      });
      
      if (isAuthEndpoint) {
        // Token expired or invalid on auth endpoints - clear auth state
        logger.info('인증 엔드포인트에서 401 에러 - 로그아웃 처리');
        const authLogout = () => {
          token.value = null;
          user.value = null;
          localStorage.removeItem('auth_token');
          error.value = null;
        };
        authLogout();
      } else {
        // For non-auth endpoints, just log the error but don't clear auth state
        logger.warn('비인증 엔드포인트에서 401 에러 - 인증 상태 유지:', { url });
      }
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
      logger.auth('로그인 시도 중...', {
        url: `${API_BASE_URL}/api/v1/auth/login`,
        credentials: { email: credentials.email, password: '[HIDDEN]' }
      });
      
      const response = await api.post<Token>('/api/v1/auth/login', credentials);
      const tokenData = response.data;
      
      logger.success('로그인 성공:', {
        hasToken: !!tokenData.access_token,
        hasUser: !!tokenData.user,
        userEmail: tokenData.user?.email
      });
      
      // Store token and user data
      token.value = tokenData.access_token;
      user.value = tokenData.user;
      localStorage.setItem('auth_token', tokenData.access_token);
      
      logger.debug('토큰과 사용자 정보 저장 완료');
      
      return true;
    } catch (err: any) {
      logger.error('로그인 실패:', {
        error: err,
        response: err.response,
        message: err.message,
        status: err.response?.status,
        data: err.response?.data
      });
      error.value = err.response?.data?.detail || 'Login failed';
      return false;
    } finally {
      loading.value = false;
    }
  };

  const logout = () => {
    logger.auth('로그아웃 처리 시작');
    
    // Clear all auth state
    token.value = null;
    user.value = null;
    error.value = null;
    
    // Clear localStorage
    localStorage.removeItem('auth_token');
    
    logger.success('로그아웃 완료 - 모든 상태 초기화됨');
  };

  const fetchUserProfile = async (): Promise<boolean> => {
    if (!token.value) {
      logger.warn('fetchUserProfile: 토큰이 없음');
      return false;
    }

    logger.debug('fetchUserProfile 시작', {
      tokenExists: !!token.value,
      tokenPrefix: token.value?.substring(0, 10) + '...'
    });

    loading.value = true;
    error.value = null;

    try {
      const response = await api.get<User>('/api/v1/auth/me');
      logger.success('fetchUserProfile 성공:', response.data);
      user.value = response.data;
      return true;
    } catch (err: any) {
      logger.error('fetchUserProfile 실패:', {
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

  const fetchModelStats = async (): Promise<ModelStatsResponse | null> => {
    if (!token.value) return null;

    loading.value = true;
    error.value = null;

    try {
      const response = await api.get<ModelStatsResponse>('/api/v1/auth/model-stats');
      return response.data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch model stats';
      console.error('Model stats fetch error:', err);
      return null;
    } finally {
      loading.value = false;
    }
  };

  // Initialize auth state on page load
  // 백엔드 연결 상태 확인
  const checkBackendConnection = async (): Promise<boolean> => {
    try {
      // 간단한 헬스체크 엔드포인트 호출 (인증 불필요)
      await api.get('/health', { timeout: 3000 });
      return true;
    } catch (error: any) {
      logger.debug('백엔드 연결 실패:', {
        code: error.code,
        message: error.message
      });
      return false;
    }
  };

  const initializeAuth = async () => {
    const currentToken = token.value;
    const storedToken = localStorage.getItem('auth_token');
    
    logger.debug('initializeAuth 호출됨', {
      hasToken: !!currentToken,
      tokenLength: currentToken?.length,
      hasUser: !!user.value,
      storedTokenExists: !!storedToken,
      storedTokenLength: storedToken?.length,
      tokensMatch: currentToken === storedToken
    });
    
    // 토큰이 localStorage에 있지만 reactive 변수에 없다면 동기화
    if (storedToken && !currentToken) {
      logger.warn('localStorage에 토큰이 있지만 reactive 변수에 없음 - 동기화 중');
      token.value = storedToken;
    }
    
    // 토큰이 있는 경우에만 백엔드 연결 확인 후 프로필 로드
    if (token.value && !user.value) {
      logger.debug('토큰은 있지만 사용자 정보 없음 - 백엔드 연결 확인 중');
      
      const isBackendConnected = await checkBackendConnection();
      if (!isBackendConnected) {
        logger.warn('백엔드가 연결되지 않음 - 인증 초기화 건너뜀');
        return;
      }
      
      logger.debug('백엔드 연결됨 - 프로필 로드 시도');
      const success = await fetchUserProfile();
      logger.debug('프로필 로드 결과:', { success, user: user.value });
    }
  };

  // Debug: 사용자 상태 변화 모니터링 (한 번만 등록)
  if (!user.value) {  // 초기화 시에만 등록
    watch(user, (newUser, oldUser) => {
      logger.debug('사용자 상태 변화:', {
        from: oldUser ? `${oldUser.email} (${oldUser.id})` : 'null',
        to: newUser ? `${newUser.email} (${newUser.id})` : 'null',
        timestamp: new Date().toISOString()
      });
    });
  }

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
    fetchModelStats,
    initializeAuth,
    
    // API instance for other composables
    api,
  };
}
