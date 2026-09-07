<script setup>
// US-C5: current session order history with status.
import { ref, onMounted } from 'vue'
import orderApi from '../../api/orderApi'

const orders = ref([])
const total = ref(0)
const loading = ref(false)
const error = ref('')
const offset = ref(0)
const limit = 20

const STATUS_LABEL = { pending: '대기중', preparing: '준비중', done: '완료' }

async function load(reset = false) {
  loading.value = true
  error.value = ''
  try {
    if (reset) {
      offset.value = 0
      orders.value = []
    }
    const page = await orderApi.listCurrent({ offset: offset.value, limit })
    orders.value = reset ? page.items : [...orders.value, ...page.items]
    total.value = page.total
    offset.value += page.items.length
  } catch (e) {
    error.value = e?.response?.data?.detail || '주문 내역을 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

const hasMore = () => orders.value.length < total.value

onMounted(() => load(true))
</script>

<template>
  <section class="orders" data-testid="current-orders-view">
    <h1>주문 내역</h1>
    <p v-if="error" class="error" data-testid="orders-error">{{ error }}</p>
    <p v-else-if="!loading && orders.length === 0" class="empty" data-testid="orders-empty">
      현재 세션의 주문이 없습니다.
    </p>

    <ul class="list">
      <li v-for="o in orders" :key="o.id" class="order" data-testid="order-row">
        <div class="head">
          <span class="no">#{{ o.order_no }}</span>
          <span class="status" :class="o.status" data-testid="order-status">
            {{ STATUS_LABEL[o.status] || o.status }}
          </span>
        </div>
        <div class="meta">
          <span>{{ new Date(o.created_at).toLocaleTimeString() }}</span>
          <span class="amount">{{ o.total.toLocaleString() }}원</span>
        </div>
      </li>
    </ul>

    <button
      v-if="hasMore()"
      type="button"
      class="btn"
      data-testid="orders-load-more"
      :disabled="loading"
      @click="load(false)"
    >
      {{ loading ? '불러오는 중…' : '더 보기' }}
    </button>
  </section>
</template>

<style scoped>
.orders { padding: 16px; }
.list { list-style: none; padding: 0; margin: 0; }
.order { padding: 12px; border: 1px solid #eee; border-radius: 8px; margin-bottom: 8px; }
.head { display: flex; justify-content: space-between; align-items: center; }
.no { font-weight: 600; }
.status { font-size: 13px; padding: 2px 8px; border-radius: 12px; background: #eee; }
.status.pending { background: #fef3c7; }
.status.preparing { background: #dbeafe; }
.status.done { background: #dcfce7; }
.meta { display: flex; justify-content: space-between; color: #666; margin-top: 6px; }
.amount { color: #111; }
.btn { min-height: 44px; width: 100%; border: 1px solid #ccc; border-radius: 8px; background: #fff; }
.error { color: #dc2626; }
.empty { color: #888; }
</style>
