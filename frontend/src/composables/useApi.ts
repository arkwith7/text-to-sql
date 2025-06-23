import { ref } from 'vue';
import type { QueryRequest, QueryResponse, SchemaInfo } from '@/types/api';
import { useAuth } from './useAuth';

export function useApi() {
  const { api } = useAuth();
  const loading = ref(false);
  const error = ref<string | null>(null);

  const executeQuery = async (question: string, connectionId: string): Promise<QueryResponse | null> => {
    loading.value = true;
    error.value = null;
    try {
      const request: QueryRequest = { question, connection_id: connectionId };
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
  const getConnections = () => api.get<any[]>('/api/v1/connections');
  const createConnection = (data: any) => api.post<any>('/api/v1/connections', data);
  const updateConnection = (id: string, data: any) => api.put<any>(`/api/v1/connections/${id}`, data);
  const deleteConnection = (id: string) => api.delete<void>(`/api/v1/connections/${id}`);
  const testConnection = (id: string) => api.post<any>(`/api/v1/connections/${id}/test`);

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
    testConnection
  };
}
