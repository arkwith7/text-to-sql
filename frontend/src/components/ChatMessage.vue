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

          <!-- Success Response -->
          <div v-else-if="message.queryResult">
            <!-- SQL Query Display -->
            <div class="mb-4">
              <h4 class="text-sm font-medium text-gray-700 mb-2">생성된 SQL 쿼리:</h4>
              <div class="bg-gray-50 rounded-md p-3 font-mono text-sm text-gray-800 overflow-x-auto">
                {{ message.queryResult.sql_query }}
              </div>
              <div class="flex justify-between items-center mt-2">
                <span class="text-xs text-gray-500">
                  실행 시간: {{ Math.round(message.queryResult.execution_time * 1000) }}ms
                </span>
                <button
                  @click="copyQuery"
                  class="text-xs text-blue-600 hover:text-blue-800 flex items-center"
                >
                  <Copy class="w-3 h-3 mr-1" />
                  복사
                </button>
              </div>
            </div>

            <!-- Results Display -->
            <div class="mb-4">
              <div class="flex items-center justify-between mb-2">
                <h4 class="text-sm font-medium text-gray-700">
                  결과 ({{ message.queryResult.row_count }}행)
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

          <!-- Regular text message -->
          <div v-else class="text-sm text-gray-800">
            {{ message.content }}
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
import { ref, computed } from 'vue';
import { 
  AlertCircle, 
  Copy, 
  Bookmark, 
  BarChart3 
} from 'lucide-vue-next';

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
}>();

const selectedView = ref('table');
const displayLimit = ref(10);

const displayData = computed(() => {
  if (!props.message.queryResult?.data) return [];
  return props.message.queryResult.data.slice(0, displayLimit.value);
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

const showMore = () => {
  displayLimit.value += 10;
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
