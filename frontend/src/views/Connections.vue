<template>
  <div class="p-6 space-y-6">
    <h1 class="text-2xl font-bold text-gray-900">데이터베이스 연결 관리</h1>

    <!-- Add Connection Form -->
    <div class="bg-white shadow rounded-lg p-4 border border-gray-200">
      <h2 class="text-lg font-semibold mb-4">새 연결 추가</h2>
      <form @submit.prevent="handleAdd">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input v-model="form.connection_name" placeholder="연결 이름" class="input" required />
          <input v-model="form.db_host" placeholder="DB Host" class="input" required />
          <input v-model.number="form.db_port" placeholder="Port" class="input" required />
          <input v-model="form.db_user" placeholder="User" class="input" required />
          <input v-model="form.db_password" placeholder="Password" type="password" class="input" required />
          <input v-model="form.db_name" placeholder="Database Name" class="input" required />
        </div>
        <button type="submit" class="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">추가</button>
      </form>
    </div>

    <!-- Connections List -->
    <div class="bg-white shadow rounded-lg p-4 border border-gray-200">
      <h2 class="text-lg font-semibold mb-4">내 연결</h2>
      <table class="min-w-full text-sm">
        <thead>
          <tr class="text-left text-gray-600">
            <th class="py-2">이름</th>
            <th class="py-2">호스트</th>
            <th class="py-2">DB</th>
            <th class="py-2">선택</th>
            <th class="py-2">삭제</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="conn in connections" :key="conn.id" class="border-t">
            <td class="py-2">{{ conn.connection_name }}</td>
            <td class="py-2">{{ conn.db_host }}:{{ conn.db_port }}</td>
            <td class="py-2">{{ conn.db_name }}</td>
            <td class="py-2">
              <button
                @click="selectConnection(conn.id)"
                :class="[
                  'px-3 py-1 rounded',
                  selectedConnectionId === conn.id ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                ]"
              >
                {{ selectedConnectionId === conn.id ? '선택됨' : '선택' }}
              </button>
            </td>
            <td class="py-2">
              <button @click="remove(conn.id)" class="text-red-500 hover:underline">삭제</button>
            </td>
          </tr>
          <tr v-if="connections.length === 0">
            <td colspan="5" class="py-4 text-center text-gray-500">등록된 연결이 없습니다.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue';
import { useConnections } from '@/composables/useConnections';

const {
  connections,
  selectedConnectionId,
  fetchConnections,
  addConnection,
  removeConnection,
  selectConnection,
} = useConnections();

const form = reactive({
  connection_name: '',
  db_type: 'postgresql',
  db_host: '',
  db_port: 5432,
  db_user: '',
  db_password: '',
  db_name: '',
});

const resetForm = () => {
  form.connection_name = '';
  form.db_host = '';
  form.db_port = 5432;
  form.db_user = '';
  form.db_password = '';
  form.db_name = '';
};

const handleAdd = async () => {
  await addConnection({ ...form });
  resetForm();
};

const remove = async (id: string) => {
  if (confirm('정말 삭제하시겠습니까?')) {
    await removeConnection(id);
  }
};

onMounted(fetchConnections);
</script>

<style scoped>
.input {
  @apply border border-gray-300 rounded px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-400;
}
</style> 