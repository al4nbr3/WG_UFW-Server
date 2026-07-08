#!/usr/bin/env bash
# Deploy and start the WG-home-VPN Status API on the remote server
set -euo pipefail

REMOTE_USER="observa"
REMOTE_HOST="192.168.1.195"
REMOTE_PATH="/opt/WG_UFW-Server"
API_PORT=8800
SSH_KEY="${HOME}/.ssh/cadena_prox"
SSH_CMD="ssh -i ${SSH_KEY}"
RSYNC_CMD="rsync -avz --progress -e 'ssh -i ${SSH_KEY}'"

echo "==> Deploying API files to ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/api/"

${SSH_CMD} "${REMOTE_USER}@${REMOTE_HOST}" \
  "sudo mkdir -p ${REMOTE_PATH}/api/{templates,static} && sudo chown -R ${REMOTE_USER}:${REMOTE_USER} ${REMOTE_PATH}/api"

eval "${RSYNC_CMD}" \
  "$(dirname "$(realpath "$0")")/../api/" \
  "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/api/"

echo "==> Installing Python dependencies"
${SSH_CMD} "${REMOTE_USER}@${REMOTE_HOST}" \
  "cd ${REMOTE_PATH} && ${REMOTE_PATH}/.venv/bin/pip install -r api/requirements.txt -q && echo '  done'"

echo "==> Installing systemd service"
${SSH_CMD} "${REMOTE_USER}@${REMOTE_HOST}" \
  "sudo cp ${REMOTE_PATH}/api/wg-api.service /etc/systemd/system/wg-api.service && sudo systemctl daemon-reload && sudo systemctl enable wg-api.service && sudo systemctl restart wg-api.service"

sleep 2
${SSH_CMD} "${REMOTE_USER}@${REMOTE_HOST}" "sudo systemctl status wg-api.service --no-pager | head -5"

echo ""
echo "==> API deployed!"
echo "    http://${REMOTE_HOST}:${API_PORT}/"
echo "    http://${REMOTE_HOST}:${API_PORT}/docs  (Swagger)"
