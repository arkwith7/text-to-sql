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
      const response = await api.post<any>('/api/v1/chat/sessions', request);
      // Transform the response to match expected structure
      return {
        session_id: response.data.id,
        title: response.data.title,
        created_at: response.data.created_at,
        updated_at: response.data.updated_at,
        is_active: true,
        message_count: response.data.message_count || 0
      };
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
      const response = await api.get<ChatSession[]>('/api/v1/chat/sessions', {
        params: { limit, offset }
      });
      // Transform the response to match expected structure
      return {
        sessions: response.data.map((session: any) => ({
          session_id: session.id,
          title: session.title,
          created_at: session.created_at,
          updated_at: session.updated_at,
          is_active: true,
          message_count: session.message_count
        })),
        total_count: response.data.length
      };
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
      const response = await api.get<any[]>(
        `/api/v1/chat/sessions/${sessionId}/messages`,
        { params: { limit, offset } }
      );
      // Transform the response to match expected structure
      return {
        session_id: sessionId,
        messages: response.data.map((msg: any) => ({
          message_id: msg.id,
          session_id: sessionId,
          user_message: msg.message_type === 'user' ? msg.content : '',
          ai_response: msg.message_type === 'assistant' ? msg.content : '',
          query_result: msg.query_results,
          timestamp: msg.created_at,
          sequence_number: 0 // Not available in current API
        })),
        total_count: response.data.length
      };
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
