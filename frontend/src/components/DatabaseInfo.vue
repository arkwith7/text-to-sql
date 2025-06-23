<template>
  <div class="space-y-6">
    <!-- Database Overview -->
    <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center">
          <div class="w-12 h-12 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center mr-4">
            <Database class="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 class="text-2xl font-bold text-gray-900">
              {{ currentConnection?.connection_name || '연결된 데이터베이스 없음' }}
            </h2>
            <p class="text-gray-600">
              {{ currentConnection ? `${currentConnection.db_type?.toUpperCase() || 'PostgreSQL'} 분석 대상 데이터베이스` : '데이터베이스 연결이 필요합니다' }}
            </p>
          </div>
        </div>
        <div class="flex space-x-2">
          <button 
            @click="refreshSchema" 
            :disabled="refreshing || !currentConnection"
            class="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {{ refreshing ? '새로고침 중...' : '새로고침' }}
          </button>
        </div>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-white bg-opacity-70 rounded-lg p-4 text-center">
          <div class="text-2xl font-bold text-blue-600">{{ schemaInfo?.table_count || '-' }}</div>
          <div class="text-sm text-gray-600">테이블 수</div>
        </div>
        <div class="bg-white bg-opacity-70 rounded-lg p-4 text-center">
          <div class="text-2xl font-bold text-green-600">{{ schemaInfo?.total_columns || '-' }}</div>
          <div class="text-sm text-gray-600">총 컬럼 수</div>
        </div>
        <div class="bg-white bg-opacity-70 rounded-lg p-4 text-center">
          <div class="text-2xl font-bold text-purple-600">
            {{ schemaInfo?.last_updated ? formatDate(schemaInfo.last_updated) : '-' }}
          </div>
          <div class="text-sm text-gray-600">마지막 업데이트</div>
        </div>
      </div>
    </div>

    <!-- Raw AI Documentation (for debugging) -->
    <div v-if="schemaInfo?.documentation && aiTables.length === 0" class="bg-white rounded-xl shadow-sm border border-yellow-200 overflow-hidden mb-6">
      <div class="px-6 py-4 bg-yellow-50 border-b border-yellow-200 flex items-center justify-between">
        <h3 class="text-lg font-semibold text-gray-900 flex items-center">
          <FileText class="w-5 h-5 mr-2" />
          📋 원본 AI 문서 (파싱 실패시 표시)
        </h3>
        <button @click="documentationExpanded = !documentationExpanded" class="text-gray-400 hover:text-gray-600 transition-colors">
          <ChevronDown class="w-5 h-5 transition-transform duration-200" :class="{ 'transform rotate-180': documentationExpanded }" />
        </button>
      </div>
      <div v-if="documentationExpanded" class="p-6">
        <div class="prose prose-sm max-w-none" v-html="formatDocumentation(schemaInfo.documentation)"></div>
      </div>
    </div>

    <!-- AI Enhanced Tables Information -->
    <div v-if="aiTables.length > 0" class="grid grid-cols-1 gap-6">
      <div
        v-for="table in aiTables"
        :key="table.name"
        class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
      >
        <!-- Table Header -->
        <div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <div class="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mr-3">
                <Table class="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 class="text-lg font-semibold text-gray-900">
                  {{ table.displayName || `${table.koreanName} (${table.name})` }}
                </h3>
                <p class="text-sm text-gray-600">{{ table.description }}</p>
                <div class="flex flex-wrap gap-1 mt-1">
                  <span 
                    v-for="keyword in (table.keywords || []).slice(0, 3)" 
                    :key="keyword"
                    class="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full"
                  >
                    {{ keyword }}
                  </span>
                </div>
              </div>
            </div>
            <button
              @click="toggleTable(table.name)"
              class="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <ChevronDown 
                class="w-5 h-5 transition-transform duration-200"
                :class="{ 'transform rotate-180': expandedTables.includes(table.name) }"
              />
            </button>
          </div>
        </div>

        <!-- Table Content (Expandable) -->
        <div v-if="expandedTables.includes(table.name)" class="p-6">
          <!-- Schema Information with Korean Names -->
          <div class="mb-6">
            <h4 class="text-md font-medium text-gray-900 mb-3 flex items-center">
              <Table class="w-4 h-4 mr-2" />
              컬럼 정보 (한국어 매핑)
            </h4>
            <div class="bg-gray-50 rounded-lg p-4">
              <div class="grid gap-3">
                <div
                  v-for="column in table.columns"
                  :key="column.name"
                  class="bg-white rounded-lg p-4 border border-gray-200 hover:border-blue-300 transition-colors"
                >
                  <div class="flex items-start justify-between">
                    <div class="flex-1">
                      <div class="flex items-center mb-2">
                        <span class="font-mono text-sm text-blue-600 mr-3">{{ column.name }}</span>
                        <span class="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">{{ column.type }}</span>
                      </div>
                      <div class="text-sm font-medium text-gray-900 mb-1">
                        🏷️ {{ column.koreanName || column.name }}
                      </div>
                      <div class="text-xs text-gray-600 mb-2">{{ column.description }}</div>
                      <div class="flex flex-wrap gap-1">
                        <span 
                          v-for="keyword in (column.keywords || [])" 
                          :key="keyword"
                          class="text-xs bg-green-100 text-green-700 px-2 py-1 rounded"
                        >
                          {{ keyword }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- SQL Mapping Examples -->
          <div class="mb-6" v-if="table.sqlMappings && table.sqlMappings.length > 0">
            <h4 class="text-md font-medium text-gray-900 mb-3 flex items-center">
              <MessageSquare class="w-4 h-4 mr-2" />
              SQL 질문 매핑
            </h4>
            <div class="space-y-3">
              <div
                v-for="mapping in table.sqlMappings"
                :key="mapping.koreanQuestion"
                class="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-4 border border-green-200"
              >
                <div class="flex items-start space-x-3">
                  <div class="flex-shrink-0 mt-1">
                    <div class="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                      <span class="text-white text-xs font-bold">Q</span>
                    </div>
                  </div>
                  <div class="flex-1">
                    <p class="font-medium text-gray-900 mb-1">{{ mapping.koreanQuestion }}</p>
                    <div class="text-xs bg-gray-800 text-green-400 px-3 py-2 rounded font-mono overflow-x-auto">
                      {{ mapping.sqlHint }}
                    </div>
                  </div>
                  <button
                    @click="copyToClipboard(mapping.koreanQuestion)"
                    class="flex-shrink-0 text-gray-400 hover:text-green-600 transition-colors"
                    title="질문 복사"
                  >
                    <Copy class="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Analysis Examples -->
          <div v-if="table.examples && table.examples.length > 0">
            <h4 class="text-md font-medium text-gray-900 mb-3 flex items-center">
              <Lightbulb class="w-4 h-4 mr-2" />
              분석 예시
            </h4>
            <div class="space-y-2">
              <div
                v-for="example in table.examples"
                :key="example.question"
                class="bg-blue-50 rounded-lg p-3 border border-blue-200"
              >
                <p class="font-medium text-gray-900 text-sm">{{ example.question }}</p>
                <p class="text-xs text-gray-600 mt-1">{{ example.purpose }}</p>
              </div>
            </div>
          </div>

          <!-- Table Relations -->
          <div v-if="table.relation && table.relation !== '자동 분석 불가'" class="mt-6">
            <h4 class="text-md font-medium text-gray-900 mb-3 flex items-center">
              <Database class="w-4 h-4 mr-2" />
              테이블 관계
            </h4>
            <div class="bg-purple-50 rounded-lg p-3 border border-purple-200">
              <p class="text-sm text-gray-700">{{ table.relation }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Dynamic Tables Information (Fallback for non-AI docs) -->
    <div v-else-if="schemaInfo?.tables" class="grid grid-cols-1 gap-6">
      <div
        v-for="table in schemaInfo.tables"
        :key="table.table_name"
        class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
      >
        <!-- Table Header -->
        <div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <div class="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center mr-3">
                <Table class="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 class="text-lg font-semibold text-gray-900">{{ table.table_name }}</h3>
                <p class="text-sm text-gray-600">{{ table.column_count }}개 컬럼</p>
              </div>
            </div>
            <button
              @click="toggleTable(table.table_name)"
              class="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <ChevronDown 
                class="w-5 h-5 transition-transform duration-200"
                :class="{ 'transform rotate-180': expandedTables.includes(table.table_name) }"
              />
            </button>
          </div>
        </div>

        <!-- Table Content (Expandable) -->
        <div v-if="expandedTables.includes(table.table_name)" class="p-6">
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="grid gap-2">
              <div
                v-for="column in table.columns"
                :key="column.column_name"
                class="flex items-center justify-between py-2 px-3 bg-white rounded border"
              >
                <div class="flex items-center">
                  <span class="font-mono text-sm text-blue-600 mr-3">{{ column.column_name }}</span>
                  <span class="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">{{ column.data_type }}</span>
                  <span v-if="!column.is_nullable" class="text-xs bg-red-100 text-red-600 px-2 py-1 rounded ml-2">NOT NULL</span>
                </div>
                <span v-if="column.column_default" class="text-xs text-gray-500">기본값: {{ column.column_default }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Fallback: Static Tables Information -->
    <div v-else class="grid grid-cols-1 gap-6">
      <div
        v-for="table in fallbackTableInfo"
        :key="table.name"
        class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
      >
        <!-- Table Header -->
        <div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <div 
                class="w-10 h-10 rounded-lg flex items-center justify-center mr-3"
                :class="table.color"
              >
                <component :is="table.icon" class="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 class="text-lg font-semibold text-gray-900">{{ table.displayName }}</h3>
                <p class="text-sm text-gray-600">{{ table.description }} • {{ table.rowCount }}개 레코드</p>
              </div>
            </div>
            <button
              @click="toggleTable(table.name)"
              class="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <ChevronDown 
                class="w-5 h-5 transition-transform duration-200"
                :class="{ 'transform rotate-180': expandedTables.includes(table.name) }"
              />
            </button>
          </div>
        </div>

        <!-- Table Content (Expandable) -->
        <div v-if="expandedTables.includes(table.name)" class="p-6">
          <!-- Schema Information -->
          <div class="mb-6">
            <h4 class="text-md font-medium text-gray-900 mb-3 flex items-center">
              <Table class="w-4 h-4 mr-2" />
              스키마 정보
            </h4>
            <div class="bg-gray-50 rounded-lg p-4">
              <div class="grid gap-2">
                <div
                  v-for="column in table.columns"
                  :key="column.name"
                  class="flex items-center justify-between py-2 px-3 bg-white rounded border"
                >
                  <div class="flex items-center">
                    <span class="font-mono text-sm text-blue-600 mr-3">{{ column.name }}</span>
                    <span class="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">{{ column.type }}</span>
                  </div>
                  <span class="text-xs text-gray-500">{{ column.description }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Sample Data -->
          <div class="mb-6" v-if="table.sampleData">
            <h4 class="text-md font-medium text-gray-900 mb-3 flex items-center">
              <FileText class="w-4 h-4 mr-2" />
              샘플 데이터
            </h4>
            <div class="bg-blue-50 rounded-lg p-4">
              <p class="text-sm text-gray-700">{{ table.sampleData }}</p>
            </div>
          </div>

          <!-- Business Analysis Examples -->
          <div>
            <h4 class="text-md font-medium text-gray-900 mb-3 flex items-center">
              <MessageSquare class="w-4 h-4 mr-2" />
              분석 질문 예시
            </h4>
            <div class="space-y-2">
              <div
                v-for="example in table.examples"
                :key="example.question"
                class="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-4 border border-green-200"
              >
                <div class="flex items-start space-x-3">
                  <div class="flex-shrink-0 mt-1">
                    <div class="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                      <span class="text-white text-xs font-bold">Q</span>
                    </div>
                  </div>
                  <div class="flex-1">
                    <p class="font-medium text-gray-900 mb-1">{{ example.question }}</p>
                    <p class="text-sm text-gray-600 mb-2">{{ example.purpose }}</p>
                    <div class="text-xs bg-white bg-opacity-70 text-gray-600 px-2 py-1 rounded font-mono">
                      {{ example.hint }}
                    </div>
                  </div>
                  <button
                    @click="copyToClipboard(example.question)"
                    class="flex-shrink-0 text-gray-400 hover:text-green-600 transition-colors"
                    title="질문 복사"
                  >
                    <Copy class="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Analytics Guide -->
    <div class="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6 border border-purple-200">
      <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <Lightbulb class="w-5 h-5 mr-2 text-purple-600" />
        빠른 분석 가이드
      </h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="space-y-3">
          <h4 class="font-medium text-gray-800">📊 매출 분석</h4>
          <ul class="text-sm text-gray-600 space-y-1">
            <li>• "카테고리별 매출을 보여줘"</li>
            <li>• "가장 수익성이 높은 제품은?"</li>
            <li>• "국가별 매출 순위를 알려줘"</li>
          </ul>
        </div>
        <div class="space-y-3">
          <h4 class="font-medium text-gray-800">👥 고객 분석</h4>
          <ul class="text-sm text-gray-600 space-y-1">
            <li>• "주문이 많은 고객 상위 10명"</li>
            <li>• "국가별 고객 수를 알려줘"</li>
            <li>• "고객별 평균 주문 금액은?"</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { 
  Database, 
  Table, 
  FileText, 
  MessageSquare, 
  Copy, 
  ChevronDown, 
  Lightbulb,
  Users,
  Package,
  ShoppingCart,
  Tag,
  UserCheck,
  Truck,
  Building,
  ClipboardList
} from 'lucide-vue-next';
import { useConnections } from '@/composables/useConnections';
import { useAuth } from '@/composables/useAuth';

// Composables
const { connections, selectedConnectionId, selectedConnection } = useConnections();
const { api } = useAuth();

// State
const expandedTables = ref<string[]>(['customers', 'products']); // 기본으로 고객과 제품 테이블 확장
const schemaInfo = ref<any>(null);
const refreshing = ref(false);
const documentationExpanded = ref(true);

// Computed
const currentConnection = computed(() => {
  return connections.value.find(conn => conn.id === selectedConnectionId.value);
});

// 날짜 포맷팅 함수
const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('ko-KR', { 
    month: 'short', 
    day: 'numeric'
  });
};

// 스키마 정보 새로고침
const refreshSchema = async () => {
  if (!selectedConnectionId.value) return;
  
  refreshing.value = true;
  try {
    const response = await api.get(`/api/v1/schema/${selectedConnectionId.value}?force_refresh=true`);
    if (response.data.success) {
      schemaInfo.value = response.data.data;
      console.log('스키마 정보 새로고침 완료:', response.data.data);
    }
  } catch (error) {
    console.error('스키마 새로고침 실패:', error);
  } finally {
    refreshing.value = false;
  }
};

// 스키마 정보 로드
const loadSchemaInfo = async () => {
  if (!selectedConnectionId.value) return;
  
  try {
    const response = await api.get(`/api/v1/schema/${selectedConnectionId.value}`);
    if (response.data.success) {
      schemaInfo.value = response.data.data;
      console.log('스키마 정보 로드 완료:', response.data.data);
    }
  } catch (error) {
    console.error('스키마 정보 로드 실패:', error);
  }
};

// 연결 변경 감지
watch(selectedConnectionId, (newConnectionId) => {
  if (newConnectionId) {
    schemaInfo.value = null; // 기존 스키마 정보 초기화
    loadSchemaInfo();
  } else {
    schemaInfo.value = null;
  }
});

// AI 문서에서 JSON 블록들을 파싱하는 함수
const parseAIDocumentation = (documentation: string) => {
  const jsonBlocks = [];
  const regex = /```jsonc\n([\s\S]*?)\n```/g;
  let match;
  
  while ((match = regex.exec(documentation)) !== null) {
    try {
      const jsonString = match[1];
      const jsonData = JSON.parse(jsonString);
      jsonBlocks.push(jsonData);
    } catch (e) {
      console.warn('JSON 파싱 실패:', e);
    }
  }
  
  return jsonBlocks;
};

// 문서화 포맷팅 함수
const formatDocumentation = (markdown: string) => {
  // 간단한 마크다운 -> HTML 변환
  return markdown
    .replace(/## (.*)/g, '<h2 class="text-xl font-bold mt-6 mb-3 text-gray-800">$1</h2>')
    .replace(/### (.*)/g, '<h3 class="text-lg font-semibold mt-4 mb-2 text-gray-700">$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>')
    .replace(/- (.*)/g, '<li class="ml-4 list-disc">$1</li>')
    .replace(/\n\n/g, '<br/><br/>');
};

// AI 문서에서 파싱된 테이블 정보
const aiTables = computed(() => {
  if (!schemaInfo.value?.documentation) return [];
  return parseAIDocumentation(schemaInfo.value.documentation);
});

// 컴포넌트 마운트 시 스키마 정보 로드
onMounted(() => {
  if (selectedConnectionId.value) {
    loadSchemaInfo();
  }
});

// Fallback 테이블 정보 (기존 하드코딩된 데이터)
const fallbackTableInfo = [
  {
    name: 'customers',
    displayName: '👥 고객 (Customers)',
    description: '고객회사 및 담당자 정보',
    rowCount: 91,
    color: 'bg-blue-500',
    icon: Users,
    columns: [
      { name: 'customerid', type: 'INTEGER PRIMARY KEY', description: '고객 ID (자동 증가)' },
      { name: 'customername', type: 'VARCHAR(50)', description: '고객회사명' },
      { name: 'contactname', type: 'VARCHAR(50)', description: '담당자명' },
      { name: 'address', type: 'VARCHAR(50)', description: '주소' },
      { name: 'city', type: 'VARCHAR(20)', description: '도시' },
      { name: 'postalcode', type: 'VARCHAR(10)', description: '우편번호' },
      { name: 'country', type: 'VARCHAR(15)', description: '국가' }
    ],
    sampleData: '미국(13개), 독일(11개), 프랑스(11개), 브라질(9개), 영국(7개) 등 21개국 91개 고객사',
    examples: [
      {
        question: '국가별 고객 수를 알려줘',
        purpose: '지역별 시장 분포 및 확장 전략 수립',
        hint: 'GROUP BY country 사용'
      },
      {
        question: '독일에 있는 고객들을 보여줘',
        purpose: '특정 지역 고객 세분화 분석',
        hint: 'WHERE country = \'Germany\' 조건'
      }
    ]
  },
  {
    name: 'products',
    displayName: '📦 제품 (Products)',
    description: '상품 카탈로그 및 가격 정보',
    rowCount: 77,
    color: 'bg-green-500',
    icon: Package,
    columns: [
      { name: 'productid', type: 'INTEGER PRIMARY KEY', description: '제품 ID (자동 증가)' },
      { name: 'productname', type: 'VARCHAR(50)', description: '제품명' },
      { name: 'supplierid', type: 'INTEGER', description: '공급업체 ID (FK)' },
      { name: 'categoryid', type: 'INTEGER', description: '카테고리 ID (FK)' },
      { name: 'unit', type: 'VARCHAR(25)', description: '단위' },
      { name: 'price', type: 'NUMERIC(10,2)', description: '단가' }
    ],
    sampleData: 'Chai ($18.00), Chang ($19.00), Aniseed Syrup ($10.00), Chef Anton\'s Cajun Seasoning ($22.00) 등',
    examples: [
      {
        question: '가장 비싼 제품 5개는?',
        purpose: '프리미엄 제품 라인업 분석',
        hint: 'ORDER BY price DESC LIMIT 5'
      },
      {
        question: '카테고리별 평균 가격을 보여줘',
        purpose: '제품군별 가격 정책 분석',
        hint: 'JOIN categories, GROUP BY categoryname'
      }
    ]
  },
  {
    name: 'orders',
    displayName: '🛒 주문 (Orders)',
    description: '고객 주문 정보 및 배송 데이터',
    rowCount: 196,
    color: 'bg-purple-500',
    icon: ShoppingCart,
    columns: [
      { name: 'orderid', type: 'INTEGER PRIMARY KEY', description: '주문 ID (자동 증가)' },
      { name: 'customerid', type: 'INTEGER', description: '고객 ID (FK)' },
      { name: 'employeeid', type: 'INTEGER', description: '직원 ID (FK)' },
      { name: 'orderdate', type: 'TIMESTAMP', description: '주문 날짜' },
      { name: 'shipperid', type: 'INTEGER', description: '배송업체 ID (FK)' }
    ],
    sampleData: '1996년 7월부터 1998년 5월까지의 주문 데이터, 196건의 주문',
    examples: [
      {
        question: '월별 주문 수를 보여줘',
        purpose: '계절성 및 트렌드 분석',
        hint: 'EXTRACT(MONTH FROM orderdate) 사용'
      },
      {
        question: '가장 많은 주문을 받은 직원은?',
        purpose: '영업사원 성과 평가',
        hint: 'JOIN employees, GROUP BY employeeid'
      }
    ]
  },
  {
    name: 'orderdetails',
    displayName: '📋 주문상세 (OrderDetails)',
    description: '주문 항목별 상세 정보',
    rowCount: 518,
    color: 'bg-yellow-500',
    icon: ClipboardList,
    columns: [
      { name: 'orderdetailid', type: 'INTEGER PRIMARY KEY', description: '주문상세 ID (자동 증가)' },
      { name: 'orderid', type: 'INTEGER', description: '주문 ID (FK)' },
      { name: 'productid', type: 'INTEGER', description: '제품 ID (FK)' },
      { name: 'quantity', type: 'INTEGER', description: '주문 수량' }
    ],
    sampleData: '각 주문별 구매 제품과 수량 정보, 평균 주문당 2.6개 항목',
    examples: [
      {
        question: '가장 많이 팔린 제품 10개는?',
        purpose: '인기 상품 및 재고 관리 전략',
        hint: 'SUM(quantity), GROUP BY productid'
      },
      {
        question: '카테고리별 총 판매량을 알려줘',
        purpose: '제품군별 판매 성과 분석',
        hint: 'JOIN products, categories, SUM(quantity)'
      }
    ]
  },
  {
    name: 'categories',
    displayName: '🏷️ 카테고리 (Categories)',
    description: '제품 분류 정보',
    rowCount: 8,
    color: 'bg-red-500',
    icon: Tag,
    columns: [
      { name: 'categoryid', type: 'INTEGER PRIMARY KEY', description: '카테고리 ID (자동 증가)' },
      { name: 'categoryname', type: 'VARCHAR(25)', description: '카테고리 이름' },
      { name: 'description', type: 'VARCHAR(255)', description: '카테고리 설명' }
    ],
    sampleData: '음료, 조미료, 과자류, 유제품, 곡물/시리얼, 육류/가금류, 농산물, 해산물',
    examples: [
      {
        question: '카테고리별 제품 수를 보여줘',
        purpose: '제품 포트폴리오 분석',
        hint: 'JOIN products, COUNT(*)'
      },
      {
        question: '가장 수익성이 높은 카테고리는?',
        purpose: '카테고리별 수익성 비교',
        hint: 'JOIN products, orderdetails, SUM(price * quantity)'
      }
    ]
  },
  {
    name: 'employees',
    displayName: '👨‍💼 직원 (Employees)',
    description: '영업 담당 직원 정보',
    rowCount: 10,
    color: 'bg-indigo-500',
    icon: UserCheck,
    columns: [
      { name: 'employeeid', type: 'INTEGER PRIMARY KEY', description: '직원 ID (자동 증가)' },
      { name: 'lastname', type: 'VARCHAR(15)', description: '성' },
      { name: 'firstname', type: 'VARCHAR(15)', description: '이름' },
      { name: 'birthdate', type: 'TIMESTAMP', description: '생년월일' },
      { name: 'photo', type: 'VARCHAR(25)', description: '사진 파일명' },
      { name: 'notes', type: 'VARCHAR(1024)', description: '직원 설명' }
    ],
    sampleData: 'Nancy Davolio, Andrew Fuller, Janet Leverling 등 10명의 영업 담당자',
    examples: [
      {
        question: '직원별 담당 주문 수를 알려줘',
        purpose: '영업사원 성과 평가',
        hint: 'JOIN orders, COUNT(*)'
      },
      {
        question: '가장 젊은 직원은 누구인가?',
        purpose: '인사 관리 및 연령 분석',
        hint: 'ORDER BY birthdate DESC'
      }
    ]
  },
  {
    name: 'suppliers',
    displayName: '🏢 공급업체 (Suppliers)',
    description: '제품 공급업체 정보',
    rowCount: 29,
    color: 'bg-teal-500',
    icon: Building,
    columns: [
      { name: 'supplierid', type: 'INTEGER PRIMARY KEY', description: '공급업체 ID (자동 증가)' },
      { name: 'suppliername', type: 'VARCHAR(50)', description: '공급업체명' },
      { name: 'contactname', type: 'VARCHAR(50)', description: '담당자명' },
      { name: 'address', type: 'VARCHAR(50)', description: '주소' },
      { name: 'city', type: 'VARCHAR(20)', description: '도시' },
      { name: 'postalcode', type: 'VARCHAR(10)', description: '우편번호' },
      { name: 'country', type: 'VARCHAR(15)', description: '국가' },
      { name: 'phone', type: 'VARCHAR(15)', description: '전화번호' }
    ],
    sampleData: 'Exotic Liquids, New Orleans Cajun Delights, Grandma Kelly\'s Homestead 등 29개 공급업체',
    examples: [
      {
        question: '공급업체별 제품 수를 보여줘',
        purpose: '공급망 다양성 분석',
        hint: 'JOIN products, COUNT(*)'
      },
      {
        question: '미국에 있는 공급업체들은?',
        purpose: '지역별 공급업체 분석',
        hint: 'WHERE country = \'USA\''
      }
    ]
  },
  {
    name: 'shippers',
    displayName: '🚚 배송업체 (Shippers)',
    description: '물류 배송업체 정보',
    rowCount: 3,
    color: 'bg-orange-500',
    icon: Truck,
    columns: [
      { name: 'shipperid', type: 'INTEGER PRIMARY KEY', description: '배송업체 ID (자동 증가)' },
      { name: 'shippername', type: 'VARCHAR(25)', description: '배송업체명' },
      { name: 'phone', type: 'VARCHAR(15)', description: '전화번호' }
    ],
    sampleData: 'Speedy Express, United Package, Federal Shipping 3개 배송업체',
    examples: [
      {
        question: '배송업체별 처리한 주문 수는?',
        purpose: '물류 파트너 성과 분석',
        hint: 'JOIN orders, COUNT(*)'
      },
      {
        question: '가장 많이 이용되는 배송업체는?',
        purpose: '배송 업체 선호도 분석',
        hint: 'GROUP BY shipperid, ORDER BY COUNT(*) DESC'
      }
    ]
  }
];

const toggleTable = (tableName: string) => {
  const index = expandedTables.value.indexOf(tableName);
  if (index === -1) {
    expandedTables.value.push(tableName);
  } else {
    expandedTables.value.splice(index, 1);
  }
};

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text);
    // 복사 성공 알림을 표시할 수 있습니다
  } catch (err) {
    console.error('Failed to copy text: ', err);
  }
};
</script>
