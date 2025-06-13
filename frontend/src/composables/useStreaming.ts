import { ref, computed } from 'vue';
import { useAuth } from './useAuth';

export interface StreamEvent {
  event: string;
  data: Record<string, any>;
  timestamp: string;
}

export interface StreamingState {
  isStreaming: boolean;
  currentEvent: string | null;
  events: StreamEvent[];
  error: string | null;
}

export function useStreaming() {
  const { api, token } = useAuth();
  
  const state = ref<StreamingState>({
    isStreaming: false,
    currentEvent: null,
    events: [],
    error: null
  });

  const currentMessage = computed(() => {
    if (state.value.events.length === 0) return null;
    const lastEvent = state.value.events[state.value.events.length - 1];
    return lastEvent.data.message || null;
  });

  const progress = computed(() => {
    const events = state.value.events;
    if (events.length === 0) return 0;
    
    // Define progress stages
    const stages = [
      'query_started',
      'session_creating',
      'session_created',
      'analyzing',
      'generating_sql',
      'sql_generated',
      'executing_query',
      'processing_results',
      'generating_insights',
      'query_completed'
    ];
    
    const lastEvent = events[events.length - 1];
    const stageIndex = stages.indexOf(lastEvent.event);
    
    if (stageIndex === -1) return 0;
    return Math.round((stageIndex + 1) / stages.length * 100);
  });

  const streamQuery = async (
    question: string,
    sessionId?: string,
    onProgress?: (event: StreamEvent) => void,
    onComplete?: (result: any) => void,
    onError?: (error: string) => void
  ): Promise<void> => {
    // Reset state
    state.value = {
      isStreaming: true,
      currentEvent: null,
      events: [],
      error: null
    };

    try {
      // Simulate streaming events for better UX
      const simulateEvent = (event: string, data: any) => {
        const streamEvent: StreamEvent = {
          event,
          data,
          timestamp: new Date().toISOString()
        };
        state.value.events.push(streamEvent);
        state.value.currentEvent = event;
        if (onProgress) {
          onProgress(streamEvent);
        }
      };

      // Start simulation
      simulateEvent('query_started', { message: '질문을 분석하고 있습니다...' });
      
      if (!sessionId) {
        simulateEvent('session_creating', { message: '새로운 채팅 세션을 생성하고 있습니다...' });
        // Create new session if needed
        // This should be handled by the calling component
      }

      simulateEvent('analyzing', { message: 'SQL 쿼리를 생성하고 있습니다...' });
      
      // Use the existing query endpoint
      const response = await api.post(`/api/v1/chat/sessions/${sessionId}/query`, {
        question,
        include_explanation: true,
        max_rows: 100
      });

      simulateEvent('executing_query', { message: '쿼리를 실행하고 있습니다...' });
      simulateEvent('processing_results', { message: '결과를 처리하고 있습니다...' });

      // Complete
      state.value.isStreaming = false;
      simulateEvent('query_completed', { 
        message: '완료되었습니다!',
        result: response.data
      });

      if (onComplete) {
        onComplete(response.data);
      }

    } catch (error) {
      state.value.isStreaming = false;
      state.value.error = error instanceof Error ? error.message : 'Unknown error';
      
      const errorEvent: StreamEvent = {
        event: 'error',
        data: { error: state.value.error },
        timestamp: new Date().toISOString()
      };
      state.value.events.push(errorEvent);
      
      if (onError) {
        onError(state.value.error);
      }
    }
  };

  const connectToSession = (
    sessionId: string,
    onEvent?: (event: StreamEvent) => void,
    onError?: (error: string) => void
  ): () => void => {
    let eventSource: EventSource | null = null;

    try {
      const url = `/api/v1/chat/stream-session/${sessionId}`;
      eventSource = new EventSource(url, {
        withCredentials: true
      });

      // Add auth header (EventSource doesn't support custom headers, so we'll use query param)
      const authUrl = `${url}?token=${encodeURIComponent(token.value || '')}`;
      eventSource = new EventSource(authUrl);

      eventSource.onmessage = (event) => {
        try {
          const eventData = JSON.parse(event.data) as StreamEvent;
          
          if (onEvent) {
            onEvent(eventData);
          }
        } catch (parseError) {
          console.error('Failed to parse session event:', parseError);
        }
      };

      eventSource.onerror = (error) => {
        console.error('EventSource error:', error);
        if (onError) {
          onError('Connection to session lost');
        }
      };

      // Return cleanup function
      return () => {
        if (eventSource) {
          eventSource.close();
        }
      };
    } catch (error) {
      if (onError) {
        onError(error instanceof Error ? error.message : 'Failed to connect to session');
      }
      
      // Return no-op cleanup function
      return () => {};
    }
  };

  const clearEvents = (): void => {
    state.value.events = [];
    state.value.currentEvent = null;
    state.value.error = null;
  };

  const stopStreaming = (): void => {
    state.value.isStreaming = false;
  };

  return {
    // State
    state: computed(() => state.value),
    isStreaming: computed(() => state.value.isStreaming),
    currentEvent: computed(() => state.value.currentEvent),
    events: computed(() => state.value.events),
    error: computed(() => state.value.error),
    currentMessage,
    progress,
    
    // Actions
    streamQuery,
    connectToSession,
    clearEvents,
    stopStreaming
  };
}
