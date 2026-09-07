// Order API client (U3, customer). Uses the U0 shell axios client (token + 401).
import client from './client'

export default {
  // US-C4: confirm an order. payload = { items: [{ menu_id, qty }] }
  create(payload) {
    return client.post('/orders', payload).then((r) => r.data)
  },
  // US-C5: current session's orders (paginated).
  listCurrent({ offset = 0, limit = 50 } = {}) {
    return client
      .get('/orders/current', { params: { offset, limit } })
      .then((r) => r.data)
  },
  // Order detail.
  get(orderId) {
    return client.get(`/orders/${orderId}`).then((r) => r.data)
  },
}
