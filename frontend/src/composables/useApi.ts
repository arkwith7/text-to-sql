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

  // Chat-integrated query execution
  const executeQueryWithChat = async (
    question: string, 
    sessionId?: string
  ): Promise<{ queryResponse: QueryResponse | null; sessionId: string | null }> => {
    // First execute the regular query
    const queryResponse = await executeQuery(question);
    
    if (!queryResponse) {
      return { queryResponse: null, sessionId: null };
    }

    // If we have a successful query response, we can integrate with chat
    // This would be used by chat components to save the query result
    return { 
      queryResponse, 
      sessionId: sessionId || null 
    };
  };

  return {
    loading,
    error,
    executeQuery,
    executeQueryWithChat,
    getSchema,
    healthCheck,
  };
}
