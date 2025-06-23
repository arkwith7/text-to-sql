<template>
  <div class="h-screen flex flex-col">
    <!-- Header -->
    <header class="bg-base-200 p-4 flex justify-between items-center shadow-md z-10">
      <h1 class="text-xl font-bold">Business Analytics Assistant</h1>
      <div class="flex items-center space-x-4">
        <select v-model="selectedConnection" class="select select-bordered select-sm w-full max-w-xs">
          <option disabled value="">Select a Database</option>
          <option v-for="conn in connections" :key="conn.id" :value="conn.id">
            {{ conn.connection_name }}
          </option>
        </select>
        <router-link to="/connections" class="btn btn-sm">Manage Connections</router-link>
      </div>
    </header>

    <!-- Main Content -->
    <div class="flex-grow flex overflow-hidden">
      <!-- Chat Interface takes the full width now -->
      <div class="flex-grow h-full">
        <ChatInterface v-if="selectedConnection" :connection-id="selectedConnection" :key="selectedConnection" />
        <div v-else class="flex items-center justify-center h-full">
          <div class="text-center">
            <p class="text-lg">Please select a database connection to start.</p>
            <p class="text-sm">If you don't have one, you can <router-link to="/connections" class="link">add one here</router-link>.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import ChatInterface from '@/components/ChatInterface.vue';
import { useApi } from '@/composables/useApi';

const { getConnections } = useApi();
const connections = ref<any[]>([]);
const selectedConnection = ref<string>('');

onMounted(async () => {
  try {
    const response = await getConnections();
    connections.value = response.data; // Assuming API returns { data: [...] }
    if (connections.value.length > 0) {
      selectedConnection.value = connections.value[0].id;
    }
  } catch (error) {
    console.error("Failed to fetch connections:", error);
  }
});
</script>
