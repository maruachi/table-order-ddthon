// Admin SPA router (U0 shell). Units register their views into `routes`.
import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '../api/token'
import HomeView from '../views/HomeView.vue'

const routes = [
  // Route slots per unit (placeholders until each unit lands):
  // { path: '/login', component: () => import('../views/LoginView.vue') },        // U1
  // { path: '/tables', component: () => import('../views/TablesView.vue') },      // U1
  { path: '/menu', name: 'menu-admin', component: () => import('../views/MenuAdminView.vue'), meta: { requiresAuth: true } }, // U2
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
