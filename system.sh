#!/bin/bash

# DevLeChain Demo Orchestrator (PoA-only)
# Launches the Clique chain, FastAPI backend, and Vue frontend for the demo.

set -u
set -o pipefail
IFS=$'\n\t'

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

GETH_PATH="/home/devlechain/Applications/Ethereum/geth"
PASSWORD_FILE="$BASE_DIR/.devlechain_keystore_password"
CHAIN_RPC_PORT=8545

LOG_DIR="$BASE_DIR/.logs"
mkdir -p "$LOG_DIR"

BLOCKCHAIN_LOG="$LOG_DIR/blockchain.log"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

BLOCKCHAIN_PID="$BASE_DIR/.blockchain.pid"
BACKEND_PID="$BASE_DIR/.backend.pid"
FRONTEND_PID="$BASE_DIR/.frontend.pid"

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

kill_by_pid_file() {
  local pid_file="$1"
  local service_name="$2"

  if [ -f "$pid_file" ]; then
    local pid
    pid=$(cat "$pid_file")
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      sleep 1
      if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null || true
      fi
      echo "✅ $service_name stopped (PID: $pid)"
    fi
    rm -f "$pid_file"
  fi
}

ensure_password_file() {
  if [ ! -f "$PASSWORD_FILE" ]; then
    echo "devlechain" > "$PASSWORD_FILE"
  fi
}

load_config_value() {
  local expr="$1"
  python3 - <<PY
from backend.config import get_blockchain_config
cfg = get_blockchain_config()
print(eval("cfg" + "$expr"))
PY
}

get_validator_address() {
  python3 - <<'PY'
from backend.config import get_blockchain_config
cfg = get_blockchain_config()
print(cfg['accounts']['manager_0'])
PY
}

kill_conflicting_processes() {
  # Stop legacy PoW chain or any process occupying the RPC port
  if command_exists lsof; then
    local pids
    pids=$(lsof -ti:"$CHAIN_RPC_PORT" 2>/dev/null || true)
    if [ -n "$pids" ]; then
      echo "⚠️  Port $CHAIN_RPC_PORT already in use. Terminating processes: $pids"
      echo "$pids" | xargs kill -9 2>/dev/null || true
      sleep 1
    fi
  fi

  if pgrep -f "$GETH_PATH" >/dev/null 2>&1; then
    echo "⚠️  Existing geth process detected. Stopping it first."
    pkill -f "$GETH_PATH" 2>/dev/null || true
    sleep 1
  fi
}

check_prerequisites() {
  if [ ! -f "$GETH_PATH" ]; then
    echo "❌ geth binary not found at $GETH_PATH"
    exit 1
  fi

  local data_dir
  data_dir=$(load_config_value "['data_dir']")
  if [ ! -d "$data_dir" ]; then
    echo "❌ PoA data directory missing: $data_dir"
    echo "   Run: python scripts/bootstrap_poa_demo.py"
    exit 1
  fi

  local keystore_dir
  keystore_dir=$(load_config_value "['keystore_dir']")
  if [ ! -d "$keystore_dir" ] || [ -z "$(ls -A "$keystore_dir" 2>/dev/null)" ]; then
    echo "❌ Keystore directory missing or empty: $keystore_dir"
    exit 1
  fi

  local contract_config
  contract_config=$(load_config_value "['contract_config_path']")
  if [ ! -f "$contract_config" ]; then
    echo "❌ Contract config not found: $contract_config"
    echo "   Run: python scripts/bootstrap_poa_demo.py"
    exit 1
  fi
}

start_blockchain() {
  check_prerequisites
  kill_conflicting_processes
  ensure_password_file

  local data_dir
  data_dir=$(load_config_value "['data_dir']")
  local network_id
  network_id=$(load_config_value "['network_id']")
  local keystore_dir
  keystore_dir=$(load_config_value "['keystore_dir']")
  local validator
  validator=$(get_validator_address)

  echo "⚡ Starting DevLeChain PoA chain..."
  echo "   Data Dir: $data_dir"
  echo "   Chain ID: $network_id"
  echo "   Validator: $validator"

  "$GETH_PATH" \
    --datadir "$data_dir" \
    --keystore "$keystore_dir" \
    --networkid "$network_id" \
    --port 0 \
    --maxpeers 0 \
    --http --http.addr "0.0.0.0" --http.port "$CHAIN_RPC_PORT" \
    --http.api "eth,net,web3,personal,clique" \
    --http.corsdomain "*" \
    --unlock "$validator" \
    --password "$PASSWORD_FILE" \
    --allow-insecure-unlock \
    --mine \
    --nodiscover \
    > "$BLOCKCHAIN_LOG" 2>&1 &

  echo $! > "$BLOCKCHAIN_PID"
  sleep 2

  if ps -p "$(cat "$BLOCKCHAIN_PID" 2>/dev/null)" >/dev/null 2>&1; then
    echo "✅ PoA chain running (PID: $(cat "$BLOCKCHAIN_PID"))"
  else
    echo "❌ Failed to launch geth. See $BLOCKCHAIN_LOG"
    exit 1
  fi
}

stop_blockchain() {
  kill_by_pid_file "$BLOCKCHAIN_PID" "Blockchain"
  if pgrep -f "$GETH_PATH" >/dev/null 2>&1; then
    pkill -f "$GETH_PATH" 2>/dev/null || true
    sleep 1
  fi
}

start_backend() {
  echo "🐍 Starting FastAPI backend..."
  ensure_password_file
  python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload \
    > "$BACKEND_LOG" 2>&1 &
  echo $! > "$BACKEND_PID"
  echo "✅ Backend running (PID: $(cat "$BACKEND_PID"))"
}

stop_backend() {
  kill_by_pid_file "$BACKEND_PID" "Backend"
  pkill -f "uvicorn" 2>/dev/null || true
}

start_frontend() {
  echo "🌐 Starting Vue frontend..."
  (cd frontend && npm run dev > "$FRONTEND_LOG" 2>&1 & echo $! > "$FRONTEND_PID")
  echo "✅ Frontend running (PID: $(cat "$FRONTEND_PID"))"
}

stop_frontend() {
  kill_by_pid_file "$FRONTEND_PID" "Frontend"
  pkill -f "vite" 2>/dev/null || true
  pkill -f "npm.*dev" 2>/dev/null || true
}

stop_all() {
  stop_frontend
  stop_backend
  stop_blockchain
  rm -f "$BLOCKCHAIN_LOG" "$BACKEND_LOG" "$FRONTEND_LOG"
}

status_report() {
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📡 Service Status"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  if [ -f "$BLOCKCHAIN_PID" ] && ps -p "$(cat "$BLOCKCHAIN_PID")" >/dev/null 2>&1; then
    echo "✅ Blockchain: running (PID $(cat "$BLOCKCHAIN_PID"))"
  else
    echo "❌ Blockchain: stopped"
  fi

  if [ -f "$BACKEND_PID" ] && ps -p "$(cat "$BACKEND_PID")" >/dev/null 2>&1; then
    echo "✅ Backend: running (PID $(cat "$BACKEND_PID"))"
  else
    echo "❌ Backend: stopped"
  fi

  if [ -f "$FRONTEND_PID" ] && ps -p "$(cat "$FRONTEND_PID")" >/dev/null 2>&1; then
    echo "✅ Frontend: running (PID $(cat "$FRONTEND_PID"))"
  else
    echo "❌ Frontend: stopped"
  fi

  if command_exists curl; then
    local block_hex
    block_hex=$(curl -s -X POST http://127.0.0.1:"$CHAIN_RPC_PORT" -H "Content-Type: application/json" \
      -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' 2>/dev/null |
      sed -n 's/.*"result":"\(.*\)".*/\1/p')
    if [ -n "$block_hex" ]; then
      echo "ℹ️  Latest block: $block_hex"
    fi
  fi
}

show_usage() {
  cat <<USAGE
🔧 DevLeChain Demo Control (PoA)

Usage: $0 {start|stop|restart|status|blockchain}

Commands:
  start       Start blockchain, backend, and frontend
  stop        Stop all services
  restart     Restart all services
  status      Show service status
  blockchain  Control blockchain only (start|stop|restart|status)
USAGE
}

case "${1:-}" in
  start)
    stop_blockchain
    start_blockchain
    start_backend
    start_frontend
    ;;
  stop)
    stop_all
    ;;
  restart)
    stop_all
    sleep 2
    start_blockchain
    start_backend
    start_frontend
    ;;
  status)
    status_report
    ;;
  blockchain)
    sub=${2:-status}
    case "$sub" in
      start)
        stop_blockchain
        start_blockchain
        ;;
      stop)
        stop_blockchain
        ;;
      restart)
        stop_blockchain
        sleep 1
        start_blockchain
        ;;
      status)
        status_report
        ;;
      *)
        show_usage
        exit 1
        ;;
    esac
    ;;
  *)
    show_usage
    exit 1
    ;;
 esac
