// Customer SPA router (U0 shell). Units register their views into `routes`.
import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '../api/token'
import HomeView from '../views/HomeView.vue'

const routes = [
  // Route slots per unit (placeholders until each unit lands):
  // { path: '/setup', component: () => import('../views/SetupView.vue') },   // U1
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
router.beforeEach((to) => {
  if (to.meta.requiresAuth && !getToken()) {
    return { path: '/setup' }
  }
  return true
})

export default router
