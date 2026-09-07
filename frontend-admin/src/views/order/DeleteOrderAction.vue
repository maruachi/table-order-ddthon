<script setup>
// US-A5: delete an order with a confirmation popup. Emits recomputed table totals.
import { ref } from 'vue'
import orderAdminApi from '../../api/orderAdminApi'

const props = defineProps({
  orderId: { type: Number, required: true },
})
const emit = defineEmits(['deleted'])

const confirming = ref(false)
const deleting = ref(false)
const error = ref('')

async function confirmDelete() {
  deleting.value = true
  error.value = ''
  try {
    const totals = await orderAdminApi.delete(props.orderId)
    emit('deleted', totals) // { table_id, total }
    confirming.value = false
  } catch (e) {
    error.value = e?.response?.data?.detail || '삭제에 실패했습니다. 주문은 유지됩니다.'
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="delete-action" data-testid="delete-order-action">
    <button
      v-if="!confirming"
      type="button"
      class="btn danger"
      data-testid="delete-order-button"
      @click="confirming = true"
    >
      주문 삭제
    </button>

    <div v-else class="confirm" data-testid="delete-confirm">
      <span>정말 이 주문을 삭제하시겠습니까?</span>
      <div class="buttons">
        <button
          type="button"
          class="btn"
          data-testid="delete-cancel"
          :disabled="deleting"
          @click="confirming = false"
        >
          취소
        </button>
        <button
          type="button"
          class="btn danger"
          data-testid="delete-confirm-button"
          :disabled="deleting"
          @click="confirmDelete"
        >
          {{ deleting ? '삭제 중…' : '삭제 확인' }}
        </button>
      </div>
    </div>

    <p v-if="error" class="error" data-testid="delete-error">{{ error }}</p>
  </div>
</template>

<style scoped>
.delete-action { margin-top: 12px; }
.confirm { border: 1px solid #fca5a5; background: #fef2f2; border-radius: 8px; padding: 12px; }
.buttons { display: flex; gap: 8px; margin-top: 8px; }
.btn { min-height: 44px; min-width: 44px; border: 1px solid #ccc; border-radius: 8px; background: #fff; padding: 0 12px; }
.btn.danger { background: #dc2626; color: #fff; border-color: #dc2626; }
.btn:disabled { opacity: 0.5; }
.error { color: #dc2626; margin-top: 8px; }
</style>
