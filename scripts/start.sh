#!/usr/bin/env bash
set -euo pipefail

echo "Building and starting containers..."
if command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD="docker-compose"
else
  COMPOSE_CMD="docker compose"
fi

$COMPOSE_CMD up -d --build

echo "Started. Service should be available at http://localhost:8000"
