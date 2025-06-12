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
               activeTab === 'profile' ? '사용자 프로필' : '새로운 질문' }}
          </h2>
          
          <!-- Connection Status -->
          <div
            class="flex items-center px-3 py-1 rounded-full text-sm"
            :class="isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
          >
            <div
              class="w-2 h-2 rounded-full mr-2"
              :class="isConnected ? 'bg-green-500' : 'bg-red-500'"
            ></div>
            {{ isConnected ? 'Connected' : 'Disconnected' }}
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
                :disabled="loading"
              ></textarea>
            </div>
            <button
              @click="sendCurrentMessage"
              :disabled="!currentMessage.trim() || loading"
              class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              <Send class="w-4 h-4" />
            </button>
          </div>
          <p class="text-xs text-gray-500 mt-2">Ctrl+Enter 또는 Enter로 전송</p>
        </div>
      </div>

      <!-- History Tab -->
      <div v-else-if="activeTab === 'history'" class="flex-1 p-6">
        <div class="text-center py-12">
          <Clock class="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p class="text-gray-600">대화 기록이 여기에 표시됩니다.</p>
        </div>
      </div>

      <!-- Saved Queries Tab -->
      <div v-else-if="activeTab === 'saved'" class="flex-1 p-6">
        <div class="text-center py-12">
          <BookMark class="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p class="text-gray-600">저장된 쿼리가 여기에 표시됩니다.</p>
        </div>
      </div>

      <!-- Profile Tab -->
      <div v-else-if="activeTab === 'profile'" class="flex-1 p-6 overflow-y-auto">
        <UserProfile />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { 
  BarChart3, 
  MessageCircle, 
  Clock, 
  Bookmark, 
  LogOut, 
  Send,
  User,
  Menu
} from 'lucide-vue-next';
import { useAuth } from '@/composables/useAuth';
import { useApi } from '@/composables/useApi';
import ChatMessage from './ChatMessage.vue';
import UserProfile from './UserProfile.vue';
import type { QueryResponse } from '@/types/api';

const router = useRouter();
const { user, logout: authLogout } = useAuth();
const { executeQuery: apiExecuteQuery, loading } = useApi();

const activeTab = ref('chat');
const currentMessage = ref('');
const isConnected = ref(true);
const messagesContainer = ref<HTMLElement>();
const isUserScrolledUp = ref(false);
const shouldAutoScroll = ref(true);
const isCollapsed = ref(false);

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  queryResult?: QueryResponse;
  error?: string;
}

const messages = ref<Message[]>([]);

const sampleQuestions = [
  "지난 3개월간 가장 많이 팔린 제품 5개는?",
  "월별 매출 추이를 보여주세요",
  "고객별 주문 횟수를 알려주세요",
  "카테고리별 평균 주문 금액은?"
];

const sendMessage = async (content: string) => {
  if (!content.trim()) return;

  // Add user message
  const userMessage: Message = {
    id: Date.now().toString(),
    type: 'user',
    content: content.trim(),
    timestamp: new Date()
  };
  messages.value.push(userMessage);

  // Clear input
  currentMessage.value = '';

  // Scroll to bottom after user message
  await nextTick();
  scrollToBottom(true);

  try {
    const response = await apiExecuteQuery(content.trim());

    if (response) {
      // Add assistant response
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `질문: "${content}"\n\n결과를 확인해주세요.`,
        timestamp: new Date(),
        queryResult: response
      };
      messages.value.push(assistantMessage);
    }

  } catch (error) {
    // Add error message
    const errorMessage: Message = {
      id: (Date.now() + 1).toString(),
      type: 'assistant',
      content: '죄송합니다. 요청을 처리하는 중 오류가 발생했습니다.',
      timestamp: new Date(),
      error: error instanceof Error ? error.message : '알 수 없는 오류'
    };
    messages.value.push(errorMessage);
  }
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

// Watch messages array for changes and auto-scroll
watch(
  () => messages.value.length,
  async () => {
    await nextTick();
    scrollToBottom();
  }
);

// Watch loading state to ensure scroll to bottom when response arrives
watch(
  () => loading.value,
  async (newLoading, oldLoading) => {
    // When loading ends (response received), scroll to bottom
    if (oldLoading && !newLoading) {
      await nextTick();
      setTimeout(() => scrollToBottom(), 100); // Small delay to ensure DOM is updated
    }
  }
);

onMounted(() => {
  // Check connection status
  // TODO: Implement actual connection check
});
</script>
