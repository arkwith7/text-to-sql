<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useAuth } from './composables/useAuth';

const { initializeAuth } = useAuth();

onMounted(async () => {
  await initializeAuth();
});
</script>
