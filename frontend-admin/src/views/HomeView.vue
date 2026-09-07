<script setup>
// Placeholder landing view for the admin shell. U4 replaces with the
// real-time dashboard (US-A2); U1 adds login/redirect.
import AdminLayout from '../layouts/AdminLayout.vue'
</script>

<template>
  <AdminLayout>
    <template #header><strong>홈</strong></template>
    <section data-testid="home-placeholder">
      <h1>관리자 콘솔</h1>
      <p>공통 앱 셸(U0)입니다. 각 유닛이 로그인/대시보드/메뉴/이력 화면을 연결합니다.</p>
    </section>
  </AdminLayout>
</template>
