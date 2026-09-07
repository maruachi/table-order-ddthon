<script setup>
// US-C3: cart management — quantity control, remove, clear, live total.
import { useRouter } from 'vue-router'
import CustomerLayout from '../../layouts/CustomerLayout.vue'
import { useCartStore } from '../../stores/cart'

const cart = useCartStore()
const router = useRouter()

function goConfirm() {
  if (!cart.isEmpty) router.push('/order/confirm')
}
</script>

<template>
  <CustomerLayout>
  <section class="cart" data-testid="cart-view">
    <h1>장바구니</h1>

    <p v-if="cart.isEmpty" class="empty" data-testid="cart-empty">
      장바구니가 비어 있습니다.
    </p>

    <ul v-else class="items">
      <li v-for="item in cart.items" :key="item.menu_id" class="item" data-testid="cart-item">
        <div class="info">
          <span class="name">{{ item.menu_name }}</span>
          <span class="price">{{ item.unit_price.toLocaleString() }}원</span>
        </div>
        <div class="qty">
          <button
            type="button"
            class="btn"
            data-testid="cart-item-decrement"
            @click="cart.decrement(item.menu_id)"
          >
            −
          </button>
          <span class="qty-value" data-testid="cart-item-qty">{{ item.qty }}</span>
          <button
            type="button"
            class="btn"
            data-testid="cart-item-increment"
            @click="cart.increment(item.menu_id)"
          >
            +
          </button>
          <button
            type="button"
            class="btn remove"
            data-testid="cart-item-remove"
            @click="cart.remove(item.menu_id)"
          >
            삭제
          </button>
        </div>
      </li>
    </ul>

    <div class="footer">
      <div class="total" data-testid="cart-total">
        총 금액: <strong>{{ cart.total.toLocaleString() }}원</strong>
      </div>
      <div class="actions">
        <button
          type="button"
          class="btn"
          data-testid="cart-clear-button"
          :disabled="cart.isEmpty"
          @click="cart.clear()"
        >
          비우기
        </button>
        <button
          type="button"
          class="btn primary"
          data-testid="cart-checkout-button"
          :disabled="cart.isEmpty"
          @click="goConfirm"
        >
          주문하기
        </button>
      </div>
    </div>
  </section>
  </CustomerLayout>
</template>

<style scoped>
.cart { padding: 16px; }
.items { list-style: none; padding: 0; margin: 0; }
.item { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #eee; }
.info { display: flex; flex-direction: column; }
.qty { display: flex; align-items: center; gap: 8px; }
.btn { min-width: 44px; min-height: 44px; border: 1px solid #ccc; border-radius: 8px; background: #fff; font-size: 16px; }
.btn.primary { background: #2563eb; color: #fff; border-color: #2563eb; }
.btn.remove { min-width: auto; padding: 0 10px; }
.btn:disabled { opacity: 0.5; }
.footer { position: sticky; bottom: 0; background: #fff; padding-top: 12px; }
.actions { display: flex; gap: 8px; margin-top: 8px; }
.empty { color: #888; }
</style>
