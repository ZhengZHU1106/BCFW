#!/bin/bash

# Reset DevLeChain PoA demo data and archive legacy artefacts.

set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_ROOT="$PROJECT_ROOT/.backups"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"

POA_DATA_DIR="$(python3 - <<'PY'
from backend.config import get_blockchain_config
print(get_blockchain_config()["data_dir"])
PY
)"
GETH_PATH="/home/devlechain/Applications/Ethereum/geth"

DB_FILES=(
  "$PROJECT_ROOT/backend/security_platform.db"
  "$PROJECT_ROOT/backend/database/bcfw.db"
)

CONTRACT_FILES=(
  "$PROJECT_ROOT/backend/assets/deployed_contract.json"
  "$PROJECT_ROOT/backend/assets/deployed_contract_pow_legacy.json"
)

mkdir -p "$BACKUP_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 Resetting DevLeChain PoA demo state"
echo "   Backup directory: $BACKUP_DIR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "⏹️  Stopping running geth instances (if any)"
pkill -f "$GETH_PATH" >/dev/null 2>&1 || true

backup_file() {
  local path="$1"
  if [ -f "$path" ]; then
    mv "$path" "$BACKUP_DIR/$(basename "$path")"
    echo "📦 Archived $(basename "$path")"
  fi
}

for db in "${DB_FILES[@]}"; do
  backup_file "$db"
done

for contract in "${CONTRACT_FILES[@]}"; do
  backup_file "$contract"
done

if [ -d "$POA_DATA_DIR" ]; then
  echo "🧹 Removing PoA chain data directory: $POA_DATA_DIR"
  rm -rf "$POA_DATA_DIR"
fi

echo "✅ Reset complete. Next steps:"
echo "   1) python scripts/bootstrap_poa_demo.py --force"
echo "   2) ./system.sh start"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
