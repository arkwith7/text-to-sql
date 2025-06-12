<template>
  <div v-if="isVisible" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
      <!-- Header -->
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-medium text-gray-900">
          {{ title }}
        </h3>
        <button
          v-if="canCancel"
          @click="$emit('cancel')"
          class="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Current Status Message -->
      <div class="mb-4">
        <p class="text-sm text-gray-600 mb-2">{{ currentMessage || '처리 중...' }}</p>
        
        <!-- Progress Bar -->
        <div class="w-full bg-gray-200 rounded-full h-2">
          <div 
            class="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
            :style="{ width: `${progress}%` }"
          ></div>
        </div>
        <div class="flex justify-between text-xs text-gray-500 mt-1">
          <span>진행률</span>
          <span>{{ progress }}%</span>
        </div>
      </div>

      <!-- Detailed Steps (Expandable) -->
      <div class="mb-4">
        <button
          @click="showDetails = !showDetails"
          class="flex items-center text-sm text-blue-600 hover:text-blue-800 transition-colors"
        >
          <ChevronDown 
            class="w-4 h-4 mr-1 transition-transform"
            :class="{ 'rotate-180': showDetails }"
          />
          세부 진행 상황 {{ showDetails ? '숨기기' : '보기' }}
        </button>

        <div v-if="showDetails" class="mt-3 space-y-2 max-h-32 overflow-y-auto">
          <div
            v-for="(event, index) in events"
            :key="index"
            class="flex items-center text-xs"
            :class="getEventStatusClass(event, index)"
          >
            <div class="w-4 h-4 mr-2 flex items-center justify-center">
              <Check v-if="isEventCompleted(event, index)" class="w-3 h-3 text-green-600" />
              <div v-else-if="isCurrentEvent(event, index)" class="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
              <div v-else class="w-2 h-2 bg-gray-300 rounded-full"></div>
            </div>
            <span>{{ getEventDisplayText(event.event) }}</span>
            <span class="ml-auto text-gray-400">
              {{ formatTime(event.timestamp) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Error Display -->
      <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
        <div class="flex items-center">
          <AlertCircle class="w-4 h-4 text-red-600 mr-2" />
          <span class="text-sm text-red-800">{{ error }}</span>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex justify-end space-x-2">
        <button
          v-if="canCancel && isStreaming"
          @click="$emit('cancel')"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
        >
          취소
        </button>
        <button
          v-if="!isStreaming"
          @click="$emit('close')"
          class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors"
        >
          확인
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { X, ChevronDown, Check, AlertCircle } from 'lucide-vue-next';
import type { StreamEvent } from '@/composables/useStreaming';

interface Props {
  isVisible: boolean;
  title?: string;
  progress: number;
  currentMessage: string | null;
  events: StreamEvent[];
  error: string | null;
  isStreaming: boolean;
  canCancel?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  title: '쿼리 실행 중...',
  canCancel: true
});

defineEmits<{
  cancel: [];
  close: [];
}>();

const showDetails = ref(false);

const eventDisplayTexts: Record<string, string> = {
  query_started: '쿼리 처리 시작',
  session_creating: '새 세션 생성 중...',
  session_created: '세션 생성 완료',
  analyzing: '질문 분석 중...',
  generating_sql: 'SQL 쿼리 생성 중...',
  sql_generated: 'SQL 쿼리 생성 완료',
  executing_query: '데이터베이스 쿼리 실행 중...',
  processing_results: '결과 처리 중...',
  generating_insights: '인사이트 생성 중...',
  query_completed: '쿼리 실행 완료',
  error: '오류 발생',
  connected: '연결됨',
  disconnected: '연결 해제됨',
  heartbeat: '연결 상태 확인'
};

const getEventDisplayText = (eventType: string): string => {
  return eventDisplayTexts[eventType] || eventType;
};

const isEventCompleted = (event: StreamEvent, index: number): boolean => {
  const currentIndex = props.events.length - 1;
  return index < currentIndex || event.event === 'query_completed';
};

const isCurrentEvent = (event: StreamEvent, index: number): boolean => {
  const currentIndex = props.events.length - 1;
  return index === currentIndex && props.isStreaming;
};

const getEventStatusClass = (event: StreamEvent, index: number): string => {
  if (event.event === 'error') {
    return 'text-red-600';
  }
  
  if (isEventCompleted(event, index)) {
    return 'text-green-600';
  }
  
  if (isCurrentEvent(event, index)) {
    return 'text-blue-600 font-medium';
  }
  
  return 'text-gray-500';
};

const formatTime = (timestamp: string): string => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};
</script>
