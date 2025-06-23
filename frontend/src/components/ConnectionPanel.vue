<template>
  <transition name="slide">
    <div v-if="open" class="fixed inset-0 z-40 flex">
      <!-- Backdrop -->
      <div class="fixed inset-0 bg-gray-900 bg-opacity-50" @click="$emit('close')"></div>

      <!-- Panel -->
      <div class="relative ml-auto w-full max-w-md bg-white shadow-xl overflow-y-auto">
        <div class="p-4 border-b flex items-center justify-between">
          <h2 class="text-lg font-semibold">데이터베이스 연결</h2>
          <button @click="$emit('close')" class="text-gray-500 hover:text-gray-700">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Content -->
        <div class="p-4 space-y-6">
          <!-- Add Connection Form -->
          <div>
            <h3 class="text-md font-medium mb-2">새 연결 추가</h3>
            <form @submit.prevent="handleAdd" class="space-y-3">
              <input v-model="form.connection_name" placeholder="연결 이름" class="input" required />
              
              <!-- Database Type Selection -->
              <select v-model="form.db_type" class="input" required>
                <option value="postgresql">PostgreSQL ✅ 지원</option>
                <option value="mysql">MySQL (향후 지원 예정)</option>
                <option value="oracle">Oracle (향후 지원 예정)</option>
                <option value="sqlserver">MS SQL Server (향후 지원 예정)</option>
                <option value="mariadb">MariaDB (향후 지원 예정)</option>
              </select>
              
              <input v-model="form.db_host" placeholder="DB Host" class="input" required />
              <input v-model.number="form.db_port" placeholder="Port" class="input" required />
              <input v-model="form.db_user" placeholder="User" class="input" required />
              <input v-model="form.db_password" placeholder="Password" type="password" class="input" required />
              <input v-model="form.db_name" placeholder="Database Name" class="input" required />
              <button type="submit" class="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">추가</button>
            </form>
          </div>

          <!-- Connection List -->
          <div>
            <h3 class="text-md font-medium mb-2">내 연결</h3>
            <div v-if="connections.length === 0" class="text-sm text-gray-500">등록된 연결이 없습니다.</div>
            <ul class="divide-y" v-else>
              <li v-for="conn in connections" :key="conn.id" class="py-3">
                <div v-if="editingId !== conn.id" class="flex items-center justify-between">
                  <div class="flex-1">
                    <div class="flex items-center space-x-2">
                      <p class="font-medium">{{ conn.connection_name }}</p>
                      <!-- Connection Status Indicator -->
                      <div
                        class="w-2 h-2 rounded-full"
                        :class="{
                          'bg-green-500': conn.status === 'connected',
                          'bg-red-500': conn.status === 'error',
                          'bg-yellow-500': conn.status === 'testing',
                          'bg-gray-400': !conn.status || conn.status === 'disconnected'
                        }"
                        :title="getStatusText(conn)"
                      ></div>
                    </div>
                    <p class="text-xs text-gray-500">{{ conn.db_type || 'postgresql' }} - {{ conn.db_host }}:{{ conn.db_port }} / {{ conn.db_name }}</p>
                    <p v-if="conn.status === 'error' && conn.last_error" class="text-xs text-red-600 mt-1">
                      {{ conn.last_error }}
                    </p>
                  </div>
                  <div class="flex items-center space-x-2">
                    <button
                      @click="handleTestConnection(conn.id)"
                      :disabled="conn.status === 'testing'"
                      class="text-blue-500 hover:text-blue-700 disabled:opacity-50"
                      title="연결 테스트"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                      </svg>
                    </button>
                    <button
                      @click="handleSelectConnection(conn.id)"
                      :class="selectedConnectionId === conn.id ? 'text-green-600' : 'text-gray-500 hover:text-gray-700'"
                      title="선택"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                      </svg>
                    </button>
                    <button @click="startEdit(conn)" class="text-blue-500 hover:text-blue-700" title="수정">
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                    <button @click="remove(conn.id)" class="text-red-500 hover:text-red-700" title="삭제">
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
                
                <!-- Edit Form -->
                <div v-else class="space-y-3">
                  <input v-model="editForm.connection_name" placeholder="연결 이름" class="input" required />
                  
                  <!-- Database Type Selection for Edit -->
                  <select v-model="editForm.db_type" class="input" required>
                    <option value="postgresql">PostgreSQL ✅ 지원</option>
                    <option value="mysql">MySQL (향후 지원 예정)</option>
                    <option value="oracle">Oracle (향후 지원 예정)</option>
                    <option value="sqlserver">MS SQL Server (향후 지원 예정)</option>
                    <option value="mariadb">MariaDB (향후 지원 예정)</option>
                  </select>
                  
                  <input v-model="editForm.db_host" placeholder="DB Host" class="input" required />
                  <input v-model.number="editForm.db_port" placeholder="Port" class="input" required />
                  <input v-model="editForm.db_user" placeholder="User" class="input" required />
                  <input v-model="editForm.db_password" placeholder="Password" type="password" class="input" />
                  <input v-model="editForm.db_name" placeholder="Database Name" class="input" required />
                  <div class="flex space-x-2">
                    <button @click="handleUpdate()" class="flex-1 px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm">저장</button>
                    <button @click="cancelEdit()" class="flex-1 px-3 py-1 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 text-sm">취소</button>
                  </div>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue';
import { useConnections } from '@/composables/useConnections';

interface Props {
  open: boolean;
}

defineProps<Props>();

const emit = defineEmits(['close']);

const {
  connections,
  selectedConnectionId,
  addConnection,
  removeConnection,
  selectConnection,
  modifyConnection,
  testConnection,
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

// Edit form state
const editingId = ref<string | null>(null);
const editForm = reactive({
  connection_name: '',
  db_type: 'postgresql',
  db_host: '',
  db_port: 5432,
  db_user: '',
  db_password: '',
  db_name: '',
});

// Watch for database type changes to update default port
watch(() => form.db_type, (newType) => {
  const defaultPorts = {
    postgresql: 5432,
    mysql: 3306,
    mariadb: 3306,
    oracle: 1521,
    sqlserver: 1433
  };
  form.db_port = defaultPorts[newType as keyof typeof defaultPorts] || 5432;
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
  try {
    await addConnection({ ...form });
    resetForm();
  } catch (error) {
    console.error('연결 추가 실패:', error);
    alert('연결 추가에 실패했습니다.');
  }
};

const remove = async (id: string) => {
  if (confirm('정말 삭제하시겠습니까?')) {
    await removeConnection(id);
  }
};

const handleSelectConnection = (id: string) => {
  selectConnection(id);
  // 선택 후 작은 지연 후 패널 닫기 (사용자가 선택 상태를 볼 수 있도록)
  setTimeout(() => {
    emit('close');
  }, 500);
};

const startEdit = (connection: any) => {
  editingId.value = connection.id;
  editForm.connection_name = connection.connection_name;
  editForm.db_type = connection.db_type || 'postgresql';
  editForm.db_host = connection.db_host;
  editForm.db_port = connection.db_port;
  editForm.db_user = connection.db_user;
  editForm.db_password = ''; // 보안상 비밀번호는 비워둠
  editForm.db_name = connection.db_name;
};

const cancelEdit = () => {
  editingId.value = null;
  // 편집 폼 초기화
  editForm.connection_name = '';
  editForm.db_host = '';
  editForm.db_port = 5432;
  editForm.db_user = '';
  editForm.db_password = '';
  editForm.db_name = '';
};

const handleUpdate = async () => {
  if (!editingId.value) return;
  
  try {
    await modifyConnection(editingId.value, { ...editForm });
    editingId.value = null;
  } catch (error) {
    console.error('연결 수정 실패:', error);
    alert('연결 수정에 실패했습니다.');
  }
};

const handleTestConnection = async (connectionId: string) => {
  const success = await testConnection(connectionId);
  if (success) {
    console.log('연결 테스트 성공');
  } else {
    console.log('연결 테스트 실패');
  }
};

const getStatusText = (conn: any) => {
  switch (conn.status) {
    case 'connected':
      return '연결됨';
    case 'error':
      return `연결 오류: ${conn.last_error || '알 수 없는 오류'}`;
    case 'testing':
      return '연결 테스트 중...';
    default:
      return '연결 상태 확인 안함';
  }
};
</script>

<style scoped>
.slide-enter-from {
  transform: translateX(100%);
}
.slide-enter-active {
  transition: transform 0.3s ease;
}
.slide-leave-to {
  transform: translateX(100%);
}
.slide-leave-active {
  transition: transform 0.3s ease;
}
.input {
  @apply border border-gray-300 rounded px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-400;
}
</style> 