<script setup>
// US-A8: admin menu management. Left: category panel (CRUD + select).
// Right: menus in the selected category (CRUD + sold-out toggle).
// Client-side validation mirrors backend rules (name required, price int >= 0,
// image_url optional http(s)).
import { ref, computed, onMounted } from 'vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import * as api from '../api/menuAdmin'

const categories = ref([])
const menus = ref([])
const selectedCategoryId = ref(null)
const error = ref('')

// category form
const newCategoryName = ref('')

// menu form modal
const showMenuForm = ref(false)
const editingMenuId = ref(null)
const form = ref({ name: '', price: '', description: '', image_url: '' })
const formError = ref('')

const selectedCategory = computed(() =>
  categories.value.find((c) => c.id === selectedCategoryId.value) || null,
)
const menusInCategory = computed(() =>
  menus.value.filter((m) => m.category_id === selectedCategoryId.value),
)

const currency = (n) => `${Number(n).toLocaleString('ko-KR')}원`

async function refresh() {
  error.value = ''
  try {
    categories.value = await api.listCategories()
    menus.value = await api.listMenus()
    if (!selectedCategoryId.value && categories.value.length) {
      selectedCategoryId.value = categories.value[0].id
    }
  } catch (e) {
    error.value = '데이터를 불러오지 못했습니다.'
  }
}

// --- categories ---
async function addCategory() {
  const name = newCategoryName.value.trim()
  if (!name) return
  try {
    await api.createCategory(name)
    newCategoryName.value = ''
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '카테고리 생성 실패'
  }
}
async function removeCategory(cat) {
  if (!confirm(`카테고리 "${cat.name}"를 삭제할까요?`)) return
  try {
    await api.deleteCategory(cat.id)
    if (selectedCategoryId.value === cat.id) selectedCategoryId.value = null
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '카테고리 삭제 실패 (활성 메뉴가 있는지 확인)'
  }
}

// --- menus ---
function openCreate() {
  editingMenuId.value = null
  form.value = { name: '', price: '', description: '', image_url: '' }
  formError.value = ''
  showMenuForm.value = true
}
function openEdit(menu) {
  editingMenuId.value = menu.id
  form.value = {
    name: menu.name,
    price: String(menu.price),
    description: menu.description || '',
    image_url: menu.image_url || '',
  }
  formError.value = ''
  showMenuForm.value = true
}
function validate() {
  if (!form.value.name.trim()) return '이름은 필수입니다.'
  const price = Number(form.value.price)
  if (!Number.isInteger(price) || price < 0) return '가격은 0 이상의 정수여야 합니다.'
  if (form.value.image_url && !/^https?:\/\//.test(form.value.image_url))
    return '이미지 URL은 http(s):// 형식이어야 합니다.'
  return ''
}
async function submitMenu() {
  const msg = validate()
  if (msg) {
    formError.value = msg
    return
  }
  const payload = {
    category_id: selectedCategoryId.value,
    name: form.value.name.trim(),
    price: Number(form.value.price),
    description: form.value.description.trim() || null,
    image_url: form.value.image_url.trim() || null,
  }
  try {
    if (editingMenuId.value) await api.updateMenu(editingMenuId.value, payload)
    else await api.createMenu(payload)
    showMenuForm.value = false
    await refresh()
  } catch (e) {
    formError.value = e.response?.data?.detail || '저장 실패'
  }
}
async function removeMenu(menu) {
  if (!confirm(`"${menu.name}" 메뉴를 삭제할까요?`)) return
  await api.deleteMenu(menu.id)
  await refresh()
}
async function toggleAvailability(menu) {
  await api.setMenuAvailability(menu.id, !menu.available)
  await refresh()
}

onMounted(refresh)
</script>

<template>
  <AdminLayout>
    <template #header><strong>메뉴 관리</strong></template>
    <section data-testid="menu-admin-view" class="wrap">
      <p v-if="error" class="error" data-testid="menu-admin-error">{{ error }}</p>

      <div class="panels">
        <!-- category panel -->
        <div class="panel" data-testid="category-panel">
          <h3>카테고리</h3>
          <ul class="cat-list">
            <li
              v-for="cat in categories"
              :key="cat.id"
              :class="{ active: cat.id === selectedCategoryId }"
              :data-testid="`category-item-${cat.id}`"
            >
              <button class="cat-name" @click="selectedCategoryId = cat.id">{{ cat.name }}</button>
              <button class="danger" :data-testid="`category-delete-${cat.id}`" @click="removeCategory(cat)">삭제</button>
            </li>
          </ul>
          <div class="add-row">
            <input
              v-model="newCategoryName"
              placeholder="새 카테고리"
              data-testid="category-name-input"
              @keyup.enter="addCategory"
            />
            <button data-testid="category-add-button" @click="addCategory">추가</button>
          </div>
        </div>

        <!-- menu panel -->
        <div class="panel" data-testid="menu-panel">
          <div class="menu-header">
            <h3>{{ selectedCategory ? selectedCategory.name : '메뉴' }}</h3>
            <button
              v-if="selectedCategory"
              data-testid="menu-add-button"
              @click="openCreate"
            >
              + 메뉴 추가
            </button>
          </div>
          <p v-if="!selectedCategory" class="hint">카테고리를 선택하세요.</p>
          <table v-else class="menu-table">
            <thead>
              <tr><th>이름</th><th>가격</th><th>상태</th><th></th></tr>
            </thead>
            <tbody>
              <tr
                v-for="menu in menusInCategory"
                :key="menu.id"
                :data-testid="`menu-row-${menu.id}`"
              >
                <td>{{ menu.name }}</td>
                <td>{{ currency(menu.price) }}</td>
                <td>
                  <button
                    class="toggle"
                    :class="{ off: !menu.available }"
                    :data-testid="`menu-availability-${menu.id}`"
                    @click="toggleAvailability(menu)"
                  >
                    {{ menu.available ? '판매중' : '품절' }}
                  </button>
                </td>
                <td class="actions">
                  <button :data-testid="`menu-edit-${menu.id}`" @click="openEdit(menu)">수정</button>
                  <button class="danger" :data-testid="`menu-delete-${menu.id}`" @click="removeMenu(menu)">삭제</button>
                </td>
              </tr>
              <tr v-if="menusInCategory.length === 0">
                <td colspan="4" class="hint">이 카테고리에 메뉴가 없습니다.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- menu form modal -->
      <div v-if="showMenuForm" class="modal-backdrop" data-testid="menu-form-modal" @click.self="showMenuForm = false">
        <div class="modal">
          <h3>{{ editingMenuId ? '메뉴 수정' : '메뉴 추가' }}</h3>
          <label>이름<input v-model="form.name" data-testid="menu-form-name" /></label>
          <label>가격(원)<input v-model="form.price" type="number" min="0" step="1" data-testid="menu-form-price" /></label>
          <label>설명<textarea v-model="form.description" data-testid="menu-form-description" /></label>
          <label>이미지 URL<input v-model="form.image_url" placeholder="https://..." data-testid="menu-form-image" /></label>
          <p v-if="formError" class="error" data-testid="menu-form-error">{{ formError }}</p>
          <div class="modal-actions">
            <button @click="showMenuForm = false">취소</button>
            <button class="primary" data-testid="menu-form-submit" @click="submitMenu">저장</button>
          </div>
        </div>
      </div>
    </section>
  </AdminLayout>
</template>

<style scoped>
.wrap { max-width: 1000px; }
.error { color: #dc2626; }
.hint { color: #6b7280; }
.panels { display: grid; grid-template-columns: 260px 1fr; gap: 20px; }
.panel { border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px; }
.cat-list { list-style: none; padding: 0; margin: 0 0 12px; }
.cat-list li { display: flex; align-items: center; justify-content: space-between; padding: 6px 4px; border-radius: 6px; }
.cat-list li.active { background: #eff6ff; }
.cat-name { border: none; background: none; font-size: 15px; cursor: pointer; }
.add-row { display: flex; gap: 8px; }
.add-row input { flex: 1; padding: 8px; }
.menu-header { display: flex; align-items: center; justify-content: space-between; }
.menu-table { width: 100%; border-collapse: collapse; }
.menu-table th, .menu-table td { text-align: left; padding: 8px; border-bottom: 1px solid #f1f5f9; }
.actions { display: flex; gap: 6px; }
.toggle { padding: 4px 10px; border-radius: 6px; border: 1px solid #16a34a; color: #16a34a; background: #fff; }
.toggle.off { border-color: #ef4444; color: #ef4444; }
.danger { color: #dc2626; }
button { min-height: 36px; cursor: pointer; }
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; }
.modal { background: #fff; border-radius: 12px; padding: 20px; width: 420px; display: flex; flex-direction: column; gap: 10px; }
.modal label { display: flex; flex-direction: column; gap: 4px; font-size: 14px; }
.modal input, .modal textarea { padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px; }
.primary { background: #2563eb; color: #fff; border: none; border-radius: 6px; padding: 0 16px; }
</style>
