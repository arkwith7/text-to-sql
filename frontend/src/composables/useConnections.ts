import { ref, computed } from 'vue';
import { useApi } from './useApi';
import { useAuth } from './useAuth';
import { logger } from '@/utils/logger';

export interface Connection {
  id: string;
  connection_name: string;
  db_type: string;
  db_host: string;
  db_port: number;
  db_user: string;
  db_name: string;
  status?: 'connected' | 'disconnected' | 'error' | 'testing';
  last_error?: string;
}

// ---- 모듈 스코프 전역 상태 (모든 컴포넌트에서 공유) ----
const connections = ref<Connection[]>([]);
const selectedConnectionId = ref<string | null>(null);

// localStorage에서 마지막 선택된 connection_id 복구
const STORAGE_KEY = 'text_to_sql_selected_connection_id';
if (typeof window !== 'undefined') {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) {
    selectedConnectionId.value = stored;
  }
}

/**
 * 전역적인 DB 연결 목록 및 선택된 connection_id 를 관리하는 컴포저블
 */
export function useConnections() {
  const { getConnections, createConnection, updateConnection, deleteConnection, testConnection: testConnectionAPI } = useApi();

  const selectedConnection = computed(() =>
    connections.value.find((c) => c.id === selectedConnectionId.value) || null,
  );

  // --- API wrapper helpers ---
  const fetchConnections = async () => {
    try {
      logger.debug('fetchConnections 시작');
      const resp = await getConnections();
      connections.value = resp.data as Connection[];
      logger.success('연결 목록 로드 성공:', { count: connections.value.length });
      
      // 선택된 connection이 목록에 없으면 해제
      if (selectedConnectionId.value) {
        const exists = connections.value.some((c) => c.id === selectedConnectionId.value);
        if (!exists) {
          selectedConnectionId.value = null;
          localStorage.removeItem(STORAGE_KEY);
        }
      }
      
      // 연결 목록이 있지만 선택된 것이 없으면 첫 번째 연결 자동 선택
      if (connections.value.length > 0 && !selectedConnectionId.value) {
        selectedConnectionId.value = connections.value[0].id;
        localStorage.setItem(STORAGE_KEY, selectedConnectionId.value);
      }
      
      // 선택된 연결이 있고 상태가 없으면 자동으로 테스트
      if (selectedConnectionId.value) {
        const selectedConn = connections.value.find(c => c.id === selectedConnectionId.value);
        if (selectedConn && !selectedConn.status) {
          try {
            await testConnection(selectedConnectionId.value);
          } catch (error) {
            logger.warn('선택된 연결 자동 테스트 실패:', error);
          }
        }
      }
    } catch (error: any) {
      logger.error('연결 목록 로드 실패:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data
      });
      
      // 401 에러의 경우 빈 배열로 설정하고 조용히 처리
      if (error.response?.status === 401) {
        logger.warn('연결 목록 접근 권한 없음 - 빈 목록으로 설정');
        connections.value = [];
        selectedConnectionId.value = null;
        localStorage.removeItem(STORAGE_KEY);
      } else {
        // 다른 에러는 다시 던지기
        throw error;
      }
    }
  };

  const addConnection = async (data: any) => {
    const resp = await createConnection(data);
    await fetchConnections();
    // 새로 만든 것을 자동 선택
    selectedConnectionId.value = resp.data.id;
    localStorage.setItem(STORAGE_KEY, resp.data.id);
    
    // 새로 추가된 연결을 즉시 테스트
    try {
      await testConnection(resp.data.id);
    } catch (error) {
      console.warn('새 연결 테스트 실패:', error);
    }
  };

  const modifyConnection = async (id: string, data: any) => {
    await updateConnection(id, data);
    await fetchConnections();
  };

  const removeConnection = async (id: string) => {
    await deleteConnection(id);
    await fetchConnections();
  };

  const selectConnection = (id: string | null) => {
    selectedConnectionId.value = id;
    // localStorage에 저장
    if (id) {
      localStorage.setItem(STORAGE_KEY, id);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  const testConnection = async (connectionId: string) => {
    try {
      // 연결 상태를 testing으로 업데이트
      const conn = connections.value.find(c => c.id === connectionId);
      if (conn) {
        conn.status = 'testing';
      }

      // 새로운 연결 테스트 API 사용
      const response = await testConnectionAPI(connectionId);
      const result = response.data;
      
      if (conn) {
        if (result.success) {
          conn.status = 'connected';
          conn.last_error = undefined;
        } else {
          conn.status = 'error';
          conn.last_error = result.error || '연결 실패';
        }
      }
      
      return result.success;
    } catch (error: any) {
      // API 호출 자체가 실패한 경우
      const conn = connections.value.find(c => c.id === connectionId);
      if (conn) {
        conn.status = 'error';
        conn.last_error = error.response?.data?.detail || error.message || '연결 테스트 실패';
      }
      return false;
    }
  };

  const testAllConnections = async () => {
    for (const conn of connections.value) {
      await testConnection(conn.id);
    }
  };

  return {
    connections,
    selectedConnectionId,
    selectedConnection,
    fetchConnections,
    addConnection,
    modifyConnection,
    removeConnection,
    selectConnection,
    testConnection,
    testAllConnections,
  };
} 