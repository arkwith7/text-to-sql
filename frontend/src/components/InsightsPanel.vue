<template>
  <div class="card">
    <div class="flex items-center mb-3">
      <Lightbulb class="w-5 h-5 text-yellow-500 mr-2" />
      <h3 class="text-lg font-semibold text-gray-800">AI Insights</h3>
    </div>
    
    <div class="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-r-md">
      <p class="text-gray-700 leading-relaxed">{{ insights }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Lightbulb } from 'lucide-vue-next';

interface Props {
  insights: string;
}

defineProps<Props>();
</script>
