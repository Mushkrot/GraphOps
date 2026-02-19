#!/bin/bash
# Run a NebulaGraph nGQL migration script
# Usage: ./run_migration.sh <migration_file.ngql>
#
# Example: ./run_migration.sh 001_core_schema.ngql

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MIGRATION_FILE="${1:?Usage: $0 <migration_file.ngql>}"

if [ ! -f "$SCRIPT_DIR/$MIGRATION_FILE" ]; then
    echo "Error: Migration file not found: $SCRIPT_DIR/$MIGRATION_FILE"
    exit 1
fi

echo "Running migration: $MIGRATION_FILE"
docker run --rm --network infra_graphops-net \
  -v "$SCRIPT_DIR/$MIGRATION_FILE:/tmp/migration.ngql" \
  vesoft/nebula-console:v3.8.0 \
  -addr nebula-graphd -port 9669 -u root -p nebula \
  -f /tmp/migration.ngql

echo "Migration complete: $MIGRATION_FILE"
