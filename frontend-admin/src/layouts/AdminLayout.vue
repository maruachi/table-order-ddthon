<script setup>
// Admin console layout: sidebar nav + header. Links to unit routes.
const nav = [
  { to: '/dashboard', label: '실시간 대시보드' },
  { to: '/menu', label: '메뉴 관리' },
  { to: '/tables', label: '테이블 설정' },
  { to: '/history', label: '과거 이력' },
]
</script>

<template>
  <div class="admin-layout">
    <aside class="sidebar" data-testid="admin-sidebar">
      <div class="brand">테이블오더 · 관리자</div>
      <nav>
        <RouterLink
          v-for="n in nav"
          :key="n.to"
          :to="n.to"
          class="nav-item"
          :data-testid="`nav-${n.label}`"
        >
          {{ n.label }}
        </RouterLink>
      </nav>
    </aside>
    <div class="main">
      <header class="header"><slot name="header" /></header>
      <main class="content"><slot /></main>
    </div>
  </div>
</template>

<style scoped>
.admin-layout { display: flex; height: 100vh; }
.sidebar { width: 220px; background: #111827; color: #e5e7eb; padding: 16px; }
.brand { font-weight: 700; margin-bottom: 20px; }
.nav-item { display: block; padding: 10px 8px; color: #cbd5e1; text-decoration: none; border-radius: 6px; }
.nav-item.router-link-active { background: #1f2937; color: #fff; }
.main { flex: 1; display: flex; flex-direction: column; }
.header { min-height: 48px; border-bottom: 1px solid #e5e7eb; padding: 12px 20px; }
.content { flex: 1; overflow-y: auto; padding: 20px; }
</style>
