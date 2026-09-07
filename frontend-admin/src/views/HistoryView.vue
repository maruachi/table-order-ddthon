<script setup>
// U4 과거 이력 (US-A7). closed 세션 스냅샷 주문을 closed_at 역순으로 조회.
// 필터: 테이블, 날짜 범위(기준 closed_at). 페이지네이션(U0 Page[T]).
import { ref, computed, onMounted } from 'vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import { getHistory } from '../api/session'

const items = ref([])
const filters = ref({ tableId: null, dateFrom: null, dateTo: null })
const page = ref({ offset: 0, limit: 20, total: 0 })
const loading = ref(false)

const hasPrev = computed(() => page.value.offset > 0)
const hasNext = computed(() => page.value.offset + page.value.limit < page.value.total)

function formatAmount(n) {
  return Number(n || 0).toLocaleString('ko-KR')
}

function formatDateTime(v) {
  if (!v) return '-'
  const d = new Date(v)
  return Number.isNaN(d.getTime()) ? v : d.toLocaleString('ko-KR')
}

function buildParams() {
  const p = { offset: page.value.offset, limit: page.value.limit }
  if (filters.value.tableId != null && filters.value.tableId !== '') {
    p.table_id = Number(filters.value.tableId)
  }
  if (filters.value.dateFrom) p.date_from = filters.value.dateFrom
  if (filters.value.dateTo) p.date_to = filters.value.dateTo
  return p
}

async function load() {
  loading.value = true
  try {
    const res = await getHistory(buildParams())
    items.value = res?.items || []
    page.value.total = res?.total ?? 0
  } catch {
    items.value = []
    page.value.total = 0
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  page.value.offset = 0
  load()
}

function prevPage() {
  if (!hasPrev.value) return
  page.value.offset = Math.max(0, page.value.offset - page.value.limit)
  load()
}

function nextPage() {
  if (!hasNext.value) return
  page.value.offset += page.value.limit
  load()
}

onMounted(load)
</script>

<template>
  <AdminLayout>
    <template #header><strong>과거 이력</strong></template>

    <section class="history" data-testid="history-view">
      <form class="filters" data-testid="history-filter" @submit.prevent="applyFilters">
        <label>
          <span>테이블</span>
          <input
            v-model="filters.tableId"
            type="number"
            min="1"
            placeholder="전체"
            data-testid="filter-table"
          />
        </label>
        <label>
          <span>시작일</span>
          <input v-model="filters.dateFrom" type="date" data-testid="filter-date-from" />
        </label>
        <label>
          <span>종료일</span>
          <input v-model="filters.dateTo" type="date" data-testid="filter-date-to" />
        </label>
        <button type="submit" class="btn" data-testid="filter-apply">조회</button>
      </form>

      <p v-if="loading" class="muted">불러오는 중...</p>
      <p v-else-if="items.length === 0" class="muted" data-testid="history-empty">
        이력이 없습니다.
      </p>

      <table v-else class="table">
        <thead>
          <tr>
            <th>주문번호</th>
            <th>주문시각</th>
            <th>메뉴</th>
            <th class="num">총액</th>
            <th>이용완료</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in items" :key="row.id ?? `${row.order_no}-${i}`" data-testid="history-row">
            <td>#{{ row.order_no }}</td>
            <td>{{ formatDateTime(row.ordered_at) }}</td>
            <td>
              <ul class="lines">
                <li v-for="(ln, j) in row.lines || []" :key="j">
                  {{ ln.menu_name }} ×{{ ln.quantity }} @{{ formatAmount(ln.unit_price) }}원
                </li>
              </ul>
            </td>
            <td class="num">{{ formatAmount(row.order_amount) }}원</td>
            <td>{{ formatDateTime(row.closed_at) }}</td>
          </tr>
        </tbody>
      </table>

      <div class="pager">
        <button
          class="btn"
          :disabled="!hasPrev"
          data-testid="page-prev"
          @click="prevPage"
        >
          이전
        </button>
        <span class="page-info">
          {{ page.total === 0 ? 0 : page.offset + 1 }}–{{ Math.min(page.offset + page.limit, page.total) }}
          / {{ page.total }}
        </span>
        <button
          class="btn"
          :disabled="!hasNext"
          data-testid="page-next"
          @click="nextPage"
        >
          다음
        </button>
      </div>
    </section>
  </AdminLayout>
</template>

<style scoped>
.history {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.filters {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 12px;
}
.filters label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  color: #374151;
}
.filters input {
  min-height: 44px;
  padding: 0 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
}
.btn {
  min-height: 44px;
  padding: 0 18px;
  border: none;
  border-radius: 8px;
  background: #2563eb;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
.btn:disabled {
  background: #cbd5e1;
  cursor: default;
}
.muted {
  color: #6b7280;
}
.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.table th,
.table td {
  border-bottom: 1px solid #e5e7eb;
  padding: 10px 8px;
  text-align: left;
  vertical-align: top;
}
.table th.num,
.table td.num {
  text-align: right;
  white-space: nowrap;
}
.lines {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.pager {
  display: flex;
  align-items: center;
  gap: 16px;
}
.page-info {
  color: #6b7280;
  font-size: 13px;
}
</style>
