// Admin SPA router (U0 shell). Units register their views into `routes`.
import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '../api/token'
import HomeView from '../views/HomeView.vue'

const routes = [
  // Route slots per unit (placeholders until each unit lands):
  // { path: '/login', component: () => import('../views/LoginView.vue') },        // U1
  // { path: '/tables', component: () => import('../views/TablesView.vue') },      // U1
  // { path: '/menu', component: () => import('../views/MenuAdminView.vue') },     // U2
  // { path: '/orders/:id', component: () => import('../views/OrderDetailView.vue') }, // U3
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
