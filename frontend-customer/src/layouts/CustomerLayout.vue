<script setup>
// Full-screen tablet layout with a bottom tab bar (NFR-6: touch-friendly).
// Tabs link to unit routes that land later.
const tabs = [
  { to: '/menu', label: '메뉴' },
  { to: '/cart', label: '장바구니' },
  { to: '/history', label: '주문내역' },
]
</script>

<template>
  <div class="customer-layout">
    <main class="content">
      <slot />
    </main>
    <nav class="tabbar" data-testid="customer-tabbar">
      <RouterLink
        v-for="t in tabs"
        :key="t.to"
        :to="t.to"
        class="tab"
        :data-testid="`tab-${t.label}`"
      >
        {{ t.label }}
      </RouterLink>
    </nav>
  </div>
</template>

<style scoped>
.customer-layout { display: flex; flex-direction: column; height: 100vh; }
.content { flex: 1; overflow-y: auto; padding: 16px; }
.tabbar { display: flex; border-top: 1px solid #e5e7eb; }
.tab {
  flex: 1; min-height: 56px; display: flex; align-items: center;
  justify-content: center; text-decoration: none; color: #374151;
}
.tab.router-link-active { color: #2563eb; font-weight: 600; }
</style>
