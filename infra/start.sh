#!/bin/bash
# GraphOps Infrastructure Startup Script
# Usage: bash /ai/GraphOps/infra/start.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== GraphOps Infrastructure Startup ==="
echo "Project: $PROJECT_DIR"

# Create data directories
echo "Creating data directories..."
mkdir -p "$PROJECT_DIR/docker-data/nebula/meta"
mkdir -p "$PROJECT_DIR/docker-data/nebula/storage"
mkdir -p "$PROJECT_DIR/docker-data/nebula/meta-logs"
mkdir -p "$PROJECT_DIR/docker-data/nebula/storage-logs"
mkdir -p "$PROJECT_DIR/docker-data/nebula/graphd-logs"
mkdir -p "$PROJECT_DIR/docker-data/qdrant"
mkdir -p "$PROJECT_DIR/docker-data/redis"

# Start services
echo "Starting Docker services..."
cd "$SCRIPT_DIR"
docker compose up -d

# Wait for graphd to respond (it depends on metad, not storaged)
echo "Waiting for NebulaGraph graphd to become ready..."
for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:19669/status > /dev/null 2>&1; then
        echo "  graphd is ready!"
        break
    fi
    echo "  Waiting... ($((i*5))s)"
    sleep 5
done

# Register storage hosts (required for storaged to become healthy)
# This is idempotent — safe to run multiple times
echo "Registering storage hosts with NebulaGraph..."
docker run --rm --network infra_graphops-net vesoft/nebula-console:v3.8.0 \
  -addr nebula-graphd -port 9669 -u root -p nebula \
  -e 'ADD HOSTS "nebula-storaged":9779;' 2>&1 || true

# Wait for storaged to become healthy after ADD HOSTS
echo "Waiting for storaged to become healthy..."
for i in $(seq 1 12); do
    if docker inspect --format='{{.State.Health.Status}}' graphops-storaged 2>/dev/null | grep -q "healthy"; then
        echo "  storaged is healthy!"
        break
    fi
    echo "  Waiting... ($((i*5))s)"
    sleep 5
done

echo ""
echo "=== Service Status ==="
docker compose ps

echo ""
echo "=== Connection Info ==="
echo "  NebulaGraph graphd:   127.0.0.1:9669"
echo "  NebulaGraph Studio:   http://127.0.0.1:9788"
echo "  Qdrant:               http://127.0.0.1:9333"
echo "  Redis:                127.0.0.1:9379"
echo ""
echo "=== Done ==="
