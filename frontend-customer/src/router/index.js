// Customer SPA router (U0 shell). Units register their views into `routes`.
import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '../api/token'
import HomeView from '../views/HomeView.vue'

const routes = [
  // U1 Auth:
  {
    path: '/setup',
    name: 'setup',
    component: () => import('../views/auth/SetupView.vue'),
    meta: { requiresAuth: false },
  },
  // Route slots per unit (placeholders until each unit lands):
  // { path: '/menu', component: () => import('../views/MenuView.vue') },     // U2
  // { path: '/cart', component: () => import('../views/CartView.vue') },     // U3
  // { path: '/order', component: () => import('../views/OrderView.vue') },   // U3
  // { path: '/history', component: () => import('../views/HistoryView.vue') },// U3
  { path: '/', name: 'home', component: HomeView, meta: { requiresAuth: false } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard: unauthenticated -> setup (U1) for protected routes.
// Auto-login (US-C1): if a token already exists, skip setup and go to /menu.
router.beforeEach((to) => {
  if (to.meta.requiresAuth && !getToken()) {
    return { path: '/setup' }
  }
  if (to.path === '/setup' && getToken()) {
    return { path: '/menu' }
  }
  return true
})

export default router
