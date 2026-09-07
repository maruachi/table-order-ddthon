<script setup>
// Tablet setup screen (US-C1): one-time table login. Touch-friendly (NFR-6).
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { tableLogin } from '../../api/auth'

const router = useRouter()
const authStore = useAuthStore()

const storeCode = ref('')
const tableNumber = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

const canSubmit = computed(
  () =>
    !loading.value &&
    storeCode.value.trim() &&
    tableNumber.value.trim() &&
    password.value.trim(),
)

async function submit() {
  if (!canSubmit.value) return
  loading.value = true
  errorMessage.value = ''
  try {
    const { data } = await tableLogin(
      storeCode.value.trim(),
      tableNumber.value.trim(),
      password.value,
    )
    // Only persist token on success (BR-U1-14).
    authStore.login(data.access_token)
    router.push('/menu')
  } catch {
    // Failure: do not store any token; show a generic message (BR-U1-8/14).
    errorMessage.value = '매장 코드, 테이블 번호 또는 비밀번호가 올바르지 않습니다.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="setup-wrap">
    <form class="setup-card" data-testid="setup-form" @submit.prevent="submit">
      <h1>태블릿 초기 설정</h1>
      <label>
        매장 코드
        <input v-model="storeCode" data-testid="setup-store-code" autocomplete="off" />
      </label>
      <label>
        테이블 번호
        <input v-model="tableNumber" data-testid="setup-table-number" autocomplete="off" />
      </label>
      <label>
        비밀번호
        <input
          v-model="password"
          type="password"
          data-testid="setup-password"
          autocomplete="off"
        />
      </label>
      <p v-if="errorMessage" class="error" data-testid="setup-error">{{ errorMessage }}</p>
      <button type="submit" :disabled="!canSubmit" data-testid="setup-submit">
        {{ loading ? '설정 중…' : '설정 완료' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.setup-wrap { display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 24px; background: #f3f4f6; }
.setup-card { display: flex; flex-direction: column; gap: 16px; width: 100%; max-width: 420px; padding: 32px; background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,.08); }
.setup-card h1 { font-size: 1.4rem; margin: 0 0 8px; }
label { display: flex; flex-direction: column; gap: 6px; font-size: 1rem; color: #374151; }
input { padding: 14px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 1.1rem; min-height: 44px; }
button { margin-top: 8px; padding: 16px; min-height: 52px; border: 0; border-radius: 8px; background: #2563eb; color: #fff; font-size: 1.1rem; cursor: pointer; }
button:disabled { background: #9ca3af; cursor: not-allowed; }
.error { color: #dc2626; font-size: .95rem; margin: 0; }
</style>
