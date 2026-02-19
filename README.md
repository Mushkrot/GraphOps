# GraphOps Intelligence Platform

Universal, domain-agnostic platform for structuring, analyzing, and reasoning about complex multi-layered dependency data using a temporal graph database.

## Key Features

- **Temporal graph storage** — every fact is an evidence-backed assertion with validity intervals
- **Multi-source conflict resolution** — automated winner selection via authority, recency, confidence
- **Domain-agnostic** — define any domain via YAML schemas (telecom, supply chain, etc.)
- **What-if scenarios** — overlay assertions without modifying the base graph
- **Workspace isolation** — multiple independent projects in one deployment

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

- [Architecture Overview](Docs/ARCHITECTURE.md) — service map, data model, project structure
- [Development TODO](Docs/TODO.md) — milestone progress tracker
- [Product Requirements](Docs/PRD_v2.2.md) — full PRD v2.2
- [OpenAPI Docs](http://localhost:9200/docs) — interactive API documentation (when backend is running)

## Current Status: M0 (Foundations) Complete

Infrastructure, core graph schema, backend skeleton, domain schema registry, resolved view engine, and test suite are in place. Ready for M1 (Data Ingestion Engine).
