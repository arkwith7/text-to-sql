<template>
  <div class="flex h-screen bg-gray-50">
    <!-- Sidebar -->
    <div 
      class="bg-white border-r border-gray-200 flex flex-col transition-all duration-300 ease-in-out relative"
      :class="isCollapsed ? 'w-16' : 'w-64'"
    >
      <!-- Sidebar Header -->
      <div class="p-4 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <router-link 
            v-if="!isCollapsed"
            to="/" 
            class="flex items-center hover:opacity-80 transition-opacity cursor-pointer group"
            title="랜딩 페이지로 이동"
          >
            <BarChart3 class="w-8 h-8 text-blue-600 mr-3 group-hover:text-blue-700 transition-colors" />
            <div>
              <h1 class="text-lg font-bold text-gray-900 group-hover:text-blue-700 transition-colors">SQL Assistant</h1>
              <p class="text-xs text-gray-600 group-hover:text-blue-600 transition-colors">AI-powered analytics</p>
            </div>
          </router-link>
          
          <!-- Collapsed Logo -->
          <router-link 
            v-else
            to="/" 
            class="flex items-center justify-center hover:opacity-80 transition-opacity cursor-pointer group w-full"
            title="랜딩 페이지로 이동"
          >
            <BarChart3 class="w-8 h-8 text-blue-600 group-hover:text-blue-700 transition-colors" />
          </router-link>
          
          <!-- Toggle Button -->
          <button
            @click="isCollapsed = !isCollapsed"
            class="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            :class="isCollapsed ? 'absolute top-4 right-2' : ''"
            title="사이드바 토글"
          >
            <Menu class="w-5 h-5 text-gray-600" />
          </button>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 p-4">
        <div class="space-y-2">
          <button
            @click="activeTab = 'chat'"
            :class="[
              'w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
              activeTab === 'chat' 
                ? 'bg-blue-100 text-blue-700' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100',
              isCollapsed ? 'justify-center' : ''
            ]"
            :title="isCollapsed ? '채팅' : ''"
          >
            <MessageCircle class="w-4 h-4" :class="isCollapsed ? '' : 'mr-3'" />
            <span v-if="!isCollapsed">채팅</span>
          </button>
          
          <button
            @click="activeTab = 'history'"
            :class="[
              'w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
              activeTab === 'history' 
                ? 'bg-blue-100 text-blue-700' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100',
              isCollapsed ? 'justify-center' : ''
            ]"
            :title="isCollapsed ? '대화 기록' : ''"
          >
            <Clock class="w-4 h-4" :class="isCollapsed ? '' : 'mr-3'" />
            <span v-if="!isCollapsed">대화 기록</span>
          </button>
          
          <button
            @click="activeTab = 'saved'"
            :class="[
              'w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
              activeTab === 'saved' 
                ? 'bg-blue-100 text-blue-700' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100',
              isCollapsed ? 'justify-center' : ''
            ]"
            :title="isCollapsed ? '저장된 쿼리' : ''"
          >
            <Bookmark class="w-4 h-4" :class="isCollapsed ? '' : 'mr-3'" />
            <span v-if="!isCollapsed">저장된 쿼리</span>
          </button>

          <button
            @click="activeTab = 'database'"
            :class="[
              'w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
              activeTab === 'database' 
                ? 'bg-blue-100 text-blue-700' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100',
              isCollapsed ? 'justify-center' : ''
            ]"
            :title="isCollapsed ? '분석 데이터 정보' : ''"
          >
            <Database class="w-4 h-4" :class="isCollapsed ? '' : 'mr-3'" />
            <span v-if="!isCollapsed">분석 데이터 정보</span>
          </button>

          <button
            @click="activeTab = 'profile'"
            :class="[
              'w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
              activeTab === 'profile' 
                ? 'bg-blue-100 text-blue-700' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100',
              isCollapsed ? 'justify-center' : ''
            ]"
            :title="isCollapsed ? '프로필' : ''"
          >
            <User class="w-4 h-4" :class="isCollapsed ? '' : 'mr-3'" />
            <span v-if="!isCollapsed">프로필</span>
          </button>
        </div>
      </nav>

      <!-- User Info -->
      <div class="p-4 border-t border-gray-200">
        <div v-if="user" class="flex items-center" :class="isCollapsed ? 'justify-center' : ''">
          <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
            {{ user.full_name?.charAt(0).toUpperCase() }}
          </div>
          <div v-if="!isCollapsed" class="ml-3 flex-1">
            <p class="text-sm font-medium text-gray-900">{{ user.full_name }}</p>
            <p class="text-xs text-gray-500">{{ user.email }}</p>
          </div>
          <button
            v-if="!isCollapsed"
            @click="logout"
            class="text-gray-400 hover:text-gray-600"
            title="로그아웃"
          >
            <LogOut class="w-4 h-4" />
          </button>
          
          <!-- Collapsed logout button -->
          <button
            v-if="isCollapsed"
            @click="logout"
            class="absolute bottom-2 right-2 text-gray-400 hover:text-gray-600 p-2 rounded-lg hover:bg-gray-100"
            title="로그아웃"
          >
            <LogOut class="w-4 h-4" />
          </button>
        </div>
        
        <!-- Fallback UI when user info is not loaded -->
        <div v-else-if="token" class="flex items-center" :class="isCollapsed ? 'justify-center' : ''">
          <div class="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center animate-pulse">
            <User class="w-4 h-4 text-gray-600" />
          </div>
          <div v-if="!isCollapsed" class="ml-3 flex-1">
            <p class="text-sm font-medium text-gray-500">사용자 정보 로딩 중...</p>
          </div>
          <button
            v-if="!isCollapsed"
            @click="logout"
            class="text-gray-400 hover:text-gray-600"
            title="로그아웃"
          >
            <LogOut class="w-4 h-4" />
          </button>
        </div>
        
        <!-- No token state -->
        <div v-else class="flex items-center justify-center p-2">
          <button
            @click="router.push('/login')"
            class="text-sm text-blue-600 hover:text-blue-800"
          >
            로그인 필요
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col h-screen">
      <!-- Header -->
      <header class="bg-white border-b border-gray-200 px-6 py-4 flex-shrink-0">
        <div class="flex items-center justify-between">
          <h2 class="text-xl font-semibold text-gray-900">
            {{ activeTab === 'chat' ? '새로운 질문' : 
               activeTab === 'history' ? '대화 기록' : 
               activeTab === 'saved' ? '저장된 쿼리' : 
               activeTab === 'database' ? '분석 데이터 정보' :
               activeTab === 'profile' ? '사용자 프로필' : '새로운 질문' }}
          </h2>
          
          <div class="flex items-center space-x-4">
            <!-- New Chat Button -->
            <button
              v-if="activeTab === 'chat'"
              @click="startNewChat"
              class="p-2 bg-green-100 text-green-700 rounded-full hover:bg-green-200 transition-colors"
              title="새 대화 시작"
            >
              <!-- 말풍선 + 플러스 아이콘 (New Chat) -->
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v8m-4-4h8" />
              </svg>
            </button>
            <!-- Connection Status & Settings -->
            <div class="flex items-center space-x-2">
              <div
                class="flex items-center px-3 py-1 rounded-full text-sm"
                :class="{
                  'bg-green-100 text-green-800': selectedConnection?.status === 'connected',
                  'bg-red-100 text-red-800': selectedConnection?.status === 'error' || !isConnected,
                  'bg-yellow-100 text-yellow-800': selectedConnection?.status === 'testing',
                  'bg-gray-100 text-gray-800': !selectedConnection?.status
                }"
                :title="getConnectionStatusText()"
              >
                <div
                  class="w-2 h-2 rounded-full mr-2"
                  :class="{
                    'bg-green-500': selectedConnection?.status === 'connected',
                    'bg-red-500': selectedConnection?.status === 'error' || !isConnected,
                    'bg-yellow-500': selectedConnection?.status === 'testing',
                    'bg-gray-400': !selectedConnection?.status
                  }"
                ></div>
                <span v-if="isConnected && selectedConnection">{{ selectedConnection.connection_name }}</span>
                <span v-else>UnConnected</span>
              </div>
              <!-- Settings Icon -->
              <button
                @click="isConnPanelOpen = true"
                class="p-2 rounded hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors"
                title="DB 연결 설정"
              >
                <Settings class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <!-- Chat Messages Area -->
      <div v-if="activeTab === 'chat'" class="flex-1 relative overflow-hidden">
        <!-- Messages Container with fixed height -->
        <div 
          ref="messagesContainer" 
          class="absolute inset-0 overflow-y-auto p-6 space-y-4"
          style="scroll-behavior: smooth; padding-bottom: 140px;"
          @scroll="handleScroll"
        >
          <!-- Welcome Message -->
          <div v-if="messages.length === 0" class="text-center py-12">
            <MessageCircle class="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 class="text-lg font-medium text-gray-900 mb-2">안녕하세요! 무엇을 도와드릴까요?</h3>
            <p class="text-gray-600 mb-6">자연어로 질문하시면 SQL 쿼리를 생성하고 결과를 보여드립니다.</p>
            
            <!-- Quick Start Questions -->
            <div class="max-w-2xl mx-auto">
              <p class="text-sm font-medium text-gray-700 mb-3">빠른 시작 질문:</p>
              <div class="grid gap-2">
                <button
                  v-for="sample in sampleQuestions"
                  :key="sample"
                  @click="sendMessage(sample)"
                  class="text-left p-3 bg-white border border-gray-200 hover:border-blue-300 rounded-lg transition-colors text-sm text-gray-700 hover:text-blue-700"
                >
                  {{ sample }}
                </button>
              </div>
            </div>
          </div>

          <!-- Chat Messages -->
          <ChatMessage
            v-for="message in messages"
            :key="message.id"
            :message="message"
            @save-query="saveQuery"
            @scroll-to-bottom="() => scrollToBottom(true)"
          />
        </div>

        <!-- Scroll to bottom button (shown when user is scrolled up) -->
        <div 
          v-if="isUserScrolledUp && messages.length > 0"
          class="absolute bottom-36 right-6 z-20"
        >
          <button
            @click="scrollToBottom(true)"
            class="bg-blue-600 text-white rounded-full p-3 shadow-lg hover:bg-blue-700 transition-all duration-200 flex items-center space-x-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"></path>
            </svg>
            <span class="text-sm">최신 메시지</span>
          </button>
        </div>

        <!-- Input Area - Fixed at bottom -->
        <div class="absolute bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4 shadow-lg z-10">
          <div class="flex space-x-4">
            <div class="flex-1">
              <textarea
                v-model="currentMessage"
                placeholder="질문을 입력하세요... (예: 지난 3개월간 가장 많이 팔린 제품 5개는?)"
                class="w-full resize-none border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows="2"
                @keydown.ctrl.enter="sendCurrentMessage"
                @keydown.enter.prevent="sendCurrentMessage"
                :disabled="!isConnected || loading || chatLoading || isStreaming"
              ></textarea>
            </div>
            <button
              @click="sendCurrentMessage"
              :disabled="!isConnected || !currentMessage.trim() || loading || chatLoading || isStreaming"
              class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              <Send class="w-4 h-4" />
            </button>
          </div>
          <p class="text-xs mt-2" :class="isConnected ? 'text-gray-500' : 'text-red-600'">
            <template v-if="!selectedConnectionId">먼저 DB 연결을 설정하세요.</template>
            <template v-else-if="selectedConnection?.status === 'error'">
              연결 오류: {{ selectedConnection.last_error || '연결을 확인하고 설정에서 테스트하세요.' }}
            </template>
            <template v-else-if="selectedConnection?.status === 'testing'">연결 테스트 중...</template>
            <template v-else-if="!selectedConnection?.status">연결 상태를 확인하려면 설정에서 테스트하세요.</template>
            <template v-else>{{ isStreaming ? '쿼리 처리 중...' : 'Ctrl+Enter 또는 Enter로 전송' }}</template>
          </p>
        </div>
      </div>

      <!-- History Tab -->
      <div v-else-if="activeTab === 'history'" class="flex-1 p-6 overflow-y-auto">
        <div v-if="sessions.length === 0" class="text-center py-12">
          <Clock class="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 class="text-lg font-medium text-gray-900 mb-2">대화 기록이 없습니다</h3>
          <p class="text-gray-600">새로운 채팅을 시작해보세요!</p>
        </div>
        
        <div v-else class="space-y-4">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">대화 기록 ({{ sessions.length }}개)</h3>
          
          <div 
            v-for="session in sessions" 
            :key="session.session_id"
            class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
            @click="switchToSessionAndGoToChat(session.session_id)"
          >
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <h4 class="font-medium text-gray-900">{{ session.title }}</h4>
                <p class="text-sm text-gray-600 mt-1">
                  {{ session.message_count }}개 메시지 • {{ formatDate(session.updated_at) }}
                </p>
              </div>
              <button
                @click.stop="confirmDeleteSession(session.session_id)"
                class="text-red-600 hover:text-red-800 p-2"
                title="세션 삭제"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Saved Queries Tab -->
      <div v-else-if="activeTab === 'saved'" class="flex-1 p-6">
        <div class="text-center py-12">
          <Bookmark class="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p class="text-gray-600">저장된 쿼리가 여기에 표시됩니다.</p>
        </div>
      </div>

      <!-- Database Info Tab -->
      <div v-else-if="activeTab === 'database'" class="flex-1 overflow-y-auto">
        <div class="p-6">
          <DatabaseInfo />
        </div>
      </div>

      <!-- Profile Tab -->
      <div v-else-if="activeTab === 'profile'" class="flex-1 p-6 overflow-y-auto">
        <UserProfile />
      </div>
    </div>

    <!-- Streaming Progress Modal -->
    <StreamingProgress
      :is-visible="isStreaming"
      :progress="streamingProgress"
      :current-message="streamingMessage"
      :events="streamingEvents"
      :error="streamingError"
      :is-streaming="isStreaming"
      @cancel="handleStreamingCancel"
      @close="handleStreamingClose"
    />

    <!-- Connection Panel -->
    <ConnectionPanel
      :open="isConnPanelOpen"
      @close="handleConnPanelClose"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, watch, computed } from 'vue';
import { useRouter } from 'vue-router';
import { 
  BarChart3, 
  MessageCircle, 
  Clock, 
  Bookmark, 
  LogOut, 
  Send,
  User,
  Menu,
  Database,
  Settings
} from 'lucide-vue-next';
import { useAuth } from '@/composables/useAuth';
import { useApi } from '@/composables/useApi';
import { useChatSession } from '@/composables/useChatSession';
import { useStreaming } from '@/composables/useStreaming';
import { useConnections } from '@/composables/useConnections';
import { logger } from '@/utils/logger';
import ChatMessage from './ChatMessage.vue';
import UserProfile from './UserProfile.vue';
import DatabaseInfo from './DatabaseInfo.vue';
import StreamingProgress from './StreamingProgress.vue';
import ConnectionPanel from './ConnectionPanel.vue';
import type { QueryResponse } from '@/types/api';

const router = useRouter();
const { user, logout: authLogout, fetchUserProfile, token } = useAuth();
const { loading } = useApi();
const {
  currentSession,
  sessions,
  loading: chatLoading,
  hasActiveSession,
  createNewSession,
  loadUserSessions,
  switchToSession,
  deleteSession,
  clearCurrentSession
} = useChatSession();

// Connections composable (DB 선택)
const { connections, selectedConnectionId, selectedConnection, fetchConnections } = useConnections();

// Raw messages from API
const rawMessages = ref<any[]>([]);

const {
  streamQuery,
  isStreaming,
  currentMessage: streamingMessage,
  progress: streamingProgress,
  events: streamingEvents,
  error: streamingError,
  clearEvents
} = useStreaming();

const activeTab = ref('chat');
const currentMessage = ref('');

// Watch user state changes
watch(user, (newUser, oldUser) => {
  logger.debug('User state changed in ChatInterface:', {
    hasNewUser: !!newUser,
    hasOldUser: !!oldUser,
    newUserEmail: newUser?.email,
    oldUserEmail: oldUser?.email
  });
}, { immediate: true });

const isConnected = computed(() => {
  // 연결 ID가 있으면 입력 허용 (테스트 목적으로 조건 완화)
  const hasConnectionId = !!selectedConnectionId.value;
  const connectionStatus = selectedConnection.value?.status;
  
  console.log('isConnected 계산:', {
    hasConnectionId,
    connectionStatus,
    selectedConnectionId: selectedConnectionId.value,
    selectedConnection: selectedConnection.value
  });
  
  // 일단 연결 ID만 있으면 허용
  return hasConnectionId;
});
const messagesContainer = ref<HTMLElement>();
const isUserScrolledUp = ref(false);
const shouldAutoScroll = ref(true);
const isCollapsed = ref(false);
const isConnPanelOpen = ref(false);

// UI Message interface for display
interface UIMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  queryResult?: QueryResponse;
  error?: string;
}

// Convert raw messages to UI messages
const messages = computed<UIMessage[]>(() => {
  const uiMessages: UIMessage[] = [];
  
  rawMessages.value.forEach((msg: any) => {
    console.log('Processing message:', msg); // 디버깅용 로그 추가
    
    // Each message from the API is already separated by type
    const hasSQL = msg.sql_query && msg.sql_query.trim() !== '';
    
    // 더 관대한 결과 체크 - 빈 배열이라도 queryResult 객체는 생성
    const results = msg.query_results || msg.query_result;
    const hasResults = results !== null && results !== undefined;
    
    console.log('SQL and Results check:', { 
      hasSQL, 
      hasResults, 
      sql_query: msg.sql_query, 
      query_results: msg.query_results, 
      query_result: msg.query_result,
      results_type: typeof results,
      results_value: results
    });
    
    uiMessages.push({
      id: msg.id,
      type: msg.message_type as 'user' | 'assistant',
      content: msg.content,
      timestamp: new Date(msg.timestamp || msg.created_at), // 두 필드 모두 시도
      queryResult: (hasSQL || hasResults) ? {
        sql_query: msg.sql_query || '',
        data: (() => {
          // query_results 또는 query_result 둘 다 시도
          const results = msg.query_results || msg.query_result;
          if (Array.isArray(results)) return results;
          if (typeof results === 'string') {
            try {
              const parsed = JSON.parse(results);
              return Array.isArray(parsed) ? parsed : [];
            } catch {
              return [];
            }
          }
          return [];
        })(),
        columns: (() => {
          const results = msg.query_results || msg.query_result;
          let data = [];
          if (Array.isArray(results)) {
            data = results;
          } else if (typeof results === 'string') {
            try {
              const parsed = JSON.parse(results);
              data = Array.isArray(parsed) ? parsed : [];
            } catch {
              data = [];
            }
          }
          return data && data.length > 0 ? Object.keys(data[0]) : [];
        })(),
        execution_time: msg.execution_time || 0,
        row_count: (() => {
          const results = msg.query_results || msg.query_result;
          let data = [];
          if (Array.isArray(results)) {
            data = results;
          } else if (typeof results === 'string') {
            try {
              data = JSON.parse(results);
            } catch {
              data = [];
            }
          }
          return Array.isArray(data) ? data.length : 0;
        })()
      } : undefined
    });
  });
  
  console.log('Processed UI messages:', uiMessages); // 디버깅용 로그 추가
  return uiMessages;
});

// Load messages for current session
const loadSessionMessages = async (sessionId: string) => {
  try {
    const { api } = useAuth();
    const response = await api.get(`/api/v1/chat/sessions/${sessionId}/messages`);
    rawMessages.value = response.data;
    console.log('Loaded messages:', response.data);
  } catch (error) {
    console.error('Failed to load messages:', error);
    rawMessages.value = [];
  }
};

const sampleQuestions = [
  "어떤 제품이 가장 많이 주문되었나요?",
  "1997년 월별 매출 현황을 보여주세요",
  "USA와 Germany의 고객 수를 비교해주세요",
  "Seafood 카테고리 제품들의 평균 단가는?",
  "직원 중 누가 가장 많은 주문을 처리했나요?"
];

// Helper functions
const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const switchToSessionAndGoToChat = async (sessionId: string) => {
  const success = await switchToSession(sessionId);
  if (success) {
    activeTab.value = 'chat';
    await loadSessionMessages(sessionId);
  }
};

const confirmDeleteSession = async (sessionId: string) => {
  if (confirm('이 대화를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
    await deleteSession(sessionId);
  }
};

const sendMessage = async (content: string) => {
  if (!content.trim()) return;

  // 연결 상태 검증
  if (!selectedConnectionId.value) {
    alert('먼저 DB 연결을 설정해주세요.');
    return;
  }

  if (selectedConnection.value?.status === 'error') {
    alert(`연결 오류: ${selectedConnection.value.last_error || '연결을 확인해주세요.'}`);
    return;
  }

  // Ensure session exists
  if (!hasActiveSession.value) {
    console.log('Creating new session...');
    const created = await createNewSession(`Chat - ${new Date().toLocaleString()}`);
    if (!created) {
      console.error('채팅 세션 생성 실패');
      return;
    }
    console.log('New session created:', currentSession.value);
  }

  // Verify we have a valid session ID
  if (!currentSession.value?.session_id) {
    console.error('세션 ID가 없습니다:', currentSession.value);
    return;
  }

  const sessionId = currentSession.value.session_id;
  console.log('Using session ID:', sessionId);

  // Clear input immediately for better UX
  currentMessage.value = '';

  // Use streaming for real-time feedback
  await streamQuery(
    content.trim(),
    sessionId,
    selectedConnectionId.value || undefined,
    // onProgress callback
    (event) => {
      console.log('Streaming event:', event);
    },
    // onComplete callback
    async (result) => {
      console.log('Query completed:', result);
      // Reload messages for current session
      await loadSessionMessages(sessionId);
      // Scroll to bottom after completion
      await nextTick();
      scrollToBottom(true);
    },
    // onError callback
    (error) => {
      console.error('Streaming error:', error);
    }
  );
};

// Start a new chat session
const startNewChat = async () => {
  clearCurrentSession();
  rawMessages.value = [];
  activeTab.value = 'chat';
  currentMessage.value = '';
  await nextTick();
  scrollToBottom(true);
};

// Streaming event handlers
const handleStreamingCancel = () => {
  // Stop the streaming process
  clearEvents();
};

const handleStreamingClose = () => {
  // Clear streaming events after completion
  clearEvents();
};

const sendCurrentMessage = () => {
  if (currentMessage.value.trim()) {
    sendMessage(currentMessage.value);
  }
};

const saveQuery = (queryData: any) => {
  // TODO: Implement save query functionality
  console.log('Saving query:', queryData);
};

const scrollToBottom = (force = false) => {
  if (messagesContainer.value && (shouldAutoScroll.value || force)) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

const handleScroll = () => {
  if (!messagesContainer.value) return;
  
  const container = messagesContainer.value;
  const threshold = 100; // 하단에서 100px 이내면 자동 스크롤 활성화
  
  const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < threshold;
  shouldAutoScroll.value = isNearBottom;
  isUserScrolledUp.value = !isNearBottom;
};

const logout = async () => {
  await authLogout();
  router.push('/login');
};

const getConnectionStatusText = () => {
  if (!selectedConnection.value) return 'DB 연결이 설정되지 않았습니다';
  
  switch (selectedConnection.value.status) {
    case 'connected':
      return '연결됨';
    case 'error':
      return `연결 오류: ${selectedConnection.value.last_error || '알 수 없는 오류'}`;
    case 'testing':
      return '연결 테스트 중...';
    default:
      return '연결 상태를 확인하려면 설정에서 테스트하세요';
  }
};

const handleConnPanelClose = () => {
  isConnPanelOpen.value = false;
  console.log('연결 패널 닫힘 후 상태:', {
    selectedConnectionId: selectedConnectionId.value,
    selectedConnection: selectedConnection.value,
    isConnected: isConnected.value
  });
};

// Watch computed messages for changes and auto-scroll
watch(
  () => messages.value.length,
  async () => {
    await nextTick();
    scrollToBottom();
  }
);

// Watch loading state to ensure scroll to bottom when response arrives
watch(
  () => loading.value || chatLoading.value,
  async (newLoading, oldLoading) => {
    // When loading ends (response received), scroll to bottom
    if (oldLoading && !newLoading) {
      await nextTick();
      setTimeout(() => scrollToBottom(), 100); // Small delay to ensure DOM is updated
    }
  }
);

onMounted(async () => {
  // Debug user state
  logger.debug('ChatInterface mounted - User state:', {
    hasUser: !!user.value,
    userEmail: user.value?.email,
    userFullName: user.value?.full_name,
    hasToken: !!token.value
  });
  
  // If we have a token but no user info, fetch user profile
  if (token.value && !user.value) {
    logger.debug('Token exists but no user info - fetching profile...');
    await fetchUserProfile();
  }
  
  // Load user's chat sessions & connections
  await loadUserSessions();
  
  try {
    await fetchConnections();
    logger.debug('연결 목록 로드 완료:', {
      count: connections.value.length,
      selectedId: selectedConnectionId.value
    });
  } catch (error: any) {
    logger.warn('연결 목록 로드 중 오류 발생 (계속 진행):', {
      status: error.response?.status,
      message: error.message
    });
    // 연결 목록 로드 실패해도 애플리케이션은 계속 동작
  }
  
  console.log('Connections loaded:', connections.value);
  console.log('Selected connection ID:', selectedConnectionId.value);
  console.log('Selected connection:', selectedConnection.value);
  console.log('Is connected:', isConnected.value);
});
</script>
