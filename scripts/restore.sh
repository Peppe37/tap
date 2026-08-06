#!/usr/bin/env bash
# Restores a dump produced by scripts/backup.sh into the running "postgres" compose service.
# DESTRUCTIVE: drops and recreates the target database first, so this overwrites current data.
#
# Usage: ./scripts/restore.sh backups/tap-20260101T030000Z.sql.gz
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

DUMP_FILE="${1:-}"
POSTGRES_USER="${POSTGRES_USER:-tap}"
POSTGRES_DB="${POSTGRES_DB:-tap}"

if [ -z "$DUMP_FILE" ]; then
  echo "usage: $0 <path-to-dump.sql.gz>" >&2
  exit 1
fi
if [ ! -f "$DUMP_FILE" ]; then
  echo "error: no such file: $DUMP_FILE" >&2
  exit 1
fi

echo "This will DROP and recreate database '${POSTGRES_DB}' and overwrite its current data."
read -r -p "Type the database name (${POSTGRES_DB}) to confirm: " confirmation
if [ "$confirmation" != "$POSTGRES_DB" ]; then
  echo "Confirmation did not match, aborting." >&2
  exit 1
fi

echo "Stopping backend/worker/beat so nothing writes during the restore..."
docker compose stop backend worker beat

echo "Dropping and recreating ${POSTGRES_DB}..."
docker compose exec -T postgres psql -U "$POSTGRES_USER" -d postgres \
  -c "DROP DATABASE IF EXISTS \"${POSTGRES_DB}\";" \
  -c "CREATE DATABASE \"${POSTGRES_DB}\" OWNER \"${POSTGRES_USER}\";"

echo "Restoring from ${DUMP_FILE}..."
gunzip -c "$DUMP_FILE" | docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

echo "Restarting backend/worker/beat..."
docker compose start backend worker beat

echo "Done."
