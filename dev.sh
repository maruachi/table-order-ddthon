#!/usr/bin/env bash
#
# 테이블오더 로컬 개발 실행 스크립트
#
# 사용법:
#   ./dev.sh start     세 개 서비스(백엔드/고객/관리자) 모두 시작
#   ./dev.sh stop      모두 종료
#   ./dev.sh restart   재시작
#   ./dev.sh status     실행 상태 확인
#   ./dev.sh logs [backend|customer|admin]   로그 실시간 보기(Ctrl+C로 나가기)
#   ./dev.sh seed      샘플 데이터 재시드
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$ROOT/.dev"
mkdir -p "$RUN_DIR"

# 서비스 정의: 이름|디렉터리|포트
SERVICES=(
  "backend|$ROOT/backend|8000"
  "customer|$ROOT/frontend-customer|5173"
  "admin|$ROOT/frontend-admin|5174"
)

# --- 유틸 ---------------------------------------------------------------

svc_dir()  { case "$1" in backend) echo "$ROOT/backend";; customer) echo "$ROOT/frontend-customer";; admin) echo "$ROOT/frontend-admin";; esac; }
svc_port() { case "$1" in backend) echo 8000;; customer) echo 5173;; admin) echo 5174;; esac; }
pid_file() { echo "$RUN_DIR/$1.pid"; }
log_file() { echo "$RUN_DIR/$1.log"; }

is_running() {
  local pf; pf="$(pid_file "$1")"
  [[ -f "$pf" ]] && kill -0 "$(cat "$pf")" 2>/dev/null
}

# --- 백엔드 최초 세팅 ---------------------------------------------------

ensure_backend() {
  if [[ ! -d "$ROOT/backend/.venv" ]]; then
    echo "[backend] .venv 없음 → 생성 및 의존성 설치"
    python3.11 -m venv "$ROOT/backend/.venv"
    "$ROOT/backend/.venv/bin/pip" install -q -r "$ROOT/backend/requirements.txt"
  fi
  if [[ ! -f "$ROOT/backend/table_order.db" ]]; then
    echo "[backend] DB 없음 → 시드 실행"
    (cd "$ROOT/backend" && "$ROOT/backend/.venv/bin/python" -m seeds.seed)
  fi
}

ensure_frontend() {
  local dir="$1"
  if [[ ! -d "$dir/node_modules" ]]; then
    echo "[$(basename "$dir")] node_modules 없음 → npm install"
    (cd "$dir" && npm install)
  fi
}

# --- 시작/종료 개별 ------------------------------------------------------

start_one() {
  local name="$1" dir port
  dir="$(svc_dir "$name")"; port="$(svc_port "$name")"

  if is_running "$name"; then
    echo "[$name] 이미 실행 중 (PID $(cat "$(pid_file "$name")"))"
    return
  fi

  local cmd
  case "$name" in
    backend)
      ensure_backend
      cmd=("$dir/.venv/bin/uvicorn" "app.main:app" "--reload" "--port" "$port")
      ;;
    customer|admin)
      ensure_frontend "$dir"
      cmd=(npm run dev)
      ;;
  esac

  echo "[$name] 시작 → http://localhost:$port"
  ( cd "$dir" && exec "${cmd[@]}" ) >"$(log_file "$name")" 2>&1 &
  echo $! >"$(pid_file "$name")"
}

stop_one() {
  local name="$1" pf; pf="$(pid_file "$name")"
  if is_running "$name"; then
    local pid; pid="$(cat "$pf")"
    echo "[$name] 종료 (PID $pid)"
    # 프로세스 그룹 전체 종료(uvicorn reloader/vite 자식 포함)
    kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
    sleep 1
    kill -9 -- "-$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null || true
  else
    echo "[$name] 실행 중 아님"
  fi
  rm -f "$pf"
}

# --- 명령 ---------------------------------------------------------------

cmd_start()  { for s in backend customer admin; do start_one "$s"; done; echo; cmd_status; }
cmd_stop()   { for s in backend customer admin; do stop_one "$s"; done; }
cmd_status() {
  echo "서비스 상태:"
  for s in backend customer admin; do
    if is_running "$s"; then
      printf "  %-9s ● 실행중  PID %-7s http://localhost:%s\n" "$s" "$(cat "$(pid_file "$s")")" "$(svc_port "$s")"
    else
      printf "  %-9s ○ 정지\n" "$s"
    fi
  done
  echo
  echo "  백엔드 API 문서: http://localhost:8000/docs"
}
cmd_logs() {
  local name="${1:-}"
  if [[ -z "$name" ]]; then
    tail -n 20 -F "$RUN_DIR"/*.log
  else
    tail -n 50 -F "$(log_file "$name")"
  fi
}
cmd_seed() {
  ensure_backend
  (cd "$ROOT/backend" && "$ROOT/backend/.venv/bin/python" -m seeds.seed)
}

case "${1:-}" in
  start)   cmd_start ;;
  stop)    cmd_stop ;;
  restart) cmd_stop; sleep 1; cmd_start ;;
  status)  cmd_status ;;
  logs)    cmd_logs "${2:-}" ;;
  seed)    cmd_seed ;;
  *)
    echo "사용법: ./dev.sh {start|stop|restart|status|logs [backend|customer|admin]|seed}"
    exit 1
    ;;
esac
