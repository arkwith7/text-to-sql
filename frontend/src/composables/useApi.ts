import { ref } from 'vue';
import type { QueryRequest, QueryResponse, SchemaInfo, User } from '@/types/api';
import { useAuth } from './useAuth';

export function useApi() {
  const { api } = useAuth();
  const loading = ref(false);
  const error = ref<string | null>(null);

  const executeQuery = async (question: string, connectionId: string): Promise<QueryResponse | null> => {
    loading.value = true;
    error.value = null;
    try {
      const request: QueryRequest = { question, context: connectionId };
      const response = await api.post<QueryResponse>('/api/v1/query', request);
      return response.data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'An error occurred';
      console.error('API Error:', err);
      return null;
    } finally {
      loading.value = false;
    }
  };

  const getSchema = async (connectionId: string): Promise<SchemaInfo | null> => {
    loading.value = true;
    error.value = null;
    try {
      // Pass connection_id as a query parameter
      const response = await api.get<SchemaInfo>(`/api/v1/schema?connection_id=${connectionId}`);
      return response.data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch schema';
      console.error('Schema Error:', err);
      return null;
    } finally {
      loading.value = false;
    }
  };

  const healthCheck = () => api.get('/health');

  // Database Connection Management
  const getConnections = () => api.get<any[]>('/api/v1/connections/');
  const createConnection = (data: any) => api.post<any>('/api/v1/connections/', data);
  const updateConnection = (id: string, data: any) => api.put<any>(`/api/v1/connections/${id}`, data);
  const deleteConnection = (id: string) => api.delete<void>(`/api/v1/connections/${id}`);
  const testConnection = (id: string) => api.post<any>(`/api/v1/connections/${id}/test`);

  // Admin User Management
  const getAllUsers = async (
    page: number = 1, 
    pageSize: number = 10, 
    search?: string, 
    role?: string, 
    status?: string
  ) => {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString()
      });
      if (search) {
        params.append('search', search);
      }
      if (role) {
        params.append('role', role);
      }
      if (status) {
        params.append('status', status);
      }
      const response = await api.get(`/api/v1/admin/users?${params}`);
      return response.data;
    } catch (err: any) {
      console.error('Failed to fetch users:', err);
      throw err;
    }
  };

  const getUserDetail = async (userId: string) => {
    try {
      const response = await api.get(`/api/v1/admin/users/${userId}`);
      return response.data;
    } catch (err: any) {
      console.error('Failed to fetch user detail:', err);
      throw err;
    }
  };

  const createUser = async (userData: any) => {
    try {
      const response = await api.post('/api/v1/admin/users', userData);
      return response.data;
    } catch (err: any) {
      console.error('Failed to create user:', err);
      throw err;
    }
  };

  const updateUser = async (userId: string, userData: any) => {
    try {
      const response = await api.put(`/api/v1/admin/users/${userId}`, userData);
      return response.data;
    } catch (err: any) {
      console.error('Failed to update user:', err);
      throw err;
    }
  };

  const deleteUser = async (userId: string) => {
    try {
      const response = await api.delete(`/api/v1/admin/users/${userId}`);
      return response.data;
    } catch (err: any) {
      console.error('Failed to delete user:', err);
      throw err;
    }
  };

  const updateUserRole = async (userId: string, newRole: string): Promise<void> => {
    try {
      await api.put<void>(`/api/v1/admin/users/${userId}/role`, { new_role: newRole });
    } catch (err: any) {
      console.error('Failed to update user role:', err);
      throw err;
    }
  };

  const updateUserStatus = async (userId: string, isActive: boolean): Promise<void> => {
    try {
      await api.put<void>(`/api/v1/admin/users/${userId}/status`, { is_active: isActive });
    } catch (err: any) {
      console.error('Failed to update user status:', err);
      throw err;
    }
  };

  return {
    loading,
    error,
    executeQuery,
    getSchema,
    healthCheck,

    // Connections
    getConnections,
    createConnection,
    updateConnection,
    deleteConnection,
    testConnection,

    // Admin User Management
    getAllUsers,
    getUserDetail,
    createUser,
    updateUser,
    deleteUser,
    updateUserRole,
    updateUserStatus
  };
}
