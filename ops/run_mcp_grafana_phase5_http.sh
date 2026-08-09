#!/usr/bin/env bash
set -euo pipefail

: "${GRAFANA_URL:?GRAFANA_URL must be set}"
: "${GRAFANA_SERVICE_ACCOUNT_TOKEN:?GRAFANA_SERVICE_ACCOUNT_TOKEN must be set}"

CONTAINER_NAME="${BOSAI_MCP_CONTAINER_NAME:-bosai-mcp-grafana-phase5}"
HOST_PORT="${BOSAI_MCP_HOST_PORT:-8010}"
IMAGE="grafana/mcp-grafana:1.0.0"
LOCAL_ORIGIN="http://127.0.0.1:${HOST_PORT}"
LOCALHOST_ORIGIN="http://localhost:${HOST_PORT}"

# Keep the listener local-only and preserve explicit Host/Origin protection.
docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true

docker run -d --rm \
  --name "${CONTAINER_NAME}" \
  -p "127.0.0.1:${HOST_PORT}:8000" \
  -e GRAFANA_URL \
  -e GRAFANA_SERVICE_ACCOUNT_TOKEN \
  "${IMAGE}" \
  -t streamable-http \
  --address :8000 \
  --endpoint-path /mcp \
  --allowed-hosts "localhost:${HOST_PORT},127.0.0.1:${HOST_PORT}" \
  --allowed-origins "${LOCAL_ORIGIN},${LOCALHOST_ORIGIN}" \
  --disable-write >/dev/null

sleep 2

status="$(curl -sS -o /dev/null -w '%{http_code}' "${LOCAL_ORIGIN}/healthz")"
printf 'MCP_HTTP_HEALTH=%s\n' "${status}"
printf 'MCP_HTTP_ENDPOINT=%s/mcp\n' "${LOCAL_ORIGIN}"

if [[ "${status}" != "200" ]]; then
  exit 1
fi
