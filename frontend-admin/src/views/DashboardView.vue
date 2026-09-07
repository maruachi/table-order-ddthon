<script setup>
// U4 실시간 대시보드 (US-A2/A6, NFR-6). 스냅샷 로드 + admin SSE 라이브 갱신.
// 재연결(Q7=C): onopen 시 스냅샷 재조회로 재동기화.
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import { openSse } from '../api/sse'
import { getDashboard, closeSession } from '../api/session'

const tables = ref([])
const filterTableId = ref(null)
const connected = ref(false)
const toast = ref(null)

let es = null
const highlightTimers = {}

const filteredTables = computed(() => {
  if (filterTableId.value == null || filterTableId.value === '') return tables.value
  return tables.value.filter((t) => t.table_id === filterTableId.value)
})

const tableOptions = computed(() =>
  tables.value.map((t) => ({ id: t.table_id, label: t.table_number ?? t.table_id })),
)

function formatAmount(n) {
  return Number(n || 0).toLocaleString('ko-KR')
}

async function loadDashboard() {
  try {
    const res = await getDashboard(3)
    const list = Array.isArray(res) ? res : (res && (res.tables || res.items)) || []
    tables.value = list.map((c) => ({ ...c, recent_orders: c.recent_orders || [], highlight: false }))
  } catch {
    /* keep current state on failure */
  }
}

function findCard(tableId) {
  return tables.value.find((t) => t.table_id === tableId)
}

function flashCard(card) {
  card.highlight = true
  clearTimeout(highlightTimers[card.table_id])
  highlightTimers[card.table_id] = setTimeout(() => {
    card.highlight = false
  }, 1500)
}

function onEvent(evt) {
  if (!evt || !evt.type) return
  const payload = evt.payload || {}
  const tableId = payload.table_id
  if (tableId == null) return
  const card = findCard(tableId)
  if (!card) return // 카드 없으면 무시 — 스냅샷 재조회로 보정

  if (evt.type === 'session.closed') {
    card.total_amount = 0
    card.recent_orders = []
    return
  }
  if (evt.type.startsWith('order.')) {
    if (typeof payload.total_amount === 'number') card.total_amount = payload.total_amount
    if (payload.order_no != null) {
      const preview = {
        order_no: payload.order_no,
        order_status: payload.order_status,
        order_amount: payload.order_amount,
      }
      const rest = (card.recent_orders || []).filter((o) => o.order_no !== payload.order_no)
      card.recent_orders = [preview, ...rest].slice(0, 3)
    }
    flashCard(card)
  }
}

async function onClose(card) {
  const label = card.table_number ?? card.table_id
  if (!window.confirm(`테이블 ${label} 세션을 종료할까요?`)) return
  try {
    const summary = await closeSession(card.table_id)
    card.total_amount = 0
    card.recent_orders = []
    const amount = summary?.total_amount ?? 0
    const count =
      summary?.order_count ??
      summary?.orders_count ??
      (Array.isArray(summary?.orders) ? summary.orders.length : null)
    toast.value = `이용 완료 · 총액 ${formatAmount(amount)}원${count != null ? ` · 주문 ${count}건` : ''}`
    setTimeout(() => {
      toast.value = null
    }, 3000)
  } catch {
    window.alert('세션 종료에 실패했습니다. 다시 시도해주세요.')
  }
}

onMounted(() => {
  loadDashboard()
  es = openSse('/realtime/admin/stream', onEvent)
  es.onopen = () => {
    connected.value = true
    loadDashboard()
  }
  es.onerror = () => {
    connected.value = false
  }
})

onBeforeUnmount(() => {
  es?.close()
  Object.values(highlightTimers).forEach(clearTimeout)
})
</script>

<template>
  <AdminLayout>
    <template #header>
      <strong>실시간 대시보드</strong>
      <span class="conn" :class="{ on: connected }" data-testid="conn-status">
        {{ connected ? '실시간 연결됨' : '연결 대기' }}
      </span>
    </template>

    <section class="dashboard" data-testid="dashboard-view">
      <div class="toolbar">
        <label class="filter">
          <span>테이블 필터</span>
          <select v-model="filterTableId" data-testid="table-filter">
            <option :value="null">전체</option>
            <option v-for="opt in tableOptions" :key="opt.id" :value="opt.id">
              테이블 {{ opt.label }}
            </option>
          </select>
        </label>
      </div>

      <p v-if="filteredTables.length === 0" class="empty" data-testid="dashboard-empty">
        활성 세션이 없습니다.
      </p>

      <div class="grid">
        <article
          v-for="card in filteredTables"
          :key="card.table_id"
          class="card"
          :class="{ highlight: card.highlight }"
          data-testid="table-card"
        >
          <header class="card-head">
            <span class="table-no">테이블 {{ card.table_number ?? card.table_id }}</span>
            <span class="total">{{ formatAmount(card.total_amount) }}원</span>
          </header>

          <ul class="orders">
            <li v-if="!card.recent_orders || card.recent_orders.length === 0" class="muted">
              주문 없음
            </li>
            <li v-for="(o, i) in card.recent_orders" :key="o.order_no ?? i">
              <span class="order-no">#{{ o.order_no }}</span>
              <span v-if="o.order_status" class="badge">{{ o.order_status }}</span>
              <span class="order-amt">{{ formatAmount(o.order_amount) }}원</span>
            </li>
          </ul>

          <button class="close-btn" data-testid="close-session-btn" @click="onClose(card)">
            이용 완료
          </button>
        </article>
      </div>

      <div v-if="toast" class="toast" data-testid="close-toast">{{ toast }}</div>
    </section>
  </AdminLayout>
</template>

<style scoped>
.conn {
  margin-left: 12px;
  font-size: 13px;
  color: #9ca3af;
}
.conn.on {
  color: #059669;
}
.dashboard {
  position: relative;
}
.toolbar {
  margin-bottom: 16px;
}
.filter {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}
.filter select {
  min-height: 44px;
  padding: 0 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
}
.empty {
  color: #6b7280;
  padding: 24px 0;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}
.card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: box-shadow 0.3s ease, border-color 0.3s ease;
}
.card.highlight {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.25);
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
.table-no {
  font-weight: 700;
  font-size: 16px;
}
.total {
  font-weight: 700;
  color: #111827;
}
.orders {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 60px;
}
.orders li {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
.orders .muted {
  color: #9ca3af;
}
.order-no {
  color: #374151;
}
.badge {
  padding: 2px 8px;
  border-radius: 999px;
  background: #eef2ff;
  color: #4338ca;
  font-size: 12px;
}
.order-amt {
  margin-left: auto;
  color: #6b7280;
}
.close-btn {
  min-height: 44px;
  border: none;
  border-radius: 8px;
  background: #2563eb;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}
.close-btn:hover {
  background: #1d4ed8;
}
.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: #111827;
  color: #fff;
  padding: 12px 18px;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
  font-size: 14px;
}
</style>
