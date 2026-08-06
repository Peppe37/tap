#!/usr/bin/env bash
# Dumps the tap Postgres database from the running "postgres" compose service to a timestamped,
# gzip-compressed file, and prunes dumps older than $TAP_BACKUP_RETENTION_DAYS (default 14).
#
# Usage: ./scripts/backup.sh [output-directory]
#   (defaults to ./backups, relative to the repo root)
#
# Run it from a cron job / systemd timer on the host for real automation, e.g.:
#   0 3 * * * cd /path/to/tap && ./scripts/backup.sh >> backups/backup.log 2>&1
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

OUTPUT_DIR="${1:-backups}"
RETENTION_DAYS="${TAP_BACKUP_RETENTION_DAYS:-14}"
POSTGRES_USER="${POSTGRES_USER:-tap}"
POSTGRES_DB="${POSTGRES_DB:-tap}"

mkdir -p "$OUTPUT_DIR"

if ! docker compose ps postgres --status running --format json | grep -q .; then
  echo "error: the postgres service isn't running (docker compose up -d postgres first)" >&2
  exit 1
fi

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
dump_file="$OUTPUT_DIR/tap-${timestamp}.sql.gz"

echo "Dumping ${POSTGRES_DB} (user ${POSTGRES_USER}) to ${dump_file}..."
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" | gzip > "$dump_file"
echo "Done: $(du -h "$dump_file" | cut -f1) written."

if [ "$RETENTION_DAYS" -gt 0 ]; then
  deleted=$(find "$OUTPUT_DIR" -name 'tap-*.sql.gz' -mtime "+${RETENTION_DAYS}" -print -delete | wc -l | tr -d ' ')
  if [ "$deleted" -gt 0 ]; then
    echo "Pruned ${deleted} backup(s) older than ${RETENTION_DAYS} days."
  fi
fi
