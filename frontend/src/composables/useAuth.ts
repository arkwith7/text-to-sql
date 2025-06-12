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
      const response = await api.post<Token>('/api/v1/auth/login', credentials);
      const tokenData = response.data;
      
      // Store token and user data
      token.value = tokenData.access_token;
      user.value = tokenData.user;
      localStorage.setItem('auth_token', tokenData.access_token);
      
      return true;
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Login failed';
      console.error('Login error:', err);
      return false;
    } finally {
      loading.value = false;
    }
  };

  const logout = () => {
    token.value = null;
    user.value = null;
    localStorage.removeItem('auth_token');
    error.value = null;
  };

  const fetchUserProfile = async (): Promise<boolean> => {
    if (!token.value) return false;

    loading.value = true;
    error.value = null;

    try {
      const response = await api.get<User>('/api/v1/auth/me');
      user.value = response.data;
      return true;
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch profile';
      console.error('Profile fetch error:', err);
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
    if (token.value) {
      await fetchUserProfile();
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
