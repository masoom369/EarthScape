#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

MONGO_URI="${MONGO_URI:-mongodb://localhost:27017}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
DATE_DIR="$BACKUP_DIR/$(date +%F)"

mkdir -p "$DATE_DIR"
mongodump --uri="$MONGO_URI" --out="$DATE_DIR"
echo "[backup] completed: $DATE_DIR"