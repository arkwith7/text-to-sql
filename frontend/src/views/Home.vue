<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-6">
          <div class="flex items-center">
            <BarChart3 class="w-8 h-8 text-primary-600 mr-3" />
            <div>
              <h1 class="text-2xl font-bold text-gray-900">Smart Business Analytics Assistant</h1>
              <p class="text-sm text-gray-600">AI-powered natural language to SQL converter</p>
            </div>
          </div>
          <div class="flex items-center space-x-4">
            <!-- User info -->
            <div v-if="user" class="flex items-center space-x-4">
              <span class="text-sm text-gray-600">Welcome, {{ user.full_name }}</span>
              <nav class="flex space-x-2">
                <router-link
                  to="/"
                  class="bg-blue-100 text-blue-700 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Analytics
                </router-link>
                <router-link
                  to="/dashboard"
                  class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Dashboard
                </router-link>
              </nav>
            </div>
            <!-- Connection status -->
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
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Query Input Section -->
      <div class="card mb-8">
        <div class="mb-6">
          <h2 class="text-xl font-semibold text-gray-800 mb-2">Ask Your Business Question</h2>
          <p class="text-gray-600">Type your question in natural language and get instant SQL results</p>
        </div>

        <!-- Sample Questions -->
        <div class="mb-6">
          <p class="text-sm font-medium text-gray-700 mb-3">Try these sample questions:</p>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <button
              v-for="sample in sampleQuestions"
              :key="sample"
              @click="selectSampleQuestion(sample)"
              class="text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors duration-200 text-sm text-gray-700"
            >
              "{{ sample }}"
            </button>
          </div>
        </div>

        <!-- Query Input -->
        <div class="space-y-4">
          <textarea
            v-model="question"
            placeholder="예: 지난 3개월간 가장 많이 팔린 제품 5개는?"
            class="input-field h-24 resize-none"
            @keydown.ctrl.enter="executeQuery"
          ></textarea>
          
          <div class="flex justify-between items-center">
            <p class="text-xs text-gray-500">Tip: Press Ctrl+Enter to execute</p>
            <button
              @click="executeQuery"
              :disabled="!question.trim() || loading"
              class="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              <Search class="w-4 h-4 mr-2" />
              {{ loading ? 'Analyzing...' : 'Ask Question' }}
            </button>
          </div>
        </div>

        <!-- Error Display -->
        <div v-if="error" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div class="flex items-center">
            <AlertCircle class="w-5 h-5 text-red-500 mr-2" />
            <p class="text-red-700">{{ error }}</p>
          </div>
        </div>
      </div>

      <!-- Results Section -->
      <div v-if="queryResult" class="space-y-6">
        <!-- SQL Query Display -->
        <SqlDisplay :sql-query="queryResult.sql_query" />

        <!-- Data Visualization -->
        <div class="card">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-800">Results</h3>
            <div class="flex items-center space-x-2">
              <span class="text-sm text-gray-600">{{ queryResult.data.length }} rows</span>
              <select
                v-model="selectedChartType"
                class="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="table">Table</option>
                <option value="bar">Bar Chart</option>
                <option value="line">Line Chart</option>
                <option value="pie">Pie Chart</option>
              </select>
            </div>
          </div>
          
          <DataVisualization
            :data="queryResult.data"
            :columns="queryResult.columns"
            :chart-type="selectedChartType"
          />
        </div>

        <!-- AI Insights -->
        <InsightsPanel
          v-if="queryResult.insights"
          :insights="queryResult.insights"
        />
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="card">
        <div class="flex items-center justify-center py-12">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span class="ml-3 text-gray-600">Processing your question...</span>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="!queryResult && !loading" class="card">
        <div class="text-center py-12">
          <Database class="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 class="text-lg font-medium text-gray-900 mb-2">Ready to analyze your data</h3>
          <p class="text-gray-600">Ask a question above to get started with AI-powered analytics</p>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Search, BarChart3, AlertCircle, Database, Lightbulb } from 'lucide-vue-next';
import { useApi } from '@/composables/useApi';
import { useAuth } from '@/composables/useAuth';
import type { QueryResponse, ChartType } from '@/types/api';
import DataVisualization from '@/components/DataVisualization.vue';
import SqlDisplay from '@/components/SqlDisplay.vue';
import InsightsPanel from '@/components/InsightsPanel.vue';

const { loading, error, executeQuery: apiExecuteQuery, healthCheck } = useApi();
const { user } = useAuth();

const question = ref('');
const queryResult = ref<QueryResponse | null>(null);
const selectedChartType = ref<ChartType>('table');
const isConnected = ref(false);

const sampleQuestions = [
  '지난 3개월간 가장 많이 팔린 제품 5개는?',
  '부서별 평균 급여를 보여줘',
  '매월 매출 추이를 확인하고 싶어',
  '고객별 주문 횟수 상위 10명',
  '카테고리별 제품 수량',
  '가장 수익성이 높은 제품은?'
];

const selectSampleQuestion = (sample: string) => {
  question.value = sample;
};

const executeQuery = async () => {
  if (!question.value.trim()) return;
  
  const result = await apiExecuteQuery(question.value);
  if (result) {
    queryResult.value = result;
    selectedChartType.value = (result.chart_suggestion as ChartType) || 'table';
  }
};

const checkConnection = async () => {
  isConnected.value = await healthCheck();
};

onMounted(() => {
  checkConnection();
  // Check connection every 30 seconds
  setInterval(checkConnection, 30000);
});
</script>
