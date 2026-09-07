<script setup>
// Table setup screen (US-A4, require_admin): create/update table number + password.
import { computed, onMounted, ref } from 'vue'
import AdminLayout from '../../layouts/AdminLayout.vue'
import { listTables, createTable, updateTable } from '../../api/auth'

const tables = ref([])
const editingId = ref(null) // null => create mode
const formNumber = ref('')
const formPassword = ref('')
const loading = ref(false)
const feedback = ref('')
const feedbackError = ref(false)

const isEditing = computed(() => editingId.value !== null)
const canSubmit = computed(
  () =>
    !loading.value &&
    formNumber.value.trim() &&
    (isEditing.value || formPassword.value.trim()), // password required on create
)

async function load() {
  loading.value = true
  try {
    const { data } = await listTables()
    tables.value = data
  } catch {
    setFeedback('테이블 목록을 불러오지 못했습니다.', true)
  } finally {
    loading.value = false
  }
}

function setFeedback(msg, isError = false) {
  feedback.value = msg
  feedbackError.value = isError
}

function resetForm() {
  editingId.value = null
  formNumber.value = ''
  formPassword.value = ''
}

function startEdit(t) {
  editingId.value = t.id
  formNumber.value = t.table_number
  formPassword.value = ''
}

async function submit() {
  if (!canSubmit.value) return
  loading.value = true
  setFeedback('')
  try {
    if (isEditing.value) {
      await updateTable(editingId.value, {
        tableNumber: formNumber.value.trim(),
        password: formPassword.value.trim() || undefined,
      })
      setFeedback('테이블이 수정되었습니다.')
    } else {
      await createTable(formNumber.value.trim(), formPassword.value)
      setFeedback('테이블이 생성되었습니다.')
    }
    resetForm()
    await load()
  } catch (err) {
    // BR-U1-11: duplicate number -> ValidationError; keep list unchanged.
    const detail = err?.response?.data?.detail || '요청을 처리하지 못했습니다.'
    setFeedback(detail, true)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <AdminLayout>
    <template #header><strong>테이블 설정</strong></template>
    <section data-testid="table-manage">
      <form class="form" data-testid="table-form" @submit.prevent="submit">
        <h2>{{ isEditing ? '테이블 수정' : '테이블 생성' }}</h2>
        <label>
          테이블 번호
          <input v-model="formNumber" data-testid="table-number-input" />
        </label>
        <label>
          비밀번호 {{ isEditing ? '(변경 시에만 입력)' : '' }}
          <input v-model="formPassword" type="password" data-testid="table-password-input" />
        </label>
        <div class="actions">
          <button type="submit" :disabled="!canSubmit" data-testid="table-submit">
            {{ isEditing ? '수정' : '생성' }}
          </button>
          <button v-if="isEditing" type="button" data-testid="table-cancel" @click="resetForm">
            취소
          </button>
        </div>
      </form>

      <p
        v-if="feedback"
        :class="['feedback', { error: feedbackError }]"
        data-testid="table-feedback"
      >
        {{ feedback }}
      </p>

      <table class="list" data-testid="table-list">
        <thead>
          <tr><th>ID</th><th>번호</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="t in tables" :key="t.id" :data-testid="`table-row-${t.id}`">
            <td>{{ t.id }}</td>
            <td>{{ t.table_number }}</td>
            <td>
              <button type="button" :data-testid="`table-edit-${t.id}`" @click="startEdit(t)">
                수정
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </AdminLayout>
</template>

<style scoped>
.form { display: flex; flex-direction: column; gap: 10px; max-width: 360px; margin-bottom: 20px; }
.form h2 { font-size: 1.1rem; margin: 0; }
label { display: flex; flex-direction: column; gap: 4px; font-size: .85rem; color: #374151; }
input { padding: 10px; border: 1px solid #d1d5db; border-radius: 6px; }
.actions { display: flex; gap: 8px; }
button { padding: 10px 16px; border: 0; border-radius: 6px; background: #2563eb; color: #fff; cursor: pointer; }
button:disabled { background: #9ca3af; cursor: not-allowed; }
.actions button[type='button'] { background: #6b7280; }
.feedback { color: #059669; }
.feedback.error { color: #dc2626; }
.list { border-collapse: collapse; width: 100%; max-width: 480px; }
.list th, .list td { border: 1px solid #e5e7eb; padding: 8px 12px; text-align: left; }
</style>
