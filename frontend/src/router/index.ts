import { createRouter, createWebHistory } from 'vue-router';
import { useAuth } from '@/composables/useAuth';
import Landing from '@/views/Landing.vue';
import Home from '@/views/Home.vue';
import Login from '@/views/Login.vue';
import Dashboard from '@/views/Dashboard.vue';

const routes = [
  {
    path: '/',
    name: 'Landing',
    component: Landing,
    meta: { requiresAuth: false }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresGuest: true }
  },
  {
    path: '/home',
    name: 'Home',
    component: Home,
    meta: { requiresAuth: true }
  },
  {
    path: '/chat',
    redirect: '/home'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// Navigation guard
router.beforeEach((to, _from, next) => {
  const { isAuthenticated } = useAuth();
  
  // 인증이 필요한 페이지에 비로그인 사용자가 접근하는 경우
  if (to.meta.requiresAuth && !isAuthenticated.value) {
    next('/login');
  } 
  // 게스트 전용 페이지에 로그인 사용자가 접근하는 경우
  else if (to.meta.requiresGuest && isAuthenticated.value) {
    next('/home');
  }
  // 루트 경로에 로그인한 사용자가 접근하는 경우 홈으로 리다이렉트
  else if (to.path === '/' && isAuthenticated.value) {
    next('/home');
  }
  else {
    next();
  }
});

export default router;
