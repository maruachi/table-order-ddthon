// Customer SPA router (U0 shell). Units register their views into `routes`.
import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '../api/token'
import HomeView from '../views/HomeView.vue'

const routes = [
  // Route slots per unit (placeholders until each unit lands):
  // { path: '/setup', component: () => import('../views/SetupView.vue') },   // U1
  // { path: '/menu', component: () => import('../views/MenuView.vue') },     // U2
  // U3 Order+Cart routes (table role):
  {
    path: '/cart',
    name: 'cart',
    component: () => import('../views/order/CartView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/order/confirm',
    name: 'order-confirm',
    component: () => import('../views/order/OrderConfirmView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/orders',
    name: 'current-orders',
    component: () => import('../views/order/CurrentOrdersView.vue'),
    meta: { requiresAuth: true },
  },
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
