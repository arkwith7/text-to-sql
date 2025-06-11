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
    
    <div v-else class="w-full h-96">
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

const chartData = computed(() => {
  if (props.chartType === 'table' || props.data.length === 0) {
    return null;
  }

  const labels = props.data.map(row => String(row[props.columns[0]]));
  const values = props.data.map(row => {
    const value = row[props.columns[1]];
    return typeof value === 'number' ? value : 0;
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
