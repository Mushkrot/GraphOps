# GraphOps Intelligence Platform

Universal, domain-agnostic platform for structuring, analyzing, and reasoning about complex multi-layered dependency data using a temporal graph database.

## Key Features

- **Temporal graph storage** — every fact is an evidence-backed assertion with validity intervals
- **Multi-source conflict resolution** — automated winner selection via authority, recency, confidence
- **Domain-agnostic** — define any domain via YAML schemas (telecom, supply chain, etc.)
- **What-if scenarios** — overlay assertions without modifying the base graph
- **Workspace isolation** — multiple independent projects in one deployment
- **Data ingestion** — Excel files mapped to graph entities via declarative YAML specs
- **Dual-hash change detection** — re-imports detect new, changed, unchanged, and disappeared data

## Quick Start

```bash
# Start infrastructure (NebulaGraph, Qdrant, Redis)
bash infra/start.sh

# Run graph schema migration (first time)
bash migrations/run_migration.sh migrations/001_core_schema.ngql

# Start backend
source .venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 9200

# Verify
curl http://localhost:9200/api/health
```

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md) — service map, data model, ingestion pipeline, project structure
- [Development TODO](docs/TODO.md) — milestone progress tracker
- [Product Requirements](docs/PRD_v2.2.md) — full PRD v2.2
- [OpenAPI Docs](http://localhost:9200/docs) — interactive API documentation (when backend is running)

## Current Status: M1 (Data Ingestion Engine) Complete

**M0 (Foundations):** Docker infrastructure, NebulaGraph schema (6 tags, 4 edges, 16 indexes), FastAPI backend, schema registry, resolved view engine.

**M1 (Data Ingestion):** Excel upload + parsing, dual-hash change detection, entity/assertion/property graph writing, import management endpoints, entity search + detail with resolved view. 116 tests passing.

**Next:** M2 (Query Engine + Graph Explorer UI) — neighbor expansion, path queries, impact analysis, frontend graph canvas.
