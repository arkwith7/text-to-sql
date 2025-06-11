<template>
  <div class="bg-white rounded-lg shadow p-6">
    <div class="flex items-center justify-between mb-6">
      <h3 class="text-lg font-semibold text-gray-800">User Profile</h3>
      <button
        @click="logout"
        class="text-sm text-red-600 hover:text-red-800 flex items-center"
      >
        <LogOut class="w-4 h-4 mr-1" />
        Logout
      </button>
    </div>

    <div v-if="user" class="space-y-4">
      <!-- User Info -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Full Name
          </label>
          <p class="text-gray-900">{{ user.full_name }}</p>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Email
          </label>
          <p class="text-gray-900">{{ user.email }}</p>
        </div>
        
        <div v-if="user.company">
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Company
          </label>
          <p class="text-gray-900">{{ user.company }}</p>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Member Since
          </label>
          <p class="text-gray-900">{{ formatDate(user.created_at) }}</p>
        </div>
      </div>

      <!-- Usage Statistics -->
      <div class="mt-8">
        <h4 class="text-md font-semibold text-gray-800 mb-4">Usage Statistics</h4>
        
        <div v-if="stats" class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="bg-blue-50 rounded-lg p-4">
            <div class="flex items-center">
              <Search class="w-5 h-5 text-blue-600 mr-2" />
              <div>
                <p class="text-sm font-medium text-blue-900">Total Queries</p>
                <p class="text-lg font-bold text-blue-700">{{ stats.total_queries }}</p>
              </div>
            </div>
          </div>
          
          <div class="bg-green-50 rounded-lg p-4">
            <div class="flex items-center">
              <Zap class="w-5 h-5 text-green-600 mr-2" />
              <div>
                <p class="text-sm font-medium text-green-900">Tokens Used</p>
                <p class="text-lg font-bold text-green-700">{{ stats.total_tokens }}</p>
              </div>
            </div>
          </div>
          
          <div class="bg-purple-50 rounded-lg p-4">
            <div class="flex items-center">
              <Clock class="w-5 h-5 text-purple-600 mr-2" />
              <div>
                <p class="text-sm font-medium text-purple-900">Last Query</p>
                <p class="text-sm font-bold text-purple-700">
                  {{ stats.last_query_at ? formatDate(stats.last_query_at) : 'Never' }}
                </p>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else-if="loading" class="flex justify-center py-4">
          <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        </div>
        
        <div v-else class="text-gray-500 text-center py-4">
          Failed to load usage statistics
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { LogOut, Search, Zap, Clock } from 'lucide-vue-next';
import { useAuth } from '@/composables/useAuth';
import type { TokenUsageStats } from '@/types/api';

const { user, logout, fetchUserStats, loading } = useAuth();

const stats = ref<TokenUsageStats | null>(null);

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

const loadStats = async () => {
  const userStats = await fetchUserStats();
  if (userStats) {
    stats.value = userStats;
  }
};

onMounted(() => {
  loadStats();
});
</script>
