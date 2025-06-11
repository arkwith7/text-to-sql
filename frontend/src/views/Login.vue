<template>
  <AuthForm @success="handleAuthSuccess" />
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import AuthForm from '@/components/AuthForm.vue';

const router = useRouter();

const handleAuthSuccess = () => {
  router.push('/home');
};
</script>
