#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Cleanup: deregister the runner from GitHub on container shutdown so we don't
# leave ghost runners behind.
# ---------------------------------------------------------------------------
cleanup() {
    echo "[watchdog] Caught signal — deregistering runner..."
    ./config.sh remove --token "${RUNNER_TOKEN}" || true
}
trap cleanup SIGTERM SIGINT EXIT

# ---------------------------------------------------------------------------
# Configure the runner (unattended, ephemeral-friendly)
# ---------------------------------------------------------------------------
./config.sh \
    --url "${REPO_URL}" \
    --token "${RUNNER_TOKEN}" \
    --unattended \
    --name "runner-$(hostname)" \
    --labels "docker,watchdog-managed" \
    --work _work \
    --replace

echo "[watchdog] Runner configured — starting..."

# ---------------------------------------------------------------------------
# Start the runner (exec replaces this shell so signals propagate correctly)
# ---------------------------------------------------------------------------
exec ./run.sh
