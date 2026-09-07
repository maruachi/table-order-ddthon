<script setup>
// US-A3: order detail modal + status change. Meant to be opened from the U4
// dashboard when an admin clicks an order card.
import { ref, watch } from 'vue'
import orderAdminApi from '../../api/orderAdminApi'
import DeleteOrderAction from './DeleteOrderAction.vue'

const props = defineProps({
  orderId: { type: Number, required: true },
})
const emit = defineEmits(['close', 'changed', 'deleted'])

const order = ref(null)
const loading = ref(false)
const error = ref('')
const saving = ref(false)

const STATUSES = [
  { value: 'pending', label: '대기중' },
  { value: 'preparing', label: '준비중' },
  { value: 'done', label: '완료' },
]

async function load() {
  loading.value = true
  error.value = ''
  try {
    order.value = await orderAdminApi.get(props.orderId)
  } catch (e) {
    error.value = e?.response?.data?.detail || '주문을 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

async function changeStatus(status) {
  if (!order.value || saving.value) return
  saving.value = true
  error.value = ''
  try {
    const updated = await orderAdminApi.updateStatus(props.orderId, status)
    order.value.status = updated.status
    emit('changed', updated)
  } catch (e) {
    error.value = e?.response?.data?.detail || '상태 변경에 실패했습니다.'
  } finally {
    saving.value = false
  }
}

function onDeleted(totals) {
  emit('deleted', totals)
  emit('close')
}

watch(() => props.orderId, load, { immediate: true })
</script>

<template>
  <div class="backdrop" data-testid="order-detail-modal" @click.self="emit('close')">
    <div class="modal">
      <header class="head">
        <h2 v-if="order">주문 #{{ order.order_no }}</h2>
        <button type="button" class="btn close" data-testid="modal-close" @click="emit('close')">
          ✕
        </button>
      </header>

      <p v-if="loading" data-testid="modal-loading">불러오는 중…</p>
      <p v-if="error" class="error" data-testid="modal-error">{{ error }}</p>

      <template v-if="order">
        <ul class="items">
          <li v-for="it in order.items" :key="it.menu_id" data-testid="detail-item">
            {{ it.menu_name }} × {{ it.qty }} —
            {{ (it.unit_price).toLocaleString() }}원
            <span class="line">= {{ it.line_total.toLocaleString() }}원</span>
          </li>
        </ul>
        <div class="total" data-testid="detail-total">
          총액: <strong>{{ order.total.toLocaleString() }}원</strong>
        </div>

        <div class="status-row">
          <span>상태:</span>
          <button
            v-for="s in STATUSES"
            :key="s.value"
            type="button"
            class="btn status"
            :class="{ active: order.status === s.value }"
            :data-testid="`status-${s.value}`"
            :disabled="saving"
            @click="changeStatus(s.value)"
          >
            {{ s.label }}
          </button>
        </div>

        <DeleteOrderAction :order-id="order.id" @deleted="onDeleted" />
      </template>
    </div>
  </div>
</template>

<style scoped>
.backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; }
.modal { background: #fff; border-radius: 12px; padding: 20px; width: min(480px, 92vw); }
.head { display: flex; justify-content: space-between; align-items: center; }
.items { list-style: none; padding: 0; }
.items li { padding: 6px 0; border-bottom: 1px solid #eee; }
.line { color: #666; margin-left: 6px; }
.total { margin: 12px 0; }
.status-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin: 12px 0; }
.btn { min-height: 44px; min-width: 44px; border: 1px solid #ccc; border-radius: 8px; background: #fff; padding: 0 12px; }
.btn.status.active { background: #2563eb; color: #fff; border-color: #2563eb; }
.btn.close { min-width: 44px; }
.btn:disabled { opacity: 0.5; }
.error { color: #dc2626; }
</style>
