<template>
  <div class="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <div class="flex justify-center">
        <BarChart3 class="w-12 h-12 text-blue-600" />
      </div>
      <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
        {{ isLoginMode ? 'Sign in to your account' : 'Create your account' }}
      </h2>
      <p class="mt-2 text-center text-sm text-gray-600">
        {{ isLoginMode ? "Don't have an account?" : "Already have an account?" }}
        <button
          @click="toggleMode"
          class="font-medium text-blue-600 hover:text-blue-500"
        >
          {{ isLoginMode ? 'Sign up' : 'Sign in' }}
        </button>
      </p>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
      <div class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
        <form @submit.prevent="handleSubmit" class="space-y-6">
          <!-- Full Name (Register only) -->
          <div v-if="!isLoginMode">
            <label for="fullName" class="block text-sm font-medium text-gray-700">
              Full Name
            </label>
            <div class="mt-1">
              <input
                id="fullName"
                v-model="form.full_name"
                type="text"
                required
                class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter your full name"
              />
            </div>
          </div>

          <!-- Email -->
          <div>
            <label for="email" class="block text-sm font-medium text-gray-700">
              Email address
            </label>
            <div class="mt-1">
              <input
                id="email"
                v-model="form.email"
                type="email"
                required
                class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter your email"
              />
            </div>
          </div>

          <!-- Company (Register only) -->
          <div v-if="!isLoginMode">
            <label for="company" class="block text-sm font-medium text-gray-700">
              Company (Optional)
            </label>
            <div class="mt-1">
              <input
                id="company"
                v-model="form.company"
                type="text"
                class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter your company name"
              />
            </div>
          </div>

          <!-- Password -->
          <div>
            <label for="password" class="block text-sm font-medium text-gray-700">
              Password
            </label>
            <div class="mt-1">
              <input
                id="password"
                v-model="form.password"
                type="password"
                required
                class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter your password"
              />
            </div>
          </div>

          <!-- Error Message -->
          <div v-if="error" class="bg-red-50 border border-red-200 rounded-md p-4">
            <div class="flex">
              <AlertCircle class="w-5 h-5 text-red-400 mr-2" />
              <p class="text-sm text-red-700">{{ error }}</p>
            </div>
          </div>

          <!-- Submit Button -->
          <div>
            <button
              type="submit"
              :disabled="loading"
              class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div v-if="loading" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              {{ loading ? 'Processing...' : (isLoginMode ? 'Sign in' : 'Sign up') }}
            </button>
          </div>

          <!-- Demo Login Button (only show in login mode) -->
          <div v-if="isLoginMode" class="mt-4">
            <button
              type="button"
              @click="handleDemoLogin"
              :disabled="loading"
              class="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              데모 로그인
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { BarChart3, AlertCircle } from 'lucide-vue-next';
import { useAuth } from '@/composables/useAuth';
import { useLogin } from '@/composables/useLogin';
import { logger } from '@/utils/logger';
import type { UserCreate, UserLogin } from '@/types/api';

const emit = defineEmits<{
  success: [];
}>();

const { register, loading, error } = useAuth();
const { loginUser, loginDemo } = useLogin();

const isLoginMode = ref(true);

const form = reactive({
  email: '',
  password: '',
  full_name: '',
  company: '',
});

const toggleMode = () => {
  isLoginMode.value = !isLoginMode.value;
  // Reset form when switching modes
  Object.assign(form, {
    email: '',
    password: '',
    full_name: '',
    company: '',
  });
};

const handleSubmit = async () => {
  let success = false;

  if (isLoginMode.value) {
    success = await loginUser(form.email, form.password);
  } else {
    const registerData: UserCreate = {
      email: form.email,
      password: form.password,
      full_name: form.full_name,
      company: form.company || undefined,
    };
    success = await register(registerData);
  }

  if (success) {
    emit('success');
  }
};

const handleDemoLogin = async () => {
  logger.debug('데모 로그인 시작...');
  
  try {
    logger.api('데모 로그인 API 호출...');
    const success = await loginDemo();
    
    if (success) {
      logger.success('데모 로그인 성공');
      emit('success');
    } else {
      logger.error('데모 로그인 실패');
      logger.debug('Error details:', error.value);
      // useAuth에서 설정된 error를 사용
    }
  } catch (err) {
    logger.error('데모 로그인 예외 발생:', err);
  }
};
</script>
