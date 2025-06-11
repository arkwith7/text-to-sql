<template>
  <div class="card">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-gray-800">Generated SQL Query</h3>
      <button
        @click="copyToClipboard"
        class="btn-secondary text-sm"
        :class="{ 'bg-green-100 text-green-800': copied }"
      >
        <Copy class="w-4 h-4 mr-1" />
        {{ copied ? 'Copied!' : 'Copy' }}
      </button>
    </div>
    
    <div class="bg-gray-900 rounded-lg p-4 overflow-x-auto">
      <Prism 
        language="sql" 
        :code="sqlQuery"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Copy } from 'lucide-vue-next';
import Prism from 'vue-prism-component';
import 'prismjs';
import 'prismjs/components/prism-sql';
import 'prismjs/themes/prism-tomorrow.css';

interface Props {
  sqlQuery: string;
}

const props = defineProps<Props>();

const copied = ref(false);

const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(props.sqlQuery);
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 2000);
  } catch (err) {
    console.error('Failed to copy text: ', err);
  }
};
</script>
