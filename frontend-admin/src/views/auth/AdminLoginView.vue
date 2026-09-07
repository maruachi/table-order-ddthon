<script setup>
// Admin login screen (US-A1). Store code + username + password.
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { adminLogin } from '../../api/auth'

const router = useRouter()
const authStore = useAuthStore()

const storeCode = ref('')
const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

// BR-U1-15: all three fields non-blank to enable submit.
const canSubmit = computed(
  () =>
    !loading.value &&
    storeCode.value.trim() &&
    username.value.trim() &&
    password.value.trim(),
)

async function submit() {
  if (!canSubmit.value) return
  loading.value = true
  errorMessage.value = ''
  try {
    const { data } = await adminLogin(
      storeCode.value.trim(),
      username.value.trim(),
      password.value,
    )
    authStore.login(data.access_token)
    router.push('/')
  } catch (err) {
    const detail = err?.response?.data?.detail || ''
    // BR-U1-8: do not reveal store/account existence.
    if (detail.includes('too many')) {
      errorMessage.value = '로그인 시도가 제한되었습니다. 잠시 후 다시 시도하세요.'
    } else {
      errorMessage.value = '아이디 또는 비밀번호가 올바르지 않습니다.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrap">
    <form class="login-card" data-testid="admin-login-form" @submit.prevent="submit">
      <h1>관리자 로그인</h1>
      <label>
        매장 코드
        <input v-model="storeCode" data-testid="login-store-code" autocomplete="off" />
      </label>
      <label>
        아이디
        <input v-model="username" data-testid="login-username" autocomplete="username" />
      </label>
      <label>
        비밀번호
        <input
          v-model="password"
          type="password"
          data-testid="login-password"
          autocomplete="current-password"
        />
      </label>
      <p v-if="errorMessage" class="error" data-testid="login-error">{{ errorMessage }}</p>
      <button type="submit" :disabled="!canSubmit" data-testid="login-submit">
        {{ loading ? '로그인 중…' : '로그인' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.login-wrap { display: flex; justify-content: center; align-items: center; height: 100vh; background: #f3f4f6; }
.login-card { display: flex; flex-direction: column; gap: 12px; width: 320px; padding: 28px; background: #fff; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,.08); }
.login-card h1 { font-size: 1.25rem; margin: 0 0 8px; }
label { display: flex; flex-direction: column; gap: 4px; font-size: .85rem; color: #374151; }
input { padding: 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 1rem; }
button { margin-top: 8px; padding: 12px; border: 0; border-radius: 6px; background: #2563eb; color: #fff; font-size: 1rem; cursor: pointer; }
button:disabled { background: #9ca3af; cursor: not-allowed; }
.error { color: #dc2626; font-size: .85rem; margin: 0; }
</style>
