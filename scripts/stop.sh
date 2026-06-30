#!/usr/bin/env bash
set -euo pipefail

echo "Stopping containers..."
if command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD="docker-compose"
else
  COMPOSE_CMD="docker compose"
fi

$COMPOSE_CMD down

echo "Stopped."
