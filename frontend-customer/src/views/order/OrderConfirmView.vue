<script setup>
// US-C4: final confirmation and order submission.
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import CustomerLayout from '../../layouts/CustomerLayout.vue'
import { useCartStore } from '../../stores/cart'
import orderApi from '../../api/orderApi'

const cart = useCartStore()
const router = useRouter()

const submitting = ref(false)
const error = ref('')
const result = ref(null) // { order_no, total }
const redirectSeconds = ref(5)

const canSubmit = computed(() => !cart.isEmpty && !submitting.value)

async function confirm() {
  if (!canSubmit.value) return
  submitting.value = true
  error.value = ''
  try {
    const order = await orderApi.create(cart.toOrderPayload())
    result.value = { order_no: order.order_no, total: order.total }
    cart.clear() // US-C4: cart auto-emptied on success
    startRedirect()
  } catch (e) {
    // Failure: keep cart intact, show message (US-C4).
    error.value = e?.response?.data?.detail || '주문 처리에 실패했습니다. 다시 시도해 주세요.'
  } finally {
    submitting.value = false
  }
}

function startRedirect() {
  const timer = setInterval(() => {
    redirectSeconds.value -= 1
    if (redirectSeconds.value <= 0) {
      clearInterval(timer)
      router.push('/menu')
    }
  }, 1000)
}
</script>

<template>
  <CustomerLayout>
  <section class="confirm" data-testid="order-confirm-view">
    <template v-if="!result">
      <h1>주문 확인</h1>
      <p v-if="cart.isEmpty" class="empty" data-testid="confirm-empty">
        장바구니가 비어 있습니다.
      </p>
      <ul v-else class="items">
        <li v-for="item in cart.items" :key="item.menu_id" data-testid="confirm-item">
          {{ item.menu_name }} × {{ item.qty }} —
          {{ (item.unit_price * item.qty).toLocaleString() }}원
        </li>
      </ul>
      <div class="total" data-testid="confirm-total">
        총 금액: <strong>{{ cart.total.toLocaleString() }}원</strong>
      </div>
      <p v-if="error" class="error" data-testid="confirm-error">{{ error }}</p>
      <button
        type="button"
        class="btn primary"
        data-testid="confirm-submit-button"
        :disabled="!canSubmit"
        @click="confirm"
      >
        {{ submitting ? '처리 중…' : '주문 확정' }}
      </button>
    </template>

    <template v-else>
      <div class="success" data-testid="order-success">
        <h1>주문이 완료되었습니다</h1>
        <p class="order-no" data-testid="success-order-no">
          주문번호 <strong>#{{ result.order_no }}</strong>
        </p>
        <p>결제 금액: {{ result.total.toLocaleString() }}원</p>
        <p class="redirect">{{ redirectSeconds }}초 후 메뉴 화면으로 이동합니다…</p>
      </div>
    </template>
  </section>
  </CustomerLayout>
</template>

<style scoped>
.confirm { padding: 16px; }
.items { list-style: none; padding: 0; }
.items li { padding: 8px 0; border-bottom: 1px solid #eee; }
.total { margin: 16px 0; }
.error { color: #dc2626; }
.btn { min-width: 44px; min-height: 44px; border-radius: 8px; border: 1px solid #ccc; background: #fff; }
.btn.primary { background: #2563eb; color: #fff; border-color: #2563eb; width: 100%; }
.btn:disabled { opacity: 0.5; }
.success { text-align: center; padding: 32px 16px; }
.order-no strong { font-size: 24px; }
.redirect { color: #888; margin-top: 16px; }
.empty { color: #888; }
</style>
