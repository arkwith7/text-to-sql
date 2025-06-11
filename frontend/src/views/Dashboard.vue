<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-6">
          <div class="flex items-center">
            <BarChart3 class="w-8 h-8 text-blue-600 mr-3" />
            <div>
              <h1 class="text-2xl font-bold text-gray-900">User Dashboard</h1>
              <p class="text-sm text-gray-600">Manage your profile and view usage statistics</p>
            </div>
          </div>
          <nav class="flex space-x-4">
            <router-link
              to="/"
              class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
            >
              Analytics
            </router-link>
            <router-link
              to="/dashboard"
              class="bg-blue-100 text-blue-700 px-3 py-2 rounded-md text-sm font-medium"
            >
              Dashboard
            </router-link>
          </nav>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <UserProfile />
    </main>
  </div>
</template>

<script setup lang="ts">
import { BarChart3 } from 'lucide-vue-next';
import UserProfile from '@/components/UserProfile.vue';
</script>
