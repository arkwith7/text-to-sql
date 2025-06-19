<template>
  <div class="flex" :class="message.type === 'user' ? 'justify-end' : 'justify-start'">
    <div
      class="max-w-3xl"
      :class="message.type === 'user' ? 'ml-12' : 'mr-12'"
    >
      <!-- Message Content -->
      <div
        class="rounded-lg px-4 py-3"
        :class="[
          message.type === 'user' 
            ? 'bg-blue-600 text-white' 
            : 'bg-white border border-gray-200'
        ]"
      >
        <!-- User Message -->
        <div v-if="message.type === 'user'" class="text-sm">
          {{ message.content }}
        </div>

        <!-- Assistant Message -->
        <div v-else class="space-y-4">
          <!-- Error Message -->
          <div v-if="message.error" class="flex items-center text-red-600">
            <AlertCircle class="w-4 h-4 mr-2" />
            <span class="text-sm">{{ message.error }}</span>
          </div>

          <!-- AI Response/Explanation (항상 표시) -->
          <div v-if="message.content && message.content.trim()" class="mb-4">
            <div class="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-r-md">
              <div class="flex items-start">
                <MessageSquare class="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
                <div 
                  v-if="message.type === 'assistant'"
                  class="text-sm text-blue-800 leading-relaxed prose prose-sm prose-blue max-w-none"
                  v-html="renderedContent"
                ></div>
                <div 
                  v-else
                  class="text-sm text-blue-800 leading-relaxed whitespace-pre-wrap"
                >{{ message.content }}</div>
              </div>
            </div>
            
            <!-- Help suggestions for specific error messages -->
            <div v-if="isComplexQueryError" class="mt-3 bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-r-md">
              <div class="flex items-start">
                <AlertCircle class="w-5 h-5 text-yellow-600 mt-0.5 mr-3 flex-shrink-0" />
                <div class="text-sm text-yellow-800">
                  <p class="font-medium mb-2">💡 도움말:</p>
                  <ul class="space-y-1 text-xs">
                    <li>• 질문을 더 구체적으로 표현해 보세요</li>
                    <li>• 테이블명이나 컬럼명을 정확히 지정해 보세요</li>
                    <li>• 예: "고객 정보를 보여줘" → "Customers 테이블에서 회사명과 연락처를 보여줘"</li>
                    <li>• 복잡한 조건이 있다면 단계별로 나누어 질문하세요</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <!-- SQL Query and Results (SQL 쿼리나 결과가 있을 때) -->
          <div v-if="message.queryResult && (message.queryResult.sql_query || (message.queryResult.data && message.queryResult.data.length > 0))">
            <!-- SQL Query Display -->
            <div v-if="message.queryResult.sql_query && message.queryResult.sql_query.trim() !== ''" class="mb-4">
              <h4 class="text-sm font-medium text-gray-700 mb-2 flex items-center">
                <Code class="w-4 h-4 mr-2" />
                생성된 SQL 쿼리:
              </h4>
              <div class="bg-gray-50 rounded-md p-3 font-mono text-sm text-gray-800 overflow-x-auto border">
                {{ message.queryResult.sql_query }}
              </div>
              <div class="flex justify-between items-center mt-2">
                <span class="text-xs text-gray-500">
                  실행 시간: {{ Math.round(message.queryResult.execution_time * 1000) }}ms
                </span>
                <button
                  @click="copyQuery"
                  class="text-xs text-blue-600 hover:text-blue-800 flex items-center transition-colors"
                >
                  <Copy class="w-3 h-3 mr-1" />
                  복사
                </button>
              </div>
            </div>

            <!-- Results Display -->
            <div v-if="message.queryResult.data && message.queryResult.data.length > 0" class="mb-4">
              <div class="flex items-center justify-between mb-2">
                <h4 class="text-sm font-medium text-gray-700">
                  결과 ({{ message.queryResult.row_count || message.queryResult.data.length }}행)
                </h4>
                <div class="flex items-center space-x-2">
                  <select
                    v-model="selectedView"
                    class="text-xs border border-gray-300 rounded px-2 py-1"
                  >
                    <option value="table">테이블</option>
                    <option value="chart">차트</option>
                  </select>
                  <button
                    @click="saveQuery"
                    class="text-xs text-blue-600 hover:text-blue-800 flex items-center"
                  >
                    <Bookmark class="w-3 h-3 mr-1" />
                    저장
                  </button>
                </div>
              </div>

              <!-- Table View -->
              <div v-if="selectedView === 'table'" class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200 text-sm">
                  <thead class="bg-gray-50">
                    <tr>
                      <th
                        v-for="column in message.queryResult.columns"
                        :key="column"
                        class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        {{ column }}
                      </th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    <tr
                      v-for="(row, index) in displayData"
                      :key="index"
                      class="hover:bg-gray-50"
                    >
                      <td
                        v-for="column in message.queryResult.columns"
                        :key="column"
                        class="px-3 py-2 whitespace-nowrap text-gray-900"
                      >
                        {{ formatValue(row[column]) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
                
                <!-- Show More Button -->
                <div v-if="message.queryResult.data.length > displayLimit" class="text-center mt-4">
                  <button
                    @click="showMore"
                    class="text-sm text-blue-600 hover:text-blue-800"
                  >
                    더 보기 ({{ message.queryResult.data.length - displayLimit }}개 남음)
                  </button>
                </div>
              </div>

              <!-- Chart View -->
              <div v-else-if="selectedView === 'chart'" class="h-64 bg-gray-50 rounded-md flex items-center justify-center">
                <div class="text-center">
                  <BarChart3 class="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <p class="text-sm text-gray-600">차트 기능 개발 중</p>
                </div>
              </div>
            </div>

            <!-- Insights -->
            <div v-if="message.queryResult.insights" class="bg-blue-50 rounded-md p-3">
              <h4 class="text-sm font-medium text-blue-800 mb-1">💡 인사이트</h4>
              <p class="text-sm text-blue-700">{{ message.queryResult.insights }}</p>
            </div>

            <!-- Explanation -->
            <div v-if="message.queryResult.explanation" class="bg-gray-50 rounded-md p-3">
              <h4 class="text-sm font-medium text-gray-700 mb-1">설명</h4>
              <p class="text-sm text-gray-600">{{ message.queryResult.explanation }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Timestamp -->
      <div
        class="text-xs text-gray-500 mt-1"
        :class="message.type === 'user' ? 'text-right' : 'text-left'"
      >
        {{ formatTime(message.timestamp) }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue';
import MarkdownIt from 'markdown-it';
import { 
  AlertCircle, 
  Copy, 
  Bookmark, 
  BarChart3,
  MessageSquare,
  Code
} from 'lucide-vue-next';

// 마크다운 파서 초기화
const md = new MarkdownIt({
  html: false, // HTML 태그 비활성화 (보안)
  breaks: true, // 줄바꿈을 <br>로 변환
  linkify: true, // 자동 링크 생성
  typographer: true // 타이포그래피 개선
});

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  queryResult?: any;
  error?: string;
}

const props = defineProps<{
  message: Message;
}>();

const emit = defineEmits<{
  saveQuery: [queryData: any];
  scrollToBottom: [];
}>();

const selectedView = ref('table');
const displayLimit = ref(10);

const displayData = computed(() => {
  if (!props.message.queryResult?.data) return [];
  return props.message.queryResult.data.slice(0, displayLimit.value);
});

const isComplexQueryError = computed(() => {
  return props.message.content?.includes('질문이 너무 복잡하거나 데이터베이스 구조에 맞는 답변을 찾지 못했습니다');
});

// 마크다운 렌더링
const renderedContent = computed(() => {
  if (props.message.type === 'user' || !props.message.content) {
    return props.message.content;
  }
  // Assistant 메시지는 마크다운으로 렌더링
  return md.render(props.message.content);
});

const copyQuery = async () => {
  if (props.message.queryResult?.sql_query) {
    try {
      await navigator.clipboard.writeText(props.message.queryResult.sql_query);
      // TODO: Show toast notification
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }
};

const saveQuery = () => {
  if (props.message.queryResult) {
    emit('saveQuery', {
      query: props.message.queryResult.sql_query,
      question: props.message.content,
      timestamp: props.message.timestamp
    });
  }
};

const showMore = async () => {
  displayLimit.value += 10;
  // Allow some time for DOM to update then scroll to maintain position
  await nextTick();
  setTimeout(() => {
    emit('scrollToBottom');
  }, 50);
};

const formatValue = (value: any): string => {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'number') {
    return value.toLocaleString();
  }
  return String(value);
};

const formatTime = (date: Date): string => {
  return date.toLocaleTimeString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit'
  });
};
</script>

<style scoped>
/* 마크다운 콘텐츠를 위한 커스텀 스타일 */
.prose {
  --tw-prose-body: #1e40af;
  --tw-prose-headings: #1e3a8a;
  --tw-prose-lead: #1e40af;
  --tw-prose-links: #2563eb;
  --tw-prose-bold: #1e3a8a;
  --tw-prose-counters: #6b7280;
  --tw-prose-bullets: #d1d5db;
  --tw-prose-hr: #e5e7eb;
  --tw-prose-quotes: #1e40af;
  --tw-prose-quote-borders: #e5e7eb;
  --tw-prose-captions: #6b7280;
  --tw-prose-code: #1e3a8a;
  --tw-prose-pre-code: #e5e7eb;
  --tw-prose-pre-bg: #1f2937;
  --tw-prose-th-borders: #d1d5db;
  --tw-prose-td-borders: #e5e7eb;
}

.prose :deep(p) {
  margin-top: 0.75em;
  margin-bottom: 0.75em;
}

.prose :deep(p:first-child) {
  margin-top: 0;
}

.prose :deep(p:last-child) {
  margin-bottom: 0;
}

.prose :deep(ul) {
  margin-top: 0.75em;
  margin-bottom: 0.75em;
  padding-left: 1.25em;
}

.prose :deep(ol) {
  margin-top: 0.75em;
  margin-bottom: 0.75em;
  padding-left: 1.25em;
}

.prose :deep(li) {
  margin-top: 0.25em;
  margin-bottom: 0.25em;
}

.prose :deep(code) {
  background-color: #f3f4f6;
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
}

.prose :deep(pre) {
  background-color: #1f2937;
  color: #e5e7eb;
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin-top: 0.75em;
  margin-bottom: 0.75em;
}

.prose :deep(blockquote) {
  border-left: 4px solid #e5e7eb;
  padding-left: 1rem;
  margin-top: 0.75em;
  margin-bottom: 0.75em;
  font-style: italic;
}

.prose :deep(h1), 
.prose :deep(h2), 
.prose :deep(h3), 
.prose :deep(h4), 
.prose :deep(h5), 
.prose :deep(h6) {
  font-weight: 600;
  margin-top: 1em;
  margin-bottom: 0.5em;
}

.prose :deep(h1:first-child), 
.prose :deep(h2:first-child), 
.prose :deep(h3:first-child), 
.prose :deep(h4:first-child), 
.prose :deep(h5:first-child), 
.prose :deep(h6:first-child) {
  margin-top: 0;
}

.prose :deep(strong) {
  font-weight: 600;
}

.prose :deep(em) {
  font-style: italic;
}

.prose :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin-top: 0.75em;
  margin-bottom: 0.75em;
}

.prose :deep(th), 
.prose :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 0.5rem;
  text-align: left;
}

.prose :deep(th) {
  background-color: #f9fafb;
  font-weight: 600;
}
</style>
