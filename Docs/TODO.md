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

## M1: Data Ingestion Engine [PENDING]

- [ ] Excel file upload endpoint (`POST /api/w/{wid}/imports`)
- [ ] Ingestion spec YAML loader and validator
- [ ] Sheet reader (openpyxl) with column mapping
- [ ] Entity creation/upsert logic
  - [ ] Generate entity VIDs via UUID v7
  - [ ] Deduplicate by primary_key within workspace
- [ ] AssertionRecord creation
  - [ ] Compute assertion_key from entity + relationship + property
  - [ ] Compute raw_hash (canonical row serialization)
  - [ ] Compute normalized_hash (normalized values)
  - [ ] Dual-hash change detection (strict vs normalized mode)
- [ ] PropertyValue vertex creation
- [ ] Relationship assertion creation (ASSERTED_REL edges)
- [ ] ChangeEvent creation (one per import run)
  - [ ] CREATED_ASSERTION / CLOSED_ASSERTION edges
  - [ ] Stats tracking (created, updated, closed, unchanged counts)
- [ ] ImportRun tracking (start, progress, complete/error)
- [ ] Source registration and authority_rank management
- [ ] Re-import logic (detect changes via hash comparison)
- [ ] Background job queue (Redis + RQ)
- [ ] Import status polling endpoint
- [ ] Tests: ingestion pipeline, change detection, re-import

---

## M2: Query Engine + Graph Explorer UI [PENDING]

- [ ] Entity search endpoint (by type, primary_key, display_name)
- [ ] Entity detail endpoint (resolved view of all properties)
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
