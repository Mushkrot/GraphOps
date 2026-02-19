# GraphOps — Architecture Overview

## Quick Start

```bash
# 1. Start infrastructure
cd /ai/GraphOps
bash infra/start.sh

# 2. Run NebulaGraph migration (first time only)
bash migrations/run_migration.sh migrations/001_core_schema.ngql

# 3. Activate Python environment and start backend
source .venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 9200

# 4. Start frontend (separate terminal)
cd frontend && npm run dev

# 5. Verify
curl http://localhost:9200/api/health
# → {"status":"ok","services":{"nebula":"ok","qdrant":"ok","redis":"ok"}}
```

---

## Service Map

| Service | Port | Purpose |
|---------|------|---------|
| **Backend API** | 9200 | FastAPI — REST endpoints, business logic |
| **Frontend** | 9100 | Next.js — graph explorer UI |
| **NebulaGraph graphd** | 9669 | Graph query engine |
| **NebulaGraph metad** | 9559 | Cluster metadata |
| **NebulaGraph storaged** | 9779 | Graph data storage |
| **NebulaGraph Studio** | 9788 | Web UI for graph inspection |
| **Qdrant** | 9333 | Vector database for semantic search |
| **Redis** | 9379 | Job queue (RQ) and cache |
| **Ollama** | 11434 | Local LLM inference (pre-existing) |

All Docker volumes mount to `/ai/GraphOps/docker-data/`.

---

## Data Model

### Core Vertex Types (NebulaGraph Tags)

```
Entity              — The real-world object (Location, Equipment, etc.)
AssertionRecord     — Evidence-backed claim about an entity or relationship
PropertyValue       — Typed value for entity properties
ChangeEvent         — Causal event tracking (one per import run)
ImportRun           — Metadata about a data import execution
Source              — Data source registration with authority_rank
```

### Edge Types

```
ASSERTED_REL        — Links AssertionRecord to target Entity (for relationships)
TRIGGERED_BY        — Links ChangeEvent to ImportRun
CREATED_ASSERTION   — Links ChangeEvent to newly created AssertionRecords
CLOSED_ASSERTION    — Links ChangeEvent to closed/superseded AssertionRecords
```

### Key Design Principle: Assertions, Not Direct Edges

Relationships between entities are NOT stored as direct edges. Instead:
1. An `AssertionRecord` vertex records the claim (source, time, confidence)
2. An `ASSERTED_REL` edge links the assertion to the target entity
3. The Resolved View Engine picks the winning assertion per relationship

This enables temporal tracking, multi-source conflict resolution, and what-if scenarios.

---

## Workspace Isolation

- Single NebulaGraph space `graphops` shared by all workspaces
- Every vertex carries a `workspace_id` property
- All queries filter by `workspace_id`
- API routes: `/api/w/{wid}/...` extract workspace from URL path
- Schema Registry stores per-workspace domain schemas

---

## Resolution Algorithm (PRD 9.4)

When multiple assertions compete for the same `assertion_key`:

```
1. Temporal filter    → valid_from <= now < valid_to
2. Scenario preference → target scenario_id > base fallback
3. Manual override    → source_type=manual always wins
4. Authority rank     → lowest number wins (rank 1 > rank 2)
5. Recency           → most recent recorded_at
6. Confidence        → highest confidence value
```

Two view modes:
- **Resolved view** (default): single winner per assertion_key
- **All-claims view**: all assertions with `is_winner` annotation

---

## Project Structure

```
/ai/GraphOps/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── core/
│   │   ├── config.py           # Settings from .env
│   │   ├── graph_client.py     # NebulaGraph connection pool
│   │   ├── vector_client.py    # Qdrant client
│   │   ├── redis_client.py     # Redis client
│   │   ├── schema_registry.py  # Domain schema YAML loader
│   │   ├── resolved_view.py    # Resolution algorithm
│   │   ├── ingestion_spec.py   # Ingestion mapping format
│   │   ├── models.py           # Pydantic models
│   │   └── id_gen.py           # UUID v7 generator
│   └── api/
│       ├── deps.py             # Workspace extraction
│       ├── health.py           # GET /api/health
│       ├── workspaces.py       # Workspace CRUD
│       ├── schemas.py          # Schema queries
│       ├── entities.py         # Entity endpoints (M1)
│       └── imports.py          # Import endpoints (M1)
├── frontend/                   # Next.js app
├── infra/
│   ├── docker-compose.yml      # 6 Docker services
│   └── start.sh                # Infrastructure startup
├── migrations/
│   ├── 001_core_schema.ngql    # NebulaGraph schema
│   └── run_migration.sh        # Migration runner
├── schemas/                    # Domain schema YAMLs
├── specs/                      # Ingestion mapping specs
├── rules/                      # Propagation rules (M2+)
├── aliases/                    # Alias dictionaries (M2+)
├── tests/                      # pytest test suite
└── Docs/
    ├── PRD_v2.2.md             # Product Requirements
    ├── TODO.md                 # Milestone progress
    └── ARCHITECTURE.md         # This file
```

---

## API Endpoints (M0)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Service connectivity check |
| GET | `/api/workspaces` | List all workspaces |
| POST | `/api/workspaces` | Create workspace with schema |
| GET | `/api/workspaces/{id}` | Get workspace details |
| GET | `/api/w/{wid}/schema` | Full domain schema |
| GET | `/api/w/{wid}/schema/entity-types` | List entity types |
| GET | `/api/w/{wid}/schema/relationship-types` | List relationship types |
| GET | `/api/w/{wid}/entities/search` | Search entities (M1) |
| GET | `/api/w/{wid}/entities/{id}` | Entity details (M1) |
| GET | `/api/w/{wid}/imports` | List imports (M1) |
| POST | `/api/w/{wid}/imports` | Create import (M1) |

OpenAPI docs: `http://localhost:9200/docs`

---

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Graph DB | NebulaGraph | 3.8.0 |
| Vector DB | Qdrant | 1.12.0 |
| Cache/Queue | Redis | 7.2 |
| Backend | FastAPI + Python | 3.12 |
| Frontend | Next.js + TypeScript | 15.x |
| LLM | Ollama (local) | latest |
| IDs | UUID v7 | — |

---

## Known Issues & Implementation Notes

These are important details discovered during M0 implementation:

### NebulaGraph
- **nGQL comments**: use `#`, not `--` (SQL-style comments cause SyntaxError)
- **nGQL statements**: must be single-line (no multiline statements)
- **Reserved words**: `timestamp` is reserved — ChangeEvent uses `ts` instead
- **Underscore prefix**: `_resolved_at` caused parse issues — renamed to `resolved_at`
- **ADD HOSTS**: requires quoted hostname in v3.8: `ADD HOSTS "nebula-storaged":9779;`
- **Index rebuild**: needs `:sleep 10` after index creation before REBUILD
- **Docker network**: Compose prefixes directory name → network is `infra_graphops-net`
- **VID format**: FIXED_STRING(64), UUID v7 hex (32 chars) + optional prefix

### Docker
- **Qdrant healthcheck**: curl not available in container, using `bash -c 'echo > /dev/tcp/localhost/6333'`
- **graphd depends on metad** (not storaged) to avoid chicken-and-egg with ADD HOSTS
- **storaged** needs ADD HOSTS from graphd before it becomes healthy (handled by `start.sh`)

### Python / FastAPI
- **pydantic-settings**: `.env` has extra vars not in Settings → `"extra": "ignore"` in model_config
- **Git remote**: uses SSH (`git@github.com:Mushkrot/GraphOps.git`), key at `~/.ssh/git`

---

## Resume Checklist (for continuing development)

```bash
# 1. Verify Docker services are running
cd /ai/GraphOps && docker compose -f infra/docker-compose.yml ps

# If not running:
bash infra/start.sh

# 2. Verify NebulaGraph schema exists
docker run --rm --network infra_graphops-net \
  vesoft/nebula-console:v3.8.0 \
  -addr nebula-graphd -port 9669 -u root -p nebula \
  -e 'USE graphops; SHOW TAGS; SHOW EDGES;'

# 3. Activate Python venv
source .venv/bin/activate

# 4. Run tests
pytest tests/ -v

# 5. Start backend
uvicorn backend.main:app --host 0.0.0.0 --port 9200

# 6. Verify health
curl http://localhost:9200/api/health
```
