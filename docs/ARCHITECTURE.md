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

## Data Ingestion Pipeline (M1)

### Import Flow

```
Excel file + Ingestion Spec
        │
        ▼
┌─────────────────────┐
│  1. parse_excel()   │  ← excel_parser.py
│  openpyxl + column  │     Reads sheets, maps columns,
│  mapping → staged   │     produces StagedRow objects
│  rows               │     with entities + relationships
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  2. compute hashes  │  ← hashing.py
│  raw_hash (SHA-256  │     Canonical serialization → hash
│  of cell values)    │     Normalized values → hash
│  normalized_hash    │     Both always stored
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  3. upsert entities │  ← graph_ops.py
│  LOOKUP existing or │     Dedup by (workspace, type, pk)
│  INSERT new Entity  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  4. change detection│  ← ingestion_engine.py
│  Compare hash with  │     strict → raw_hash
│  existing open      │     normalized → normalized_hash
│  assertions         │     Unchanged=skip, Changed=close+new
└─────────┬───────────┘     New=create, Disappeared=close
          │
          ▼
┌─────────────────────┐
│  5. write graph     │  ← graph_ops.py
│  AssertionRecord    │     INSERT vertices + edges
│  PropertyValue      │     ASSERTED_REL: entity→asrt→pv
│  ASSERTED_REL edges │     or entity→asrt→entity
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  6. ChangeEvent     │  ← ingestion_engine.py
│  ONE per import run │     CREATED_ASSERTION edges
│  Stats + links      │     CLOSED_ASSERTION edges
└─────────────────────┘     TRIGGERED_BY → ImportRun
```

### Assertion Key Formats

- **Property:** `{wid}:{entity_type}:{pk}:prop:{property_key}`
- **Relationship:** `{wid}:{type_from}:{pk_from}:{rel_type}:{type_to}:{pk_to}`

### Dual-Hash Change Detection

| Mode | Hash compared | Detects |
|------|---------------|---------|
| `strict` | `raw_hash` | Any cell value change (whitespace, casing, formatting) |
| `normalized` | `normalized_hash` | Only semantically meaningful changes |

Both hashes are always computed and stored regardless of mode.

### Ingestion Spec Format

YAML files in `specs/` directory define how Excel files map to graph entities:

```yaml
spec_name: example
workspace_id: my_workspace
sheets:
  - sheet_name: "Items"
    entities:
      item:
        entity_type: Item
        key_columns: ["item_code"]
        key_template: "{item_code}"
        properties:
          - source_column: "Item Code"
            target_property: item_code
    relationships:
      - relationship_type: BELONGS_TO
        from_entity: item
        to_entity: category
change_detection:
  mode: normalized
```

---

## Project Structure

```
/ai/GraphOps/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── core/
│   │   ├── config.py           # Settings from .env
│   │   ├── graph_client.py     # NebulaGraph connection pool
│   │   ├── graph_ops.py        # nGQL CRUD for all vertex/edge types (M1)
│   │   ├── vector_client.py    # Qdrant client
│   │   ├── redis_client.py     # Redis client
│   │   ├── schema_registry.py  # Domain schema YAML loader
│   │   ├── resolved_view.py    # Resolution algorithm
│   │   ├── ingestion_spec.py   # Ingestion mapping format
│   │   ├── ingestion_engine.py # Import pipeline + change detection (M1)
│   │   ├── excel_parser.py     # Excel parsing + staged rows (M1)
│   │   ├── hashing.py          # Dual-hash + assertion keys (M1)
│   │   ├── spec_loader.py      # Load YAML ingestion specs (M1)
│   │   ├── models.py           # Pydantic models
│   │   └── id_gen.py           # UUID v7 generator
│   └── api/
│       ├── deps.py             # Workspace extraction
│       ├── health.py           # GET /api/health
│       ├── workspaces.py       # Workspace CRUD
│       ├── schemas.py          # Schema queries
│       ├── entities.py         # Entity search + detail (M1)
│       └── imports.py          # Import upload + status + diff (M1)
├── frontend/                   # Next.js app
├── infra/
│   ├── docker-compose.yml      # 6 Docker services
│   └── start.sh                # Infrastructure startup
├── migrations/
│   ├── 001_core_schema.ngql    # NebulaGraph schema
│   └── run_migration.sh        # Migration runner
├── data/
│   └── raw/                    # Uploaded Excel files (gitignored)
├── schemas/                    # Domain schema YAMLs
├── specs/                      # Ingestion mapping specs
├── rules/                      # Propagation rules (M2+)
├── aliases/                    # Alias dictionaries (M2+)
├── tests/
│   ├── test_graph_ops.py       # 23 tests — nGQL generation
│   ├── test_hashing.py         # 25 tests — dual-hash, assertion keys
│   ├── test_excel_parser.py    # 25 tests — Excel parsing
│   ├── test_ingestion_engine.py# 10 tests — change detection pipeline
│   ├── test_spec_loader.py     # 4 tests — spec loading
│   ├── test_resolved_view.py   # 15 tests — resolution algorithm
│   └── test_schema_registry.py # 14 tests — schema validation
└── docs/
    ├── PRD_v2.2.md             # Product Requirements
    ├── TODO.md                 # Milestone progress
    └── ARCHITECTURE.md         # This file
```

---

## API Endpoints (M0 + M1)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Service connectivity check |
| GET | `/api/workspaces` | List all workspaces |
| POST | `/api/workspaces` | Create workspace with schema |
| GET | `/api/workspaces/{id}` | Get workspace details |
| GET | `/api/w/{wid}/schema` | Full domain schema |
| GET | `/api/w/{wid}/schema/entity-types` | List entity types |
| GET | `/api/w/{wid}/schema/relationship-types` | List relationship types |
| GET | `/api/w/{wid}/entities/search` | Search entities (type, primary_key, q) |
| GET | `/api/w/{wid}/entities/{id}` | Entity detail (view_mode, scenario_id) |
| POST | `/api/w/{wid}/imports` | Upload Excel + spec → run import |
| GET | `/api/w/{wid}/imports` | List import runs |
| GET | `/api/w/{wid}/imports/{id}` | Import status + stats |
| GET | `/api/w/{wid}/imports/{id}/diff` | Change diff (created/closed assertions) |

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
- **Reserved words**: `timestamp`, `desc` are reserved — ChangeEvent uses `ts`, YIELD aliases use `descr`
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
- **datetime.utcnow()**: deprecated in Python 3.12+ — use `datetime.now(timezone.utc)` instead
- **python-multipart**: required for FastAPI `UploadFile` / `Form()` — added to requirements.txt
- **openpyxl**: use `data_only=True` when reading to get computed values, not formulas

### M1 Ingestion Notes
- **NebulaGraph NULL filtering**: LOOKUP queries cannot filter `valid_to IS NULL` — workaround: fetch all, filter in Python
- **ASSERTED_REL edge topology**: two edges per assertion: `from_entity→assertion` and `assertion→target` (PropertyValue or Entity)
- **Change detection scope**: disappearance detection finds previous import_run by spec_name, compares assertion_keys
- **Synchronous imports**: M1 runs imports inline in HTTP request. RQ background jobs deferred. `run_import()` function is RQ-ready (takes serializable args, no request context)
- **Spec files**: stored in `specs/` directory, loaded by name (without `.yaml` extension). Files starting with `_` are excluded from `list_specs()` but can be loaded directly
- **Upload storage**: raw files saved to `data/raw/{workspace_id}/` (gitignored)
- **NebulaGraph NULL vs EMPTY**: `is_empty()` only catches `__EMPTY__` (unset), `is_null()` catches explicit NULL — use `_is_null()` helper that checks both
- **NebulaGraph DateTimeWrapper**: `as_datetime()` returns a nebula3 `DateTimeWrapper`, NOT a Python datetime. Must manually construct `datetime()` from `get_year()`, `get_month()`, etc.
- **ASSERTED_REL traversal**: to find assertions for an entity, use forward `GO FROM entity OVER ASSERTED_REL` (not REVERSELY), because edges go entity→assertion

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

# 4. Run all tests (should be 116 passing as of M1 completion)
pytest tests/ -v

# 5. Start backend
uvicorn backend.main:app --host 0.0.0.0 --port 9200

# 6. Verify health
curl http://localhost:9200/api/health
```

### Current Status Summary (end of M1)

**Completed:** M0 (Foundations) + M1 (Data Ingestion Engine)
**Test count:** 116 tests, all passing
**Next milestone:** M2 (Query Engine + Graph Explorer UI)

**M1 delivers:**
- Full data ingestion pipeline: Excel upload → parse → hash → change detect → graph write
- Entity search + detail endpoints with resolved view integration
- Import management (upload, list, status, diff)
- Dual-hash change detection (strict vs normalized modes)
- ChangeEvent tracking (one per import, links to all affected assertions)

**What M1 does NOT yet have (deferred):**
- Background job queue (RQ) — imports run synchronously
- Integration tests with live NebulaGraph — unit tests mock graph_ops
- No sample data imported — needs real ingestion spec + Excel file to test end-to-end

**Key files for M1:**

| File | Purpose |
|------|---------|
| `backend/core/graph_ops.py` | nGQL CRUD for all 6 vertex types + 4 edge types |
| `backend/core/hashing.py` | SHA-256 dual-hash + assertion key builders |
| `backend/core/excel_parser.py` | openpyxl reader → StagedRow dataclasses |
| `backend/core/ingestion_engine.py` | `run_import()` — full pipeline orchestrator |
| `backend/core/spec_loader.py` | Loads YAML specs from `specs/` directory |
| `backend/api/imports.py` | POST upload, GET list/status/diff |
| `backend/api/entities.py` | GET search, GET detail (resolved view) |
| `backend/core/models.py` | All Pydantic models (vertex + API) |

**Dependencies added in M1:** `openpyxl>=3.1.0`, `python-multipart>=0.0.9`
