# GraphOps — Development TODO

Tracks milestone progress per PRD v2.2 section 24.

---

## M0: Foundations [COMPLETE]

- [x] Project structure and directory layout
- [x] Python virtual environment + dependencies
- [x] Frontend shell (Next.js + TypeScript + Tailwind)
- [x] `.env` configuration and `.env.template`
- [x] Docker infrastructure (NebulaGraph, Qdrant, Redis, Studio)
- [x] NebulaGraph core schema (6 tags, 4 edge types, 16 indexes)
- [x] Migration runner script
- [x] FastAPI backend with lifespan management
- [x] Service clients (NebulaGraph pool, Qdrant, Redis)
- [x] Domain Schema Registry (YAML loader + validator)
- [x] Ingestion Spec format definition
- [x] UUID v7 ID generator
- [x] Workspace isolation (API prefix `/api/w/{wid}/`)
- [x] Health check endpoint (all services)
- [x] Workspace management endpoints (CRUD)
- [x] Schema query endpoints
- [x] Resolved View Engine (PRD 9.4 algorithm)
- [x] Test suite (30 tests, all passing)
- [x] Documentation (ARCHITECTURE.md, TODO.md, README)

---

## M1: Data Ingestion Engine [COMPLETE]

- [x] Graph data access layer (`graph_ops.py` — nGQL CRUD for all vertex/edge types)
- [x] Dual-hash engine (`hashing.py` — raw_hash + normalized_hash + assertion key builders)
- [x] Excel parser (`excel_parser.py` — openpyxl, column mapping, staged rows)
- [x] Ingestion engine (`ingestion_engine.py` — full pipeline with change detection)
  - [x] Entity creation/upsert (deduplicate by workspace + type + primary_key)
  - [x] Assertion key computation (relationships + properties)
  - [x] Dual-hash change detection (strict vs normalized mode)
  - [x] PropertyValue vertex creation + HAS_PROPERTY assertions
  - [x] Relationship assertion creation + ASSERTED_REL edges
  - [x] Disappearance detection (close assertions not seen in re-import)
  - [x] ChangeEvent creation (one per import run, CREATED/CLOSED edges)
  - [x] ImportRun tracking with stats
- [x] Spec loader (`spec_loader.py` — loads YAML ingestion specs)
- [x] Excel file upload endpoint (`POST /api/w/{wid}/imports`)
- [x] Import listing and status endpoints (`GET /imports`, `GET /imports/{id}`)
- [x] Import diff endpoint (`GET /imports/{id}/diff`)
- [x] Entity search endpoint (`GET /api/w/{wid}/entities/search`)
- [x] Entity detail endpoint with resolved view (`GET /api/w/{wid}/entities/{id}`)
- [x] Source authority management (`upsert_source`, `get_source_authority_map`)
- [x] API response models (ImportCreateResponse, EntityDetailResponse, etc.)
- [x] Test suite (116 tests, all passing)
- [x] E2E testing with live NebulaGraph — import, search, entity detail all verified
- [x] Bugfixes discovered during E2E: NULL handling (`_is_null`), datetime conversion (`_to_dt`), edge traversal direction, `desc` reserved word
- [x] Test ingestion spec (`specs/test_items.yaml`) + sample Excel verified
- [ ] Background job queue (Redis + RQ) — deferred, synchronous-first

---

## M2: Query Engine + Graph Explorer UI [PENDING]

*Note: Entity search + detail endpoints were built in M1. M2 focuses on
advanced graph queries and the frontend UI.*

- [x] Entity search endpoint (by type, primary_key, display_name) — done in M1
- [x] Entity detail endpoint (resolved view of all properties) — done in M1
- [ ] Neighbor expansion endpoint (with depth control)
- [ ] Path query endpoint (shortest path between entities)
- [ ] Impact analysis endpoint (downstream dependency traversal)
- [ ] `view_mode` parameter support (resolved vs all_claims)
- [ ] Temporal query support (`at_time` parameter)
- [ ] Qdrant collection setup for entity embeddings
- [ ] Embedding generation via Ollama
- [ ] Semantic search endpoint
- [ ] Frontend: Graph canvas (D3.js or similar)
- [ ] Frontend: Entity detail panel
- [ ] Frontend: Search bar with type-ahead
- [ ] Frontend: Time slider for temporal queries
- [ ] Frontend: Workspace selector

---

## M3: LLM Integration + Conversational Interface [PENDING]

- [ ] Ollama integration (local LLM tool interface)
- [ ] Cloud LLM API support (optional)
- [ ] Tool definitions for LLM (search, expand, analyze)
- [ ] Conversational query endpoint
- [ ] Context window management
- [ ] LLM-assisted entity extraction from unstructured text
- [ ] Frontend: Chat panel
- [ ] Frontend: Tool execution visualization

---

## M4: Scenarios + Conflict Resolution [PENDING]

- [ ] Scenario CRUD endpoints
- [ ] Scenario-scoped assertion creation
- [ ] Scenario comparison (base vs scenario resolved views)
- [ ] Conflict detection endpoint
- [ ] Conflict resolution UI
- [ ] Manual override assertion creation
- [ ] Scenario merge/promote to base
- [ ] Frontend: Scenario selector
- [ ] Frontend: Conflict resolution panel
- [ ] Frontend: Side-by-side comparison view

---

## M5: Production Hardening [PENDING]

- [ ] Authentication and authorization
- [ ] Rate limiting
- [ ] Audit logging
- [ ] Performance optimization (query caching, batch operations)
- [ ] Monitoring and alerting
- [ ] Backup and restore procedures
- [ ] API documentation polish
- [ ] End-to-end integration tests
- [ ] Load testing
- [ ] Deployment documentation
