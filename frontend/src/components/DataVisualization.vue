<template>
  <div class="w-full">
    <div v-if="chartType === 'table'" class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th
              v-for="column in columns"
              :key="column"
              class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              {{ column }}
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="(row, index) in data" :key="index">
            <td
              v-for="column in columns"
              :key="column"
              class="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
            >
              {{ formatValue(row[column]) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div v-else-if="!isChartable.valid" class="w-full h-96 bg-gray-50 rounded-md flex items-center justify-center">
      <div class="text-center max-w-md px-4">
        <svg class="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
        </svg>
        <h3 class="text-lg font-medium text-gray-900 mb-2">차트를 생성할 수 없습니다</h3>
        <p class="text-sm text-gray-600 leading-relaxed">{{ isChartable.reason }}</p>
        <p class="text-xs text-gray-500 mt-3">💡 테이블 형태로 데이터를 확인해보세요.</p>
      </div>
    </div>
    
    <div v-else-if="isChartable.valid && chartData" class="w-full h-96">
      <Bar
        v-if="chartType === 'bar'"
        :data="chartData"
        :options="chartOptions"
      />
      <Line
        v-else-if="chartType === 'line'"
        :data="chartData"
        :options="chartOptions"
      />
      <Pie
        v-else-if="chartType === 'pie'"
        :data="chartData"
        :options="chartOptions"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar, Line, Pie } from 'vue-chartjs';
import type { ChartType } from '@/types/api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

interface Props {
  data: Record<string, any>[];
  columns: string[];
  chartType: ChartType;
}

const props = defineProps<Props>();

const formatValue = (value: any): string => {
  if (value === null || value === undefined) return 'N/A';
  if (typeof value === 'number') {
    return value.toLocaleString();
  }
  return String(value);
};

// 차트를 그릴 수 있는 데이터인지 검사
const isChartable = computed(() => {
  // 기본 조건: 데이터가 있고, 컬럼이 2개 이상이어야 함
  if (!props.data || props.data.length === 0 || props.columns.length < 2) {
    return { valid: false, reason: '차트를 그리려면 최소 2개의 컬럼과 1개 이상의 데이터가 필요합니다.' };
  }

  // 두 번째 컬럼(값)이 숫자형 데이터인지 확인
  const hasNumericData = props.data.some(row => {
    const value = row[props.columns[1]];
    return typeof value === 'number' || (!isNaN(Number(value)) && value !== null && value !== '');
  });

  if (!hasNumericData) {
    return { valid: false, reason: '차트를 그리려면 숫자형 데이터가 포함된 컬럼이 필요합니다.' };
  }

  // 데이터가 너무 많은 경우 (파이차트 제한)
  if (props.chartType === 'pie' && props.data.length > 10) {
    return { valid: false, reason: '파이차트는 최대 10개 항목까지만 표시할 수 있습니다. 막대차트나 선차트를 사용해보세요.' };
  }

  return { valid: true, reason: '' };
});

const chartData = computed(() => {
  if (props.chartType === 'table' || props.data.length === 0 || props.columns.length < 2) {
    return null;
  }

  const labels = props.data.map(row => String(row[props.columns[0]]));
  const values = props.data.map(row => {
    const value = row[props.columns[1]];
    return typeof value === 'number' ? value : (Number(value) || 0);
  });

  const colors = [
    '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
    '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6366f1'
  ];

  if (props.chartType === 'pie') {
    return {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: colors.slice(0, values.length),
          borderColor: colors.slice(0, values.length),
          borderWidth: 1,
        },
      ],
    };
  }

  return {
    labels,
    datasets: [
      {
        label: props.columns[1],
        data: values,
        backgroundColor: props.chartType === 'bar' ? '#3b82f6' : undefined,
        borderColor: '#3b82f6',
        borderWidth: 2,
        fill: false,
      },
    ],
  };
});

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
    },
    title: {
      display: false,
    },
  },
  scales: props.chartType !== 'pie' ? {
    y: {
      beginAtZero: true,
    },
  } : {},
}));
</script>
