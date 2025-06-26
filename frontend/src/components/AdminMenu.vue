<template>
  <nav v-if="isAdmin" class="admin-menu">
    <ul>
      <li><router-link to="/admin">관리자 대시보드</router-link></li>
      <li><router-link to="/admin/system-prompts">시스템 프롬프트 관리</router-link></li>
      <li><router-link to="/admin/db-connections">DB 접속정보 관리</router-link></li>
      <li><router-link to="/admin/schema-metadata">스키마 메타데이터 관리</router-link></li>
      <li><router-link to="/admin/users">사용자 및 권한 관리</router-link></li>
      <li><router-link to="/admin/llm-connections">LLM 접속정보 관리</router-link></li>
    </ul>
  </nav>
</template>

<script setup lang="ts">
import { useAuth } from '@/composables/useAuth';
import { computed } from 'vue';

const { user } = useAuth();
const isAdmin = computed(() => user.value?.role === 'admin');
</script>

<style scoped>
.admin-menu {
  background: #f8fafc;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}
.admin-menu ul {
  list-style: none;
  padding: 0;
}
.admin-menu li {
  margin-bottom: 0.5rem;
}
.admin-menu a {
  color: #2563eb;
  text-decoration: none;
  font-weight: 500;
}
.admin-menu a.router-link-exact-active {
  color: #1e293b;
  font-weight: bold;
}
</style>
