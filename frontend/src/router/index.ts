import { createRouter, createWebHistory } from 'vue-router';
import { useAuth } from '@/composables/useAuth';
import { logger } from '@/utils/logger';
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
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/connections',
    name: 'Connections',
    component: () => import('@/views/Connections.vue'),
    meta: { requiresAuth: true }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// Navigation guard
router.beforeEach((to, _from, next) => {
  const { isAuthenticated, user, token } = useAuth();
  
  logger.router('Router guard check:', {
    to: to.path,
    requiresAuth: to.meta.requiresAuth,
    requiresGuest: to.meta.requiresGuest,
    isAuthenticated: isAuthenticated.value,
    hasUser: !!user.value,
    hasToken: !!token.value,
    tokenPrefix: token.value?.substring(0, 10) + '...'
  });
  
  if (to.meta.requiresAuth && !isAuthenticated.value) {
    logger.warn('Access denied - redirecting to login');
    next('/login');
  } else if (to.meta.requiresGuest && isAuthenticated.value) {
    logger.info('Already authenticated - redirecting to home');
    next('/home');
  } else {
    logger.debug('Navigation allowed');
    next();
  }
});

export default router;
