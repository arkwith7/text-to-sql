<template>
  <div class="flex h-screen bg-gray-50">
    <!-- Sidebar -->
    <div class="w-64 bg-white border-r border-gray-200 flex flex-col">
      <!-- Sidebar Header -->
      <div class="p-4 border-b border-gray-200">
        <div class="flex items-center">
          <BarChart3 class="w-8 h-8 text-blue-600 mr-3" />
          <div>
            <h1 class="text-lg font-bold text-gray-900">SQL Assistant</h1>
            <p class="text-xs text-gray-600">AI-powered analytics</p>
          </div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 p-4">
        <div class="space-y-2">
          <button
            @click="activeTab = 'chat'"
            :class="[
              'w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg',
              activeTab === 'chat' 
                ? 'bg-blue-100 text-blue-700' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            ]"
          >
            <MessageCircle class="w-4 h-4 mr-3" />
            채팅
          </button>
          
          <button
            @click="activeTab = 'history'"
            :class="[
              'w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg',
              activeTab === 'history' 
                ? 'bg-blue-100 text-blue-700' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            ]"
          >
            <Clock class="w-4 h-4 mr-3" />
            대화 기록
          </button>
          
          <button
            @click="activeTab = 'saved'"
            :class="[
              'w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg',
              activeTab === 'saved' 
                ? 'bg-blue-100 text-blue-700' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            ]"
          >
            <Bookmark class="w-4 h-4 mr-3" />
            저장된 쿼리
          </button>
        </div>
      </nav>

      <!-- User Info -->
      <div class="p-4 border-t border-gray-200">
        <div v-if="user" class="flex items-center">
          <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
            {{ user.full_name?.charAt(0).toUpperCase() }}
          </div>
          <div class="ml-3 flex-1">
            <p class="text-sm font-medium text-gray-900">{{ user.full_name }}</p>
            <p class="text-xs text-gray-500">{{ user.email }}</p>
          </div>
          <button
            @click="logout"
            class="text-gray-400 hover:text-gray-600"
          >
            <LogOut class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col">
      <!-- Header -->
      <header class="bg-white border-b border-gray-200 px-6 py-4">
        <div class="flex items-center justify-between">
          <h2 class="text-xl font-semibold text-gray-900">
            {{ activeTab === 'chat' ? '새로운 질문' : activeTab === 'history' ? '대화 기록' : '저장된 쿼리' }}
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
      <div v-if="activeTab === 'chat'" class="flex-1 flex flex-col">
        <!-- Messages Container -->
        <div ref="messagesContainer" class="flex-1 overflow-y-auto p-6 space-y-4">
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
          />
        </div>

        <!-- Input Area -->
        <div class="border-t border-gray-200 p-4 bg-white">
          <div class="flex space-x-4">
            <div class="flex-1">
              <textarea
                v-model="currentMessage"
                placeholder="질문을 입력하세요... (예: 지난 3개월간 가장 많이 팔린 제품 5개는?)"
                class="w-full resize-none border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows="2"
                @keydown.ctrl.enter="sendCurrentMessage"
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
          <p class="text-xs text-gray-500 mt-2">Ctrl+Enter로 전송</p>
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { 
  BarChart3, 
  MessageCircle, 
  Clock, 
  Bookmark, 
  LogOut, 
  Send 
} from 'lucide-vue-next';
import { useAuth } from '@/composables/useAuth';
import { useApi } from '@/composables/useApi';
import ChatMessage from './ChatMessage.vue';
import type { QueryResponse } from '@/types/api';

const router = useRouter();
const { user, logout: authLogout } = useAuth();
const { executeQuery: apiExecuteQuery, loading } = useApi();

const activeTab = ref('chat');
const currentMessage = ref('');
const isConnected = ref(true);
const messagesContainer = ref<HTMLElement>();

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

  // Scroll to bottom
  await nextTick();
  scrollToBottom();

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
  } finally {
    await nextTick();
    scrollToBottom();
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

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

const logout = async () => {
  await authLogout();
  router.push('/login');
};

onMounted(() => {
  // Check connection status
  // TODO: Implement actual connection check
});
</script>
