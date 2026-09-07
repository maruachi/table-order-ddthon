// Order admin API client (U3, admin). Uses the U0 shell axios client.
import client from './client'

export default {
  // US-A3: order detail (menu/qty/unit price/total).
  get(orderId) {
    return client.get(`/orders/${orderId}`).then((r) => r.data)
  },
  // US-A3: change cooking status (pending | preparing | done).
  updateStatus(orderId, status) {
    return client
      .patch(`/orders/${orderId}/status`, { status })
      .then((r) => r.data)
  },
  // US-A5: delete an order; returns recomputed { table_id, total }.
  delete(orderId) {
    return client.delete(`/orders/${orderId}`).then((r) => r.data)
  },
  // US-A2 (initial snapshot, consumed by U4 dashboard): per-table totals + latest orders.
  dashboardSnapshot({ tableId = null } = {}) {
    const params = tableId != null ? { table_id: tableId } : {}
    return client.get('/orders/dashboard', { params }).then((r) => r.data)
  },
}
