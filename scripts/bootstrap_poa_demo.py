#!/usr/bin/env python3
"""One-click bootstrap for the DevLeChain PoA demo.

This script performs the full Phase 0 workflow automatically:
  1. Generates the PoA genesis file (if missing) and runs `geth init`.
  2. Renames the old PoW contract artifact to keep historic data.
  3. Starts a temporary PoA node, deploys the multisig contract, assigns roles,
     and funds the reward pool via `deploy_and_init.py`.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from backend.config import get_blockchain_config  # noqa: E402

BACKEND_DIR = PROJECT_ROOT / "backend"
ASSETS_DIR = BACKEND_DIR / "assets"
CONTRACT_PATH = ASSETS_DIR / "deployed_contract.json"
LEGACY_CONTRACT_PATH = ASSETS_DIR / "deployed_contract_pow_legacy.json"
DATA_DIR = Path(get_blockchain_config()["data_dir"])
GENESIS_PATH = DATA_DIR / "genesis_poa.json"
KEYSTORE_DIR = Path("/home/devlechain/ChainData/20000_20000_ethash_0/keystore")
GETH_PATH = Path("/home/devlechain/Applications/Ethereum/geth")
RPC_URL = "http://127.0.0.1:8545"
RPC_PORT = 8545
PASSWORD_FILE = PROJECT_ROOT / ".devlechain_keystore_password"

import setup_poa_chain  # type: ignore  # noqa: E402


def log(msg: str) -> None:
    print(f"ℹ️  {msg}")


def success(msg: str) -> None:
    print(f"✅ {msg}")


def warn(msg: str) -> None:
    print(f"⚠️  {msg}")


def error(msg: str) -> None:
    print(f"❌ {msg}")


def ensure_password_file() -> None:
    if not PASSWORD_FILE.exists():
        PASSWORD_FILE.write_text("devlechain", encoding="utf-8")


def kill_conflicting_processes() -> None:
    """Terminate any process already occupying the RPC port or legacy geth."""

    if shutil.which("lsof"):
        try:
            output = subprocess.check_output(["lsof", "-ti:%d" % RPC_PORT], text=True)
        except subprocess.CalledProcessError:
            output = ""
        for line in output.strip().splitlines():
            if line:
                warn(f"Killing process {line} on port {RPC_PORT}")
                subprocess.run(["kill", "-9", line], check=False)

    if shutil.which("pkill"):
        subprocess.run(["pkill", "-f", str(GETH_PATH)], check=False)


def rename_legacy_contract() -> None:
    if not CONTRACT_PATH.exists():
        return

    try:
        data = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        warn("Existing deployed_contract.json is not valid JSON; moving to legacy file")
        backup_target = LEGACY_CONTRACT_PATH
    else:
        chain_id = data.get("chain_id")
        if chain_id == 20001:
            # Already PoA contract; keep as-is.
            return
        backup_target = LEGACY_CONTRACT_PATH

    if backup_target.exists():
        timestamped = backup_target.with_name(
            f"{backup_target.stem}_{int(time.time())}{backup_target.suffix}"
        )
        backup_target = timestamped

    shutil.move(str(CONTRACT_PATH), str(backup_target))
    warn(f"Moved legacy contract artifact to {backup_target.name}")


def ensure_genesis(force: bool = False) -> None:
    config = get_blockchain_config()
    validator = config["accounts"]["manager_0"]

    if force or not GENESIS_PATH.exists():
        log("Generating Clique genesis (PoA)...")
        setup_poa_chain.generate_genesis(validator, setup_poa_chain.AccountBook.load(), GENESIS_PATH)
        success(f"Genesis written to {GENESIS_PATH}")

    if force or not DATA_DIR.exists() or not (DATA_DIR / "geth" / "chaindata").exists():
        log("Running geth init for PoA data directory...")
        setup_poa_chain.init_chain(GETH_PATH, DATA_DIR, GENESIS_PATH)
        success(f"PoA data directory initialised at {DATA_DIR}")


def start_temp_geth() -> subprocess.Popen:
    kill_conflicting_processes()
    ensure_password_file()
    validator = get_blockchain_config()["accounts"]["manager_0"]
    cmd = [
        str(GETH_PATH),
        "--datadir", str(DATA_DIR),
        "--keystore", str(KEYSTORE_DIR),
        "--networkid", str(get_blockchain_config()["network_id"]),
        "--port", "0",
        "--maxpeers", "0",
        "--http", "--http.addr", "0.0.0.0", "--http.port", str(RPC_PORT),
        "--http.api", "eth,net,web3,personal,clique",
        "--http.corsdomain", "*",
        "--unlock", validator,
        "--password", str(PASSWORD_FILE),
        "--allow-insecure-unlock",
        "--mine",
        "--nodiscover",
    ]
    log("Starting temporary PoA geth node...")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process


def wait_for_rpc(timeout: int = 30) -> None:
    import urllib.request
    import json as _json

    payload = _json.dumps({
        "jsonrpc": "2.0",
        "method": "net_version",
        "params": [],
        "id": 1,
    }).encode("utf-8")

    url = f"http://127.0.0.1:{RPC_PORT}"
    for _ in range(timeout):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}), timeout=1) as resp:
                data = resp.read()
                if data:
                    success("PoA RPC endpoint is ready")
                    return
        except Exception:
            time.sleep(1)
    raise RuntimeError("Timed out waiting for geth RPC to become available")


def stop_process(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


def run_deploy_and_init(force: bool = False) -> None:
    if CONTRACT_PATH.exists() and not force:
        success("PoA contract artifact already present; skipping deployment step")
        return

    log("Deploying multisig contract and initialising roles via deploy_and_init.py")
    subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "deploy_and_init.py")], check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap DevLeChain PoA demo environment")
    parser.add_argument("--force", action="store_true", help="Regenerate genesis, reinitialise data dir, and redeploy contract")
    parser.add_argument("--redeploy", action="store_true", help="Redeploy contract even if an artefact already exists")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not GETH_PATH.exists():
        error(f"geth binary not found at {GETH_PATH}")
        sys.exit(1)

    if not KEYSTORE_DIR.exists():
        error(f"Keystore directory not found: {KEYSTORE_DIR}")
        sys.exit(1)

    rename_legacy_contract()
    ensure_genesis(force=args.force)

    if CONTRACT_PATH.exists() and not args.redeploy and not args.force:
        success("PoA bootstrap already completed. Nothing else to do.")
        return

    proc: Optional[subprocess.Popen] = None
    try:
        proc = start_temp_geth()
        wait_for_rpc()
        run_deploy_and_init(force=args.redeploy or args.force)
        success("PoA contract deployment finished. You can now run ./system.sh start")
    except Exception as exc:
        error(str(exc))
        sys.exit(1)
    finally:
        if proc:
            stop_process(proc)
            log("Temporary geth node stopped")


if __name__ == "__main__":
    main()
