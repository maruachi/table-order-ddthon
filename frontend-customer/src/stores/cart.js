// Cart store (U3, US-C3): client-side only, persisted to localStorage (NFR-5).
// Server is contacted only at order confirmation (US-C4). The cart is scoped per
// table token so different tablets/sessions don't share a basket.
import { defineStore } from 'pinia'
import { getToken } from '../api/token'

function storageKey() {
  // Namespace by token so a re-login / different table gets a fresh cart.
  const token = getToken() || 'anon'
  return `cart:${token.slice(0, 24)}`
}

function loadItems() {
  try {
    const raw = localStorage.getItem(storageKey())
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export const useCartStore = defineStore('cart', {
  state: () => ({
    // items: [{ menu_id, menu_name, unit_price, qty }]
    items: loadItems(),
  }),
  getters: {
    count: (state) => state.items.reduce((n, i) => n + i.qty, 0),
    total: (state) => state.items.reduce((sum, i) => sum + i.unit_price * i.qty, 0),
    isEmpty: (state) => state.items.length === 0,
  },
  actions: {
    persist() {
      localStorage.setItem(storageKey(), JSON.stringify(this.items))
    },
    add(menu, qty = 1) {
      const existing = this.items.find((i) => i.menu_id === menu.id)
      if (existing) {
        existing.qty += qty
      } else {
        this.items.push({
          menu_id: menu.id,
          menu_name: menu.name,
          unit_price: menu.price,
          qty,
        })
      }
      this.persist()
    },
    increment(menuId) {
      const item = this.items.find((i) => i.menu_id === menuId)
      if (item) {
        item.qty += 1
        this.persist()
      }
    },
    decrement(menuId) {
      const item = this.items.find((i) => i.menu_id === menuId)
      if (!item) return
      item.qty -= 1
      if (item.qty <= 0) this.remove(menuId)
      else this.persist()
    },
    remove(menuId) {
      this.items = this.items.filter((i) => i.menu_id !== menuId)
      this.persist()
    },
    clear() {
      this.items = []
      this.persist()
    },
    // Payload sent to POST /orders (server recomputes price authoritatively).
    toOrderPayload() {
      return { items: this.items.map((i) => ({ menu_id: i.menu_id, qty: i.qty })) }
    },
  },
})
