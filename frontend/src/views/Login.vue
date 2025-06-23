<template>
  <AuthForm @success="handleAuthSuccess" />
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useAuth } from '@/composables/useAuth';
import { logger } from '@/utils/logger';
import AuthForm from '@/components/AuthForm.vue';

const router = useRouter();

const handleAuthSuccess = () => {
  logger.success('Login success - about to navigate to /home');
  logger.debug('Auth state before navigation:', {
    isAuthenticated: useAuth().isAuthenticated.value,
    hasUser: !!useAuth().user.value,
    hasToken: !!useAuth().token.value
  });
  router.push('/home');
};
</script>
