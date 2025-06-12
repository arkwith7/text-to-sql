import { ref } from 'vue';
import type { 
  ChatSession, 
  ChatMessage, 
  CreateSessionRequest, 
  AddMessageRequest,
  SessionListResponse,
  SessionMessagesResponse 
} from '@/types/api';
import { useAuth } from './useAuth';

export function useChatApi() {
  const { api } = useAuth();
  const loading = ref(false);
  const error = ref<string | null>(null);

  // Create a new chat session
  const createSession = async (request: CreateSessionRequest): Promise<ChatSession | null> => {
    loading.value = true;
    error.value = null;

    try {
      const response = await api.post<ChatSession>('/api/v1/chat/sessions', request);
      return response.data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to create chat session';
      console.error('Create Session Error:', err);
      return null;
    } finally {
      loading.value = false;
    }
  };

  // Get user's chat sessions
  const getUserSessions = async (limit = 20, offset = 0): Promise<SessionListResponse | null> => {
    loading.value = true;
    error.value = null;

    try {
      const response = await api.get<SessionListResponse>('/api/v1/chat/sessions', {
        params: { limit, offset }
      });
      return response.data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch chat sessions';
      console.error('Get Sessions Error:', err);
      return null;
    } finally {
      loading.value = false;
    }
  };

  // Get messages for a specific session
  const getSessionMessages = async (
    sessionId: string, 
    limit = 50, 
    offset = 0
  ): Promise<SessionMessagesResponse | null> => {
    loading.value = true;
    error.value = null;

    try {
      const response = await api.get<SessionMessagesResponse>(
        `/api/v1/chat/sessions/${sessionId}/messages`,
        { params: { limit, offset } }
      );
      return response.data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch session messages';
      console.error('Get Messages Error:', err);
      return null;
    } finally {
      loading.value = false;
    }
  };

  // Add a message to a session
  const addMessage = async (
    sessionId: string, 
    request: AddMessageRequest
  ): Promise<ChatMessage | null> => {
    loading.value = true;
    error.value = null;

    try {
      const response = await api.post<ChatMessage>(
        `/api/v1/chat/sessions/${sessionId}/messages`,
        request
      );
      return response.data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to add message';
      console.error('Add Message Error:', err);
      return null;
    } finally {
      loading.value = false;
    }
  };

  // Deactivate a session
  const deactivateSession = async (sessionId: string): Promise<boolean> => {
    loading.value = true;
    error.value = null;

    try {
      await api.delete(`/api/v1/chat/sessions/${sessionId}`);
      return true;
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to deactivate session';
      console.error('Deactivate Session Error:', err);
      return false;
    } finally {
      loading.value = false;
    }
  };

  // Get session context for AI (internal use)
  const getSessionContext = async (sessionId: string): Promise<any | null> => {
    loading.value = true;
    error.value = null;

    try {
      const response = await api.get(`/api/v1/chat/sessions/${sessionId}/context`);
      return response.data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to get session context';
      console.error('Get Context Error:', err);
      return null;
    } finally {
      loading.value = false;
    }
  };

  return {
    loading,
    error,
    createSession,
    getUserSessions,
    getSessionMessages,
    addMessage,
    deactivateSession,
    getSessionContext,
  };
}
