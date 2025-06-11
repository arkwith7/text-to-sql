import axios from 'axios';
import { ref, reactive } from 'vue';
import type { QueryRequest, QueryResponse, SchemaInfo } from '@/types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export function useApi() {
  const loading = ref(false);
  const error = ref<string | null>(null);

  const executeQuery = async (question: string): Promise<QueryResponse | null> => {
    loading.value = true;
    error.value = null;

    try {
      const request: QueryRequest = { question };
      const response = await api.post<QueryResponse>('/query', request);
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
      const response = await api.get<SchemaInfo>('/schema');
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
      await api.get('/health');
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
