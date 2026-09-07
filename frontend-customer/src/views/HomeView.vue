<script setup>
// Placeholder landing view for the shell. U2 replaces the default route
// with the menu screen (default screen per US-C2).
import CustomerLayout from '../layouts/CustomerLayout.vue'
</script>

<template>
  <CustomerLayout>
    <section data-testid="home-placeholder">
      <h1>테이블오더 · 고객</h1>
      <p>공통 앱 셸(U0)입니다. 각 유닛이 메뉴/장바구니/주문 화면을 여기에 연결합니다.</p>
    </section>
  </CustomerLayout>
</template>
