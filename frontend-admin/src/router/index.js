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
  // { path: '/menu', component: () => import('../views/MenuAdminView.vue') },     // U2
  // { path: '/orders/:id', component: () => import('../views/OrderDetailView.vue') }, // U3
  // { path: '/dashboard', component: () => import('../views/DashboardView.vue') },// U4
  // { path: '/history', component: () => import('../views/HistoryView.vue') },    // U4
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
