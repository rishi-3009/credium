#!/usr/bin/env bash
# Demo rules:
#   Quit Qwen first: pgrep -a llama and pgrep -a lmstudio must print nothing.
#   Check free -h: at least 10 GB "available".
#   Find the LAN IP with hostname -I (take the first address).
#   Run LAN_IP=<ip> ./ops/run_demo.sh when Rishi needs to view.
#   Reset between takes: curl -X POST http://127.0.0.1:8000/api/reset (or re-run the script).

set -euo pipefail

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$HOME/credium-venv/bin/python"
export PATH="$PATH:/home/ayaan/.config/.foundry/bin"
LOGS="$HOME/credium-logs"
LAN_IP="${LAN_IP:-127.0.0.1}"

cd "$ROOT"

# ---------------------------------------------------------------------------
# STEP 1: Stop old processes
# ---------------------------------------------------------------------------
echo "STEP 1: stopping old processes"
pkill -f "anvil --chain-id 31337" || true
pkill -f "anvil --chain-id 31338" || true
pkill -f "uvicorn api.main:app" || true
sleep 1

# ---------------------------------------------------------------------------
# STEP 2: Start both anvils in the background
# ---------------------------------------------------------------------------
echo "STEP 2: starting both anvils"
mkdir -p "$LOGS"
nohup anvil --chain-id 31337 --port 8545 --host 127.0.0.1 > "$LOGS/anvil-31337.log" 2>&1 &
nohup anvil --chain-id 31338 --port 8546 --host 127.0.0.1 > "$LOGS/anvil-31338.log" 2>&1 &

# ---------------------------------------------------------------------------
# STEP 3: Wait for both RPCs to be ready
# ---------------------------------------------------------------------------
echo "STEP 3: waiting for RPC readiness"
wait_rpc() {
    local port=$1
    local expected_chain=$2
    local url="http://127.0.0.1:${port}"
    for i in $(seq 1 30); do
        if cast chain-id --rpc-url "$url" 2>/dev/null | grep -q "^${expected_chain}$"; then
            return 0
        fi
        sleep 1
    done
    echo "ERROR: chain ${expected_chain} on port ${port} not ready after 30s" >&2
    exit 1
}

wait_rpc 8545 31337
wait_rpc 8546 31338

# ---------------------------------------------------------------------------
# STEP 4: Deploy
# ---------------------------------------------------------------------------
echo "STEP 4: deploying contracts"
"$PY" contracts/deploy.py --deployments contracts/deployments.json

# ---------------------------------------------------------------------------
# STEP 5: Generate bills if missing, then seed
# ---------------------------------------------------------------------------
echo "STEP 5: generating bills (if missing) and seeding"
if [ ! -f "sim/fixtures/bills.json" ]; then
    "$PY" -m sim.gen_bills --write sim/fixtures/bills.json
fi
"$PY" -m sim.seed_demo --deployments contracts/deployments.json

# ---------------------------------------------------------------------------
# STEP 6: Start the API
# ---------------------------------------------------------------------------
echo "READY: open http://127.0.0.1:8000 (or http://${LAN_IP}:8000)"
exec "$PY" -m uvicorn api.main:app --host "${LAN_IP}" --port 8000
