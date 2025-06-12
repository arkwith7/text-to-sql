import { ref, computed } from 'vue';
import type { ChatSession, ChatMessage } from '@/types/api';
import { useChatApi } from './useChatApi';

export function useChatSession() {
  const chatApi = useChatApi();
  
  // State
  const currentSession = ref<ChatSession | null>(null);
  const sessions = ref<ChatSession[]>([]);
  const messages = ref<ChatMessage[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // Computed
  const hasActiveSession = computed(() => !!currentSession.value);
  const sessionCount = computed(() => sessions.value.length);
  const messageCount = computed(() => messages.value.length);

  // Actions
  const createNewSession = async (title?: string, context?: string): Promise<boolean> => {
    loading.value = true;
    error.value = null;

    try {
      const session = await chatApi.createSession({ title, context });
      if (session) {
        currentSession.value = session;
        sessions.value.unshift(session); // Add to beginning of list
        messages.value = []; // Clear messages for new session
        return true;
      }
      return false;
    } catch (err: any) {
      error.value = err.message || 'Failed to create session';
      return false;
    } finally {
      loading.value = false;
    }
  };

  const loadUserSessions = async (): Promise<void> => {
    loading.value = true;
    error.value = null;

    try {
      const result = await chatApi.getUserSessions();
      if (result) {
        sessions.value = result.sessions;
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to load sessions';
    } finally {
      loading.value = false;
    }
  };

  const switchToSession = async (sessionId: string): Promise<boolean> => {
    const session = sessions.value.find(s => s.session_id === sessionId);
    if (!session) return false;

    loading.value = true;
    error.value = null;

    try {
      const result = await chatApi.getSessionMessages(sessionId);
      if (result) {
        currentSession.value = session;
        messages.value = result.messages;
        return true;
      }
      return false;
    } catch (err: any) {
      error.value = err.message || 'Failed to load session messages';
      return false;
    } finally {
      loading.value = false;
    }
  };

  const addMessageToSession = async (
    userMessage: string,
    aiResponse: string,
    queryResult?: Record<string, any>
  ): Promise<boolean> => {
    if (!currentSession.value) return false;

    loading.value = true;
    error.value = null;

    try {
      const message = await chatApi.addMessage(
        currentSession.value.session_id,
        { user_message: userMessage, ai_response: aiResponse, query_result: queryResult }
      );

      if (message) {
        messages.value.push(message);
        // Update session message count
        currentSession.value.message_count += 1;
        return true;
      }
      return false;
    } catch (err: any) {
      error.value = err.message || 'Failed to add message';
      return false;
    } finally {
      loading.value = false;
    }
  };

  const deleteSession = async (sessionId: string): Promise<boolean> => {
    loading.value = true;
    error.value = null;

    try {
      const success = await chatApi.deactivateSession(sessionId);
      if (success) {
        // Remove from local state
        sessions.value = sessions.value.filter(s => s.session_id !== sessionId);
        
        // If this was the current session, clear it
        if (currentSession.value?.session_id === sessionId) {
          currentSession.value = null;
          messages.value = [];
        }
        return true;
      }
      return false;
    } catch (err: any) {
      error.value = err.message || 'Failed to delete session';
      return false;
    } finally {
      loading.value = false;
    }
  };

  const clearCurrentSession = (): void => {
    currentSession.value = null;
    messages.value = [];
  };

  const refreshCurrentSession = async (): Promise<void> => {
    if (!currentSession.value) return;
    await switchToSession(currentSession.value.session_id);
  };

  return {
    // State
    currentSession,
    sessions,
    messages,
    loading,
    error,
    
    // Computed
    hasActiveSession,
    sessionCount,
    messageCount,
    
    // Actions
    createNewSession,
    loadUserSessions,
    switchToSession,
    addMessageToSession,
    deleteSession,
    clearCurrentSession,
    refreshCurrentSession,
  };
}
