// Admin SPA router (U0 shell). Units register their views into `routes`.
import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '../api/token'
import HomeView from '../views/HomeView.vue'

const routes = [
  // U1 Auth:
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/auth/AdminLoginView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/tables',
    name: 'tables',
    component: () => import('../views/auth/TableManageView.vue'),
    meta: { requiresAuth: true },
  },
  // Route slots per unit (placeholders until each unit lands):
  { path: '/menu', name: 'menu-admin', component: () => import('../views/MenuAdminView.vue'), meta: { requiresAuth: true } }, // U2
  // U3 order management (US-A3/A5) is handled via OrderDetailModal opened from
  // the dashboard order rows — no standalone route needed.
  // U4 routes. requiresAuth stays false until U1 login lands (standalone build/run);
  // U1 to flip these to requiresAuth: true on integration.
  { path: '/dashboard', name: 'dashboard', component: () => import('../views/DashboardView.vue'), meta: { requiresAuth: false } },
  { path: '/history', name: 'history', component: () => import('../views/HistoryView.vue'), meta: { requiresAuth: false } },
  { path: '/', name: 'home', component: HomeView, meta: { requiresAuth: false } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !getToken()) {
    return { path: '/login' }
  }
  return true
})

export default router
