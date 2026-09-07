// Realtime order-status store (U4) — US-C6 (고객 상태 실시간).
// Subscribes to the customer SSE stream; server filters by table_id (Q8=A).
//
// 통합 지점: U3 OrderHistoryView(US-C5)가 이 스토어의 statusByOrderNo를 구독해
// 상태 배지를 라이브 갱신한다. U4는 스트림/헬퍼/스토어만 제공한다.
import { defineStore } from 'pinia'
import { openSse } from '../api/sse'

export const useRealtimeStore = defineStore('realtime', {
  state: () => ({
    statusByOrderNo: {}, // order_no -> order_status
    connected: false,
    _es: null,
  }),
  actions: {
    connect() {
      this._es = openSse('/realtime/table/stream', (evt) => this.onEvent(evt))
      this._es.onopen = () => {
        this.connected = true
        // 재연결(Q7=C): 재연결 시 U3의 현재 세션 주문 조회(US-C5)로
        // statusByOrderNo를 재동기화한다(U3 API 사용 — 통합 시 연결).
      }
    },
    onEvent(evt) {
      if (evt.type === 'order.status_changed') {
        const p = evt.payload
        if (p.order_no) this.statusByOrderNo[p.order_no] = p.order_status
      }
    },
    disconnect() {
      this._es?.close()
      this._es = null
      this.connected = false
    },
  },
})
