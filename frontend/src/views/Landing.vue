<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
    <!-- Navigation Header -->
    <nav class="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center space-x-2">
            <div class="w-8 h-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
              </svg>
            </div>
            <span class="text-xl font-bold text-gray-900">Smart Analytics</span>
          </div>
          <div class="flex items-center space-x-4">
            <router-link 
              to="/login" 
              class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              시작하기
            </router-link>
          </div>
        </div>
      </div>
    </nav>

    <!-- Hero Section -->
    <section class="relative overflow-hidden">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        <div class="lg:grid lg:grid-cols-12 lg:gap-8 items-center">
          <div class="sm:text-center md:max-w-2xl md:mx-auto lg:col-span-6 lg:text-left">
            <h1 class="text-4xl tracking-tight font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
              <span class="block">AI가 바꾸는</span>
              <span class="block text-blue-600">비즈니스 분석</span>
            </h1>
            <p class="mt-3 text-base text-gray-500 sm:mt-5 sm:text-xl lg:text-lg xl:text-xl">
              복잡한 SQL 쿼리 작성 없이 자연어로 질문하면, AI Agent가 즉시 인사이트를 제공합니다. 
              Azure OpenAI 기반의 Text-to-SQL 기술로 비즈니스 의사결정을 가속화하세요.
            </p>
            <div class="mt-8 sm:max-w-lg sm:mx-auto sm:text-center lg:text-left lg:mx-0">
              <div class="flex flex-col sm:flex-row gap-4">
                <router-link 
                  to="/login"
                  class="flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 md:py-4 md:text-lg md:px-10 transition-all transform hover:scale-105"
                >
                  무료로 시작하기
                </router-link>
                <button 
                  @click="scrollToDemo" 
                  class="flex items-center justify-center px-8 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 md:py-4 md:text-lg md:px-10 transition-colors"
                >
                  데모 보기
                </button>
              </div>
            </div>
          </div>
          <div class="mt-12 relative sm:max-w-lg sm:mx-auto lg:mt-0 lg:max-w-none lg:mx-0 lg:col-span-6 lg:flex lg:items-center">
            <div class="relative mx-auto w-full rounded-lg shadow-lg lg:max-w-md">
              <div class="relative block w-full bg-white rounded-lg overflow-hidden border border-gray-200">
                <div class="px-6 py-4 border-b border-gray-200">
                  <div class="flex items-center space-x-2">
                    <div class="w-3 h-3 bg-red-500 rounded-full"></div>
                    <div class="w-3 h-3 bg-yellow-500 rounded-full"></div>
                    <div class="w-3 h-3 bg-green-500 rounded-full"></div>
                  </div>
                </div>
                <div class="p-6 space-y-4">
                  <div class="bg-blue-50 p-4 rounded-lg">
                    <p class="text-sm text-gray-600 mb-2">질문:</p>
                    <p class="font-medium text-gray-900">"지난 3개월간 가장 많이 팔린 제품 5개는?"</p>
                  </div>
                  <div class="bg-green-50 p-4 rounded-lg">
                    <p class="text-sm text-gray-600 mb-2">AI 응답:</p>
                    <div class="space-y-2">
                      <div class="bg-white p-3 rounded border">
                        <div class="flex justify-between">
                          <span class="text-sm font-medium">노트북 컴퓨터</span>
                          <span class="text-sm text-blue-600">1,245개</span>
                        </div>
                      </div>
                      <div class="bg-white p-3 rounded border">
                        <div class="flex justify-between">
                          <span class="text-sm font-medium">무선 마우스</span>
                          <span class="text-sm text-blue-600">987개</span>
                        </div>
                      </div>
                      <div class="text-xs text-gray-500">+ 3개 더...</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Business Value Section -->
    <section class="py-16 bg-gray-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center">
          <h2 class="text-3xl font-extrabold text-gray-900 sm:text-4xl">
            비즈니스 가치 극대화
          </h2>
          <p class="mt-4 max-w-2xl mx-auto text-xl text-gray-500">
            AI Agent 기반 Text-to-SQL 기술이 가져다주는 혁신적인 비즈니스 임팩트
          </p>
        </div>

        <div class="mt-16">
          <div class="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
            <!-- ROI Improvement -->
            <div class="relative group">
              <div class="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg blur opacity-25 group-hover:opacity-75 transition duration-1000 group-hover:duration-200"></div>
              <div class="relative p-6 bg-white ring-1 ring-gray-900/5 rounded-lg leading-none">
                <div class="flex items-center space-x-4">
                  <div class="flex-shrink-0">
                    <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                      <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                      </svg>
                    </div>
                  </div>
                  <div class="flex-1">
                    <h3 class="text-lg font-medium text-gray-900">ROI 300% 향상</h3>
                    <p class="mt-2 text-sm text-gray-500">
                      데이터 분석 시간을 90% 단축하여 의사결정 속도를 3배 가속화
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Cost Reduction -->
            <div class="relative group">
              <div class="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg blur opacity-25 group-hover:opacity-75 transition duration-1000 group-hover:duration-200"></div>
              <div class="relative p-6 bg-white ring-1 ring-gray-900/5 rounded-lg leading-none">
                <div class="flex items-center space-x-4">
                  <div class="flex-shrink-0">
                    <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                      <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
                      </svg>
                    </div>
                  </div>
                  <div class="flex-1">
                    <h3 class="text-lg font-medium text-gray-900">비용 절감 70%</h3>
                    <p class="mt-2 text-sm text-gray-500">
                      SQL 전문가 없이도 복잡한 데이터 분석이 가능하여 인력 비용 대폭 절감
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Productivity -->
            <div class="relative group">
              <div class="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg blur opacity-25 group-hover:opacity-75 transition duration-1000 group-hover:duration-200"></div>
              <div class="relative p-6 bg-white ring-1 ring-gray-900/5 rounded-lg leading-none">
                <div class="flex items-center space-x-4">
                  <div class="flex-shrink-0">
                    <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                      <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                      </svg>
                    </div>
                  </div>
                  <div class="flex-1">
                    <h3 class="text-lg font-medium text-gray-900">생산성 5배 증가</h3>
                    <p class="mt-2 text-sm text-gray-500">
                      자연어 질문으로 즉시 답변을 얻어 업무 효율성 극대화
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Sample Questions Section -->
    <section class="py-16 bg-indigo-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center">
          <h2 class="text-3xl font-extrabold text-gray-900 sm:text-4xl">
            이런 질문들을 자연어로 해보세요
          </h2>
          <p class="mt-4 max-w-2xl mx-auto text-xl text-gray-500">
            복잡한 SQL 없이 평소 말하듯이 질문하면 AI가 즉시 답변해드립니다
          </p>
        </div>

        <div class="mt-16 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
          <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
            <div class="flex items-start space-x-3">
              <div class="flex-shrink-0">
                <svg class="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-1l-4 4z"></path>
                </svg>
              </div>
              <div>
                <p class="text-gray-900 font-medium">"지난 3개월간 가장 많이 팔린 제품 5개는?"</p>
                <p class="mt-2 text-sm text-gray-500">매출 분석 및 인기 상품 파악</p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
            <div class="flex items-start space-x-3">
              <div class="flex-shrink-0">
                <svg class="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
                </svg>
              </div>
              <div>
                <p class="text-gray-900 font-medium">"부서별 평균 급여를 보여줘"</p>
                <p class="mt-2 text-sm text-gray-500">인사 데이터 분석 및 급여 비교</p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-purple-500">
            <div class="flex items-start space-x-3">
              <div class="flex-shrink-0">
                <svg class="w-6 h-6 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                </svg>
              </div>
              <div>
                <p class="text-gray-900 font-medium">"매월 매출 추이를 확인하고 싶어"</p>
                <p class="mt-2 text-sm text-gray-500">시계열 분석 및 트렌드 파악</p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-red-500">
            <div class="flex items-start space-x-3">
              <div class="flex-shrink-0">
                <svg class="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                </svg>
              </div>
              <div>
                <p class="text-gray-900 font-medium">"고객별 주문 횟수 상위 10명"</p>
                <p class="mt-2 text-sm text-gray-500">고객 세분화 및 VIP 고객 식별</p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-yellow-500">
            <div class="flex items-start space-x-3">
              <div class="flex-shrink-0">
                <svg class="w-6 h-6 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                </svg>
              </div>
              <div>
                <p class="text-gray-900 font-medium">"카테고리별 제품 수량"</p>
                <p class="mt-2 text-sm text-gray-500">재고 관리 및 카테고리 분석</p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-indigo-500">
            <div class="flex items-start space-x-3">
              <div class="flex-shrink-0">
                <svg class="w-6 h-6 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                </svg>
              </div>
              <div>
                <p class="text-gray-900 font-medium">"가장 수익성이 높은 제품은?"</p>
                <p class="mt-2 text-sm text-gray-500">수익성 분석 및 마진 최적화</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section id="demo" class="py-16 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center">
          <h2 class="text-3xl font-extrabold text-gray-900 sm:text-4xl">
            핵심 기능
          </h2>
          <p class="mt-4 max-w-2xl mx-auto text-xl text-gray-500">
            Azure OpenAI 기반 AI Agent가 제공하는 혁신적인 기능들
          </p>
        </div>

        <div class="mt-16">
          <div class="grid grid-cols-1 gap-12 lg:grid-cols-2">
            <!-- Natural Language Processing -->
            <div class="relative">
              <div class="relative">
                <h3 class="text-2xl font-bold text-gray-900">자연어 처리</h3>
                <p class="mt-3 text-lg text-gray-500">
                  복잡한 SQL 문법 없이 평소 말하는 방식으로 질문하면 AI가 정확한 쿼리를 생성합니다.
                </p>
                <div class="mt-6 space-y-4">
                  <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0">
                      <div class="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center">
                        <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                      </div>
                    </div>
                    <p class="text-gray-700">한국어 자연어 완벽 지원</p>
                  </div>
                  <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0">
                      <div class="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center">
                        <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                      </div>
                    </div>
                    <p class="text-gray-700">복잡한 비즈니스 로직 이해</p>
                  </div>
                  <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0">
                      <div class="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center">
                        <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                      </div>
                    </div>
                    <p class="text-gray-700">실시간 쿼리 최적화</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Real-time Visualization -->
            <div class="relative">
              <div class="relative">
                <h3 class="text-2xl font-bold text-gray-900">실시간 시각화</h3>
                <p class="mt-3 text-lg text-gray-500">
                  쿼리 결과를 자동으로 분석하여 최적의 차트와 그래프로 시각화합니다.
                </p>
                <div class="mt-6 space-y-4">
                  <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0">
                      <div class="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                        <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                        </svg>
                      </div>
                    </div>
                    <p class="text-gray-700">자동 차트 유형 선택</p>
                  </div>
                  <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0">
                      <div class="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                        <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                        </svg>
                      </div>
                    </div>
                    <p class="text-gray-700">대화형 대시보드</p>
                  </div>
                  <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0">
                      <div class="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                        <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
                        </svg>
                      </div>
                    </div>
                    <p class="text-gray-700">실시간 데이터 업데이트</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ROI and Impact Section -->
    <section class="py-16 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center">
          <h2 class="text-3xl font-extrabold text-gray-900 sm:text-4xl">
            입증된 비즈니스 성과
          </h2>
          <p class="mt-4 max-w-2xl mx-auto text-xl text-gray-500">
            실제 고객들이 경험한 AI Agent Text-to-SQL 솔루션의 임팩트
          </p>
        </div>

        <div class="mt-16">
          <div class="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
            <!-- Metric 1 -->
            <div class="text-center">
              <div class="flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mx-auto mb-4">
                <span class="text-2xl font-bold text-blue-600">90%</span>
              </div>
              <h3 class="text-lg font-medium text-gray-900">분석 시간 단축</h3>
              <p class="mt-2 text-sm text-gray-500">기존 2시간 → 12분으로 단축</p>
            </div>

            <!-- Metric 2 -->
            <div class="text-center">
              <div class="flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mx-auto mb-4">
                <span class="text-2xl font-bold text-green-600">300%</span>
              </div>
              <h3 class="text-lg font-medium text-gray-900">ROI 향상</h3>
              <p class="mt-2 text-sm text-gray-500">투자 대비 3배 수익 증대</p>
            </div>

            <!-- Metric 3 -->
            <div class="text-center">
              <div class="flex items-center justify-center w-16 h-16 bg-purple-100 rounded-full mx-auto mb-4">
                <span class="text-2xl font-bold text-purple-600">70%</span>
              </div>
              <h3 class="text-lg font-medium text-gray-900">비용 절감</h3>
              <p class="mt-2 text-sm text-gray-500">전문 인력 의존도 대폭 감소</p>
            </div>

            <!-- Metric 4 -->
            <div class="text-center">
              <div class="flex items-center justify-center w-16 h-16 bg-yellow-100 rounded-full mx-auto mb-4">
                <span class="text-2xl font-bold text-yellow-600">5배</span>
              </div>
              <h3 class="text-lg font-medium text-gray-900">생산성 증가</h3>
              <p class="mt-2 text-sm text-gray-500">일일 분석 처리량 대폭 향상</p>
            </div>
          </div>
        </div>

        <!-- Before vs After Comparison -->
        <div class="mt-20">
          <div class="grid grid-cols-1 gap-8 lg:grid-cols-2">
            <!-- Before -->
            <div class="relative">
              <div class="bg-red-50 border border-red-200 rounded-lg p-6">
                <div class="flex items-center mb-4">
                  <svg class="w-6 h-6 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                  </svg>
                  <h3 class="text-lg font-medium text-red-800">기존 방식의 문제점</h3>
                </div>
                <ul class="space-y-3 text-sm text-red-700">
                  <li class="flex items-start">
                    <span class="mr-2">❌</span>
                    <span>복잡한 SQL 문법 학습 필요</span>
                  </li>
                  <li class="flex items-start">
                    <span class="mr-2">❌</span>
                    <span>전문 인력에 의존적인 분석</span>
                  </li>
                  <li class="flex items-start">
                    <span class="mr-2">❌</span>
                    <span>분석 결과까지 평균 2-3시간 소요</span>
                  </li>
                  <li class="flex items-start">
                    <span class="mr-2">❌</span>
                    <span>실시간 의사결정 지원 불가</span>
                  </li>
                  <li class="flex items-start">
                    <span class="mr-2">❌</span>
                    <span>높은 인력 비용과 교육 비용</span>
                  </li>
                </ul>
              </div>
            </div>

            <!-- After -->
            <div class="relative">
              <div class="bg-green-50 border border-green-200 rounded-lg p-6">
                <div class="flex items-center mb-4">
                  <svg class="w-6 h-6 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  <h3 class="text-lg font-medium text-green-800">AI Agent 솔루션</h3>
                </div>
                <ul class="space-y-3 text-sm text-green-700">
                  <li class="flex items-start">
                    <span class="mr-2">✅</span>
                    <span>자연어로 간단한 질문만 입력</span>
                  </li>
                  <li class="flex items-start">
                    <span class="mr-2">✅</span>
                    <span>누구나 쉽게 데이터 분석 가능</span>
                  </li>
                  <li class="flex items-start">
                    <span class="mr-2">✅</span>
                    <span>즉시 결과 제공 (평균 30초)</span>
                  </li>
                  <li class="flex items-start">
                    <span class="mr-2">✅</span>
                    <span>실시간 비즈니스 인사이트</span>
                  </li>
                  <li class="flex items-start">
                    <span class="mr-2">✅</span>
                    <span>운영비용 70% 절감</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Technology Stack -->
    <section class="py-16 bg-gray-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center">
          <h2 class="text-3xl font-extrabold text-gray-900 sm:text-4xl">
            검증된 기술 스택
          </h2>
          <p class="mt-4 max-w-2xl mx-auto text-xl text-gray-500">
            엔터프라이즈급 안정성과 확장성을 보장하는 Microsoft Azure 기반 아키텍처
          </p>
        </div>

        <div class="mt-16">
          <div class="grid grid-cols-2 gap-8 md:grid-cols-4">
            <div class="col-span-1 flex justify-center items-center">
              <div class="text-center">
                <div class="w-16 h-16 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg class="w-8 h-8 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                  </svg>
                </div>
                <h3 class="text-lg font-medium text-gray-900">Azure OpenAI</h3>
                <p class="mt-2 text-sm text-gray-500">GPT-4o-mini</p>
              </div>
            </div>
            <div class="col-span-1 flex justify-center items-center">
              <div class="text-center">
                <div class="w-16 h-16 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg class="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                  </svg>
                </div>
                <h3 class="text-lg font-medium text-gray-900">Vue.js 3</h3>
                <p class="mt-2 text-sm text-gray-500">TypeScript</p>
              </div>
            </div>
            <div class="col-span-1 flex justify-center items-center">
              <div class="text-center">
                <div class="w-16 h-16 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg class="w-8 h-8 text-purple-600" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                  </svg>
                </div>
                <h3 class="text-lg font-medium text-gray-900">FastAPI</h3>
                <p class="mt-2 text-sm text-gray-500">Python</p>
              </div>
            </div>
            <div class="col-span-1 flex justify-center items-center">
              <div class="text-center">
                <div class="w-16 h-16 bg-indigo-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg class="w-8 h-8 text-indigo-600" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                  </svg>
                </div>
                <h3 class="text-lg font-medium text-gray-900">PostgreSQL</h3>
                <p class="mt-2 text-sm text-gray-500">Northwind DB</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Use Cases Section -->
    <section class="py-16 bg-gray-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center">
          <h2 class="text-3xl font-extrabold text-gray-900 sm:text-4xl">
            다양한 업계에서 활용 중
          </h2>
          <p class="mt-4 max-w-2xl mx-auto text-xl text-gray-500">
            업계를 막론하고 데이터 기반 의사결정이 필요한 모든 곳에서 사용됩니다
          </p>
        </div>

        <div class="mt-16">
          <div class="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
            <!-- E-commerce -->
            <div class="bg-white rounded-lg shadow-lg p-6">
              <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M8 11v6h8v-6M8 11h8"></path>
                </svg>
              </div>
              <h3 class="text-lg font-medium text-gray-900 mb-2">이커머스</h3>
              <p class="text-sm text-gray-500 mb-4">매출 분석, 상품 성과, 고객 세분화</p>
              <ul class="text-xs text-gray-600 space-y-1">
                <li>• 베스트셀러 제품 분석</li>
                <li>• 고객 구매 패턴 파악</li>
                <li>• 계절별 매출 트렌드</li>
              </ul>
            </div>

            <!-- Manufacturing -->
            <div class="bg-white rounded-lg shadow-lg p-6">
              <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                </svg>
              </div>
              <h3 class="text-lg font-medium text-gray-900 mb-2">제조업</h3>
              <p class="text-sm text-gray-500 mb-4">생산 효율성, 품질 관리, 재고 최적화</p>
              <ul class="text-xs text-gray-600 space-y-1">
                <li>• 생산라인 효율성 분석</li>
                <li>• 불량률 추적 관리</li>
                <li>• 재고 회전율 최적화</li>
              </ul>
            </div>

            <!-- Financial Services -->
            <div class="bg-white rounded-lg shadow-lg p-6">
              <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
                </svg>
              </div>
              <h3 class="text-lg font-medium text-gray-900 mb-2">금융서비스</h3>
              <p class="text-sm text-gray-500 mb-4">리스크 분석, 고객 포트폴리오, 수익성</p>
              <ul class="text-xs text-gray-600 space-y-1">
                <li>• 고객 신용도 평가</li>
                <li>• 포트폴리오 성과 분석</li>
                <li>• 리스크 모니터링</li>
              </ul>
            </div>

            <!-- Healthcare -->
            <div class="bg-white rounded-lg shadow-lg p-6">
              <div class="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center mb-4">
                <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                </svg>
              </div>
              <h3 class="text-lg font-medium text-gray-900 mb-2">헬스케어</h3>
              <p class="text-sm text-gray-500 mb-4">환자 데이터, 치료 효과, 운영 효율성</p>
              <ul class="text-xs text-gray-600 space-y-1">
                <li>• 환자 치료 결과 분석</li>
                <li>• 병원 운영 효율성</li>
                <li>• 의료 비용 최적화</li>
              </ul>
            </div>

            <!-- Retail -->
            <div class="bg-white rounded-lg shadow-lg p-6">
              <div class="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mb-4">
                <svg class="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
                </svg>
              </div>
              <h3 class="text-lg font-medium text-gray-900 mb-2">리테일</h3>
              <p class="text-sm text-gray-500 mb-4">매장 성과, 고객 행동, 재고 관리</p>
              <ul class="text-xs text-gray-600 space-y-1">
                <li>• 매장별 매출 비교</li>
                <li>• 고객 방문 패턴</li>
                <li>• 상품 진열 최적화</li>
              </ul>
            </div>

            <!-- Education -->
            <div class="bg-white rounded-lg shadow-lg p-6">
              <div class="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
                <svg class="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                </svg>
              </div>
              <h3 class="text-lg font-medium text-gray-900 mb-2">교육</h3>
              <p class="text-sm text-gray-500 mb-4">학습 성과, 학생 분석, 운영 효율성</p>
              <ul class="text-xs text-gray-600 space-y-1">
                <li>• 학습 성과 추적</li>
                <li>• 학생 참여도 분석</li>
                <li>• 교육 프로그램 효과</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="relative bg-gradient-to-r from-blue-600 to-indigo-700">
      <div class="absolute inset-0">
        <div class="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-700 mix-blend-multiply"></div>
      </div>
      <div class="relative max-w-7xl mx-auto py-24 px-4 sm:px-6 lg:px-8">
        <div class="text-center">
          <h2 class="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            <span class="block">지금 바로 시작하세요</span>
            <span class="block">미래의 비즈니스 분석을 경험해보세요</span>
          </h2>
          <p class="mt-4 text-lg leading-6 text-blue-200">
            5분 만에 설정 완료. 복잡한 설치 과정 없이 즉시 사용 가능합니다.
          </p>
          <div class="mt-8">
            <div class="inline-flex rounded-md shadow">
              <router-link 
                to="/login"
                class="inline-flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-blue-600 bg-white hover:bg-blue-50 md:py-4 md:text-lg md:px-10 transition-colors"
              >
                무료 체험 시작하기
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="bg-white">
      <div class="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div class="border-t border-gray-200 pt-8">
          <p class="text-base text-gray-400 xl:text-center">
            &copy; 2025 Smart Business Analytics Assistant. AI Agent 기반 Text-to-SQL 솔루션.
          </p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';

const scrollToDemo = () => {
  const element = document.getElementById('demo');
  if (element) {
    element.scrollIntoView({ behavior: 'smooth' });
  }
};

// Add smooth scrolling behavior
onMounted(() => {
  // Intersection Observer for animations
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-fade-in');
      }
    });
  }, observerOptions);

  // Observe elements for animation
  const elementsToAnimate = document.querySelectorAll('.relative.group, .grid > div');
  elementsToAnimate.forEach((el) => observer.observe(el));
});
</script>

<style scoped>
@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fade-in 0.6s ease-out forwards;
}
</style>
