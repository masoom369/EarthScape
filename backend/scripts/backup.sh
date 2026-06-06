#!/usr/bin/env bash
# Daily MongoDB backup — register as cron: 0 2 * * * /path/to/backup.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"

if [ -f "$ENV_FILE" ]; then
  export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

MONGO_URI="${MONGO_URI:-mongodb://localhost:27017}"
BACKUP_DIR="/backups/$(date +%F)"

mkdir -p "$BACKUP_DIR"
mongodump --uri="$MONGO_URI" --out="$BACKUP_DIR"
echo "Backup completed: $BACKUP_DIR"
