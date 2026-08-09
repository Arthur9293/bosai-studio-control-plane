#!/usr/bin/env sh
set -eu
: "${GRAFANA_URL:?GRAFANA_URL is required}"
: "${GRAFANA_SERVICE_ACCOUNT_TOKEN:?GRAFANA_SERVICE_ACCOUNT_TOKEN is required}"

MCP_GRAFANA_IMAGE="${MCP_GRAFANA_IMAGE:-grafana/mcp-grafana:1.0.0}"
exec docker run --rm \
  -p 127.0.0.1:8000:8000 \
  -e GRAFANA_URL \
  -e GRAFANA_SERVICE_ACCOUNT_TOKEN \
  "$MCP_GRAFANA_IMAGE" \
  -t streamable-http \
  --disable-write \
  --metrics
