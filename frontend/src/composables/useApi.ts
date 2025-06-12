import { ref } from 'vue';
import type { QueryRequest, QueryResponse, SchemaInfo } from '@/types/api';
import { useAuth } from './useAuth';

export function useApi() {
  const { api } = useAuth();
  const loading = ref(false);
  const error = ref<string | null>(null);

  const executeQuery = async (question: string): Promise<QueryResponse | null> => {
    loading.value = true;
    error.value = null;

    try {
      const request: QueryRequest = { question };
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

  const getSchema = async (): Promise<SchemaInfo | null> => {
    loading.value = true;
    error.value = null;

    try {
      const response = await api.get<SchemaInfo>('/api/v1/schema');
      return response.data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch schema';
      console.error('Schema Error:', err);
      return null;
    } finally {
      loading.value = false;
    }
  };

  const healthCheck = async (): Promise<boolean> => {
    try {
      await api.get('/api/v1/health');
      return true;
    } catch {
      return false;
    }
  };

  return {
    loading,
    error,
    executeQuery,
    getSchema,
    healthCheck,
  };
}
