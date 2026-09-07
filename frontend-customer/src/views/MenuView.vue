<script setup>
// US-C2: customer menu browsing. Category nav + per-category sections +
// touch-friendly menu cards (NFR-6). Sold-out items show a badge and are not
// selectable. Adding to cart is U3's boundary (not implemented here).
import { ref, onMounted } from 'vue'
import CustomerLayout from '../layouts/CustomerLayout.vue'
import { fetchMenu } from '../api/menu'

const categories = ref([])
const loading = ref(true)
const error = ref('')
const selected = ref(null) // menu shown in the detail modal

const currency = (n) => `${n.toLocaleString('ko-KR')}원`

async function load() {
  loading.value = true
  error.value = ''
  try {
    categories.value = await fetchMenu()
  } catch (e) {
    error.value = '메뉴를 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

function openDetail(menu) {
  if (!menu.available) return // sold-out not selectable
  selected.value = menu
}

function closeDetail() {
  selected.value = null
}

function scrollTo(id) {
  const el = document.getElementById(`category-${id}`)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

onMounted(load)
</script>

<template>
  <CustomerLayout>
    <section data-testid="menu-view">
      <div v-if="loading" data-testid="menu-loading">메뉴를 불러오는 중…</div>
      <div v-else-if="error" data-testid="menu-error">
        {{ error }}
        <button class="retry" data-testid="menu-retry" @click="load">다시 시도</button>
      </div>
      <template v-else>
        <!-- category quick-nav -->
        <nav class="category-nav" data-testid="category-nav">
          <button
            v-for="cat in categories"
            :key="cat.id"
            class="chip"
            :data-testid="`category-chip-${cat.id}`"
            @click="scrollTo(cat.id)"
          >
            {{ cat.name }}
          </button>
        </nav>

        <div v-if="categories.length === 0" data-testid="menu-empty" class="empty">
          등록된 메뉴가 없습니다.
        </div>

        <section
          v-for="cat in categories"
          :id="`category-${cat.id}`"
          :key="cat.id"
          class="category-section"
          :data-testid="`category-section-${cat.id}`"
        >
          <h2 class="category-title">{{ cat.name }}</h2>
          <div class="menu-grid">
            <button
              v-for="menu in cat.menus"
              :key="menu.id"
              class="menu-card"
              :class="{ 'sold-out': !menu.available }"
              :data-testid="`menu-card-${menu.id}`"
              :disabled="!menu.available"
              @click="openDetail(menu)"
            >
              <div class="thumb">
                <img v-if="menu.image_url" :src="menu.image_url" :alt="menu.name" />
                <div v-else class="thumb-placeholder">🍽️</div>
                <span v-if="!menu.available" class="badge" data-testid="sold-out-badge">품절</span>
              </div>
              <div class="info">
                <div class="name">{{ menu.name }}</div>
                <div class="price">{{ currency(menu.price) }}</div>
              </div>
            </button>
          </div>
        </section>
      </template>

      <!-- detail modal -->
      <div v-if="selected" class="modal-backdrop" data-testid="menu-detail-modal" @click.self="closeDetail">
        <div class="modal">
          <img v-if="selected.image_url" :src="selected.image_url" :alt="selected.name" class="modal-img" />
          <h3>{{ selected.name }}</h3>
          <p class="modal-price">{{ currency(selected.price) }}</p>
          <p v-if="selected.description" class="modal-desc">{{ selected.description }}</p>
          <!-- "장바구니 담기" belongs to U3 Order; intentionally omitted here. -->
          <button class="close" data-testid="menu-detail-close" @click="closeDetail">닫기</button>
        </div>
      </div>
    </section>
  </CustomerLayout>
</template>

<style scoped>
.category-nav {
  display: flex; gap: 8px; overflow-x: auto; padding-bottom: 12px;
  position: sticky; top: 0; background: #fff; z-index: 1;
}
.chip {
  flex: 0 0 auto; min-height: 44px; padding: 0 16px; border-radius: 22px;
  border: 1px solid #d1d5db; background: #f9fafb; font-size: 15px;
}
.category-section { margin-top: 20px; }
.category-title { font-size: 18px; margin: 0 0 12px; }
.menu-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.menu-card {
  display: flex; flex-direction: column; text-align: left; padding: 0;
  border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden;
  background: #fff; min-height: 44px;
}
.menu-card.sold-out { opacity: 0.55; }
.thumb { position: relative; width: 100%; aspect-ratio: 4 / 3; background: #f3f4f6; }
.thumb img { width: 100%; height: 100%; object-fit: cover; }
.thumb-placeholder { display: flex; align-items: center; justify-content: center; height: 100%; font-size: 32px; }
.badge {
  position: absolute; top: 8px; left: 8px; background: #ef4444; color: #fff;
  font-size: 12px; padding: 2px 8px; border-radius: 4px;
}
.info { padding: 10px 12px; }
.name { font-weight: 600; }
.price { color: #374151; margin-top: 4px; }
.empty { color: #6b7280; padding: 40px 0; text-align: center; }
.retry { margin-left: 8px; min-height: 44px; padding: 0 16px; }
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.4);
  display: flex; align-items: center; justify-content: center; padding: 20px;
}
.modal { background: #fff; border-radius: 16px; padding: 20px; max-width: 420px; width: 100%; }
.modal-img { width: 100%; border-radius: 12px; margin-bottom: 12px; }
.modal-price { color: #2563eb; font-weight: 700; }
.modal-desc { color: #4b5563; }
.close { width: 100%; min-height: 48px; margin-top: 16px; border-radius: 10px; border: none; background: #2563eb; color: #fff; font-size: 16px; }
</style>
