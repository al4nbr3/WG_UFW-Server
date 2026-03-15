#!/usr/bin/env bash
# Deploy WG_UFW-Server to remote host via rsync over SSH
set -euo pipefail

REMOTE_USER="observa"
REMOTE_HOST="192.168.1.195"
REMOTE_PATH="/opt/WG_UFW-Server"

echo "==> Deploying WG_UFW-Server to ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}"

# Create destination directory on remote (uses -t for sudo TTY)
ssh -t "${REMOTE_USER}@${REMOTE_HOST}" "sudo mkdir -p ${REMOTE_PATH} && sudo chown ${REMOTE_USER}:${REMOTE_USER} ${REMOTE_PATH}"

# Sync project files (exclude secrets, caches, git history)
rsync -avz --progress \
    --exclude='.git' \
    --exclude='.env' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='config/clients/' \
    --exclude='backups/' \
    --exclude='*.key' \
    "$(dirname "$(realpath "$0")")/../" \
    "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/"

echo ""
echo "==> Deploy complete."
echo ""
echo "Next steps on the remote server:"
echo "  ssh ${REMOTE_USER}@${REMOTE_HOST}"
echo "  cd ${REMOTE_PATH}"
echo "  cp .env.example .env && nano .env    # add your ANTHROPIC_API_KEY"
echo "  pip install -r requirements.txt"
echo "  bash scripts/install.sh"
echo "  bash scripts/configure-server.sh"
echo "  bash scripts/ufw-rules.sh"
echo "  bash scripts/start-wg.sh"
