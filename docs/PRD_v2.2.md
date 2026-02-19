# PRD — GraphOps Intelligence Platform

**Document status:** Draft v2.2  
**Previous versions:** v1.0 (restaurant-specific POC), v2.0 (universal platform), v2.1 (physical storage model + dual-hash + ChangeEvent + resolved view)  
**Changelog v2.2:** Workspace isolation technical binding (shared space + workspace_id + API prefix); property assertions as evidence-backed HAS_PROPERTY relationships; authority_rank naming fix with explicit ordering; ChangeEvent granularity fixed as decision; raw_hash redefined as canonical row serialization; agent mode guardrails (max calls, timeout, logging, all-claims policy)  
**Primary language:** English  
**Target deployment:** Dedicated Ubuntu Linux server (Docker-first)  
**Licensing goal:** Open-source components only (no paid product licenses). Paid cloud LLM tokens are allowed when needed.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Background & Evolution of the Problem](#2-background--evolution-of-the-problem)
3. [Vision & Platform Philosophy](#3-vision--platform-philosophy)
4. [Problem Statement (General)](#4-problem-statement-general)
5. [Goals, Success Metrics, Non-Goals](#5-goals-success-metrics-non-goals)
6. [Users & Personas](#6-users--personas)
7. [Platform Architecture Principles](#7-platform-architecture-principles)
8. [POC Use Case: Restaurant Network Infrastructure](#8-poc-use-case-restaurant-network-infrastructure)
9. [Core Data Model: Domain-Agnostic Foundation](#9-core-data-model-domain-agnostic-foundation)
10. [Functional Requirements](#10-functional-requirements)
11. [Temporal Versioning & Change Analysis](#11-temporal-versioning--change-analysis)
12. [Scenario Branching (What-If)](#12-scenario-branching-what-if)
13. [Multi-Source Reconciliation & Conflict Resolution](#13-multi-source-reconciliation--conflict-resolution)
14. [Intelligent Analysis Layer](#14-intelligent-analysis-layer)
15. [LLM Integration Design (Strict Grounding)](#15-llm-integration-design-strict-grounding)
16. [API Requirements](#16-api-requirements)
17. [UI/UX Requirements](#17-uiux-requirements)
18. [Proposed Tech Stack & Rationale](#18-proposed-tech-stack--rationale)
19. [System Architecture](#19-system-architecture)
20. [Ingestion Framework & Vibe Coding](#20-ingestion-framework--vibe-coding)
21. [Deployment (Docker-first)](#21-deployment-docker-first)
22. [Non-Functional Requirements](#22-non-functional-requirements)
23. [Testing & Validation](#23-testing--validation)
24. [Milestones](#24-milestones)
25. [Risks & Mitigations](#25-risks--mitigations)
26. [Open Questions](#26-open-questions)
27. [Acceptance Criteria (POC)](#27-acceptance-criteria-poc)

---

## 1. Executive Summary

### What we are building

**GraphOps Intelligence Platform** is a **universal, domain-agnostic** system for structuring, analyzing, and reasoning about complex multi-layered dependency data. It combines a temporal graph database, strict evidence tracking, scenario branching, and an LLM-powered intelligent interface into a single web application.

### Why it matters

Organizations across industries face the same fundamental problem: critical dependency and inventory information is scattered across disconnected sources (spreadsheets, databases, APIs, documents), maintained by separate teams who rarely coordinate. Tracing dependencies, understanding impact, analyzing changes, and predicting failures requires manually assembling people and data — a process that is slow, error-prone, and does not scale.

### How it works

The platform ingests data from diverse sources into a **unified temporal graph** where every fact is an **evidence-backed assertion** with provenance, validity period, confidence level, and scenario context. Users interact with this graph through an intuitive web interface and a natural language "intelligent assistant" that finds information, traces dependency chains, models impact cascades, and explains its reasoning — all strictly grounded in source data, never hallucinating.

### POC approach

To validate the architecture and build the first working version, we use a **real-world use case**: a restaurant chain's network infrastructure inventory and project management data. This use case is representative because it already contains multi-layered dependencies, overlapping projects, data from multiple teams, alias/legacy ID challenges, and temporal change tracking — all the complexity patterns the platform must handle universally.

The system is designed so that **the restaurant domain is a configuration, not a hardcoded architecture**. The same platform can be reconfigured for cloud infrastructure, enterprise networking, supply chain, research knowledge bases, or any other domain with complex interdependencies.

---

## 2. Background & Evolution of the Problem

### 2.1 Initial exploration: World Models (JEPA)

The initiative began from a research interest in **world models** — systems that build internal representations of complex environments and can predict consequences of changes. The JEPA (Joint Embedding Predictive Architecture) family of models was explored as a potential approach to understanding multi-layered dependencies.

### 2.2 Key insight: the problem is structural, not perceptual

JEPA-style architectures are designed for visual/video data — predicting embeddings of masked image or video regions. The actual need is fundamentally different: **reasoning about structured and semi-structured dependency networks described in text and tabular data**.

The core requirements identified:
- Handling **infinitely nested, heterogeneous components** with many-to-many relationships
- **Tracing dependency chains** across multiple layers (physical → virtual → logical → business)
- **Temporal reasoning**: understanding how the system evolves, finding root causes in the past, predicting failures in the future
- **Intelligent querying**: asking questions in natural language and getting answers backed by evidence

### 2.3 Direction: Graph + Time + Evidence + Intelligence

The problem maps naturally to:
- A **graph database** as the structural backbone for dependencies
- A **temporal/versioned model** for change tracking and time-travel
- A **strict evidence layer** linking every assertion to its source
- **Vector search / RAG** for semantic understanding and document access
- An **LLM-assisted interface** that routes questions to deterministic queries and summarizes results without hallucination

### 2.4 From specific to universal

During the design process, it became clear that the restaurant infrastructure use case — while being our immediate, real-world project — represents a **general class of problems**. Any organization dealing with complex, multi-team, multi-source inventories and projects faces identical structural challenges. The platform must therefore be designed as a **universal tool** with domain-specific configurations, not as a restaurant inventory system.

### 2.5 Philosophical extensibility

A longer-term vision includes applying the same platform to **non-deterministic, research-oriented** use cases: connecting concepts across domains, exploring competing interpretations, tracking evolution of ideas over time. The assertion-based model with confidence scores and scenario branching naturally supports this — "hard" engineering facts and "soft" research hypotheses coexist in the same architecture, distinguished by metadata.

---

## 3. Vision & Platform Philosophy

### 3.1 Core principles

1. **Domain-agnostic by design**: The platform defines a universal core model (entities, relationships, assertions, evidence, time). Domain-specific schemas (restaurant inventory, cloud infrastructure, research knowledge) are configurations, not code changes.

2. **Intelligence beyond a database**: The system is not just storage — it is an **analytical partner** that understands context, traces multi-hop dependencies, models cascading effects, detects anomalies, and explains its reasoning.

3. **Evidence is mandatory**: Every assertion in the system must be traceable to its source. The system never presents ungrounded information. This is non-negotiable for both engineering and research use cases.

4. **Time is a first-class dimension**: The system natively understands that facts change — it can show the state at any point in time, compute diffs, trace what changed before a failure, and support "what-if" scenarios.

5. **Code-first / Vibe Coding**: All configuration, schema definition, ingestion mapping, and deployment is managed through code and version control. No required manual UI configuration steps.

6. **Open-source foundation**: No paid product licenses. Cloud LLM API costs are the only variable expense.

### 3.2 What the platform is NOT

- It is **not a CMDB** (though it can serve as one for a specific domain)
- It is **not a monitoring/observability tool** (though it can ingest and correlate monitoring data)
- It is **not a general-purpose LLM chatbot** (the LLM is constrained to graph-grounded reasoning)
- It is **not domain-locked** (the restaurant use case is the first deployment, not the product definition)

---

## 4. Problem Statement (General)

### 4.1 The universal problem

Organizations store critical information about their systems, processes, and dependencies across **many disconnected sources** maintained by **separate teams**. These sources use different formats, naming conventions, update cycles, and levels of detail. Dependencies between components are **multi-hop, many-to-many, multi-layered, and dynamic**.

Answering questions like:
- "What depends on X and what breaks if X fails?"
- "Show the exact dependency chain between A and B"
- "What changed between two points in time and could this explain the incident?"
- "If we make this change, what is the impact across all layers?"
- "Which locations/components/projects share this specific dependency?"
- "Are there anomalies or patterns we're not seeing?"

...currently requires **manual coordination across teams**, each performing their own partial analysis, followed by a manual synthesis that is slow, incomplete, and often outdated by the time it's finished.

### 4.2 Why existing tools fall short

- **Relational databases**: Cannot efficiently traverse deep multi-hop dependency chains (5-15+ hops with N:N branching)
- **Spreadsheets**: No relationship model, no temporal tracking, no cross-reference integrity
- **Existing CMDBs**: Usually domain-locked to IT infrastructure, rigid schemas, poor at handling overlapping projects and "soft" knowledge
- **Pure LLM/RAG solutions**: Hallucinate when asked about specific dependencies; cannot guarantee evidence-backed answers
- **Graph databases alone**: Provide the structural model but lack the intelligence layer, temporal versioning, evidence tracking, and user-friendly interface needed for the complete solution

### 4.3 What we need

A **unified, queryable, temporal dependency model** with:
- Universal schema adaptable to any domain
- Strict evidence tracking for every fact
- Temporal versioning and change analysis
- Multi-source reconciliation (handling conflicting data from different teams)
- Scenario branching for what-if analysis
- Intelligent natural language interface strictly grounded in data
- Modern, intuitive web UI for visual exploration and analysis

---

## 5. Goals, Success Metrics, Non-Goals

### 5.1 Goals (Platform-level)

1. **Universal graph foundation**: A domain-agnostic core that can model any dependency structure through configurable schemas
2. **Temporal intelligence**: Native support for time-travel, change tracking, diff analysis, and temporal correlation
3. **Evidence-backed reasoning**: Every fact traceable to source; every answer citable
4. **Multi-source reconciliation**: Graceful handling of conflicting data from different teams/sources with source authority and conflict visibility
5. **Intelligent analysis**: LLM-powered interface for natural language queries, multi-step reasoning, and analytical insights — all strictly grounded
6. **Code-first deployment**: Everything configurable and reproducible through code

### 5.2 Goals (POC — Restaurant Network)

1. **Ingest** 3-4 disparate Excel files into one consistent graph centered on `location_id` (4-digit base truth)
2. **Interactive graph exploration** (expand, pin, filter) in a browser
3. **Core query capabilities**:
   - Path explanation (top-K dependency chains with evidence)
   - Impact / blast radius analysis
   - Change analysis + timeline view
   - What-if scenario overlay
4. **Intelligent search** including alias resolution (legacy IDs, corporate abbreviations)
5. **Strict evidence**: every returned relationship includes source references (file, sheet, row)
6. **Demonstrate universality**: the POC domain schema is a configuration file, not hardcoded logic; loading a second minimal schema demonstrates data isolation and schema independence

### 5.3 Success metrics (POC)

- Ingest 3 Excel files and build a consistent graph with: Locations, Providers, Connections (primary/backup), Devices, Projects with per-location status
- Answer demo questions with correct entity resolution, explainable graph output, and evidence links per relationship
- Show timeline/change between two imports (any row changes reflected)
- Create a what-if branch and show impact differences
- Load a second trivial domain schema and demonstrate that the core engine handles it without code changes (data isolation confirmed)
- Demonstrate that adding a new domain schema (e.g., a simplified cloud infrastructure) requires only configuration changes, not code changes

### 5.4 Non-goals (POC)

- Continuous real-time synchronization from monitoring systems (planned later)
- Automated RCA / causal inference from telemetry (future phase, but architecture must accommodate)
- Enterprise SSO/RBAC (future phase; POC is single user, no auth)
- Full document RAG and semantic knowledge extraction (optional future, architecture accommodates)
- Predictive ML models (future phase, but data model must support training data collection)

---

## 6. Users & Personas

### 6.1 POC persona

**Infrastructure Analyst / Engineer**
- Needs fast answers about dependencies, impact, changes across a multi-location network
- Currently spends hours manually cross-referencing Excel files from different teams
- Wants to ask questions in plain English and get precise, evidence-backed answers
- Needs visual graph exploration to discover unexpected dependencies

### 6.2 Future personas

**Program / Project Manager**
- Needs rollout status views, location-level project progress, provider/modem deployment tracking
- Wants to understand how projects interact and overlap across locations

**Operations / Incident Response**
- Needs rapid impact assessment: "what is affected by this failure?"
- Needs root cause analysis: "what changed before this incident?"
- Needs cascade modeling: "if X degrades, what else degrades, stops, or recovers automatically?"

**Knowledge Researcher** (philosophical/underdetermined use cases)
- Wants to connect concepts across domains
- Tracks competing interpretations and hypotheses
- Explores probabilistic assertions with evidence weighting

**Executive / Decision Maker**
- Needs high-level views: portfolio risk, dependency hotspots, project overlap analysis
- Wants "what-if" scenario comparison for strategic decisions

---

## 7. Platform Architecture Principles

### 7.1 Domain-agnostic core vs. domain configurations

The platform separates **core engine** from **domain schema**:

**Core engine** (universal, does not change per domain):
- Graph storage with temporal versioning
- Assertion model with evidence tracking
- Ingestion framework (spec-driven)
- Query engine (path, impact, change, timeline, what-if)
- LLM orchestration layer
- UI shell (graph canvas, search, filters, timeline, chat)

**Domain configuration** (changes per use case):
- **Schema definition**: entity types, relationship types, property schemas (YAML/JSON)
- **Ingestion specs**: mapping from source files/APIs to graph entities (YAML/JSON)
- **Propagation rules**: how impact cascades through specific relationship types
- **Alias dictionary**: domain-specific abbreviations and naming conventions
- **Display rules**: how entities are labeled, colored, and grouped in the UI

### 7.2 Multi-domain support

The core engine supports **multiple domains/workspaces** within one deployment:
- Each workspace has its own schema, data, and ingestion specs
- Cross-workspace queries are possible (for future "connect the dots" scenarios)
- A workspace can extend the core ontology without breaking other workspaces
- **POC scope**: Core engine implements workspace isolation; POC demonstrates loading a second minimal schema and verifying data isolation. Full multi-workspace UI (workspace switcher, cross-workspace queries) is deferred to production phase.

### 7.3 Extensibility architecture

New capabilities should be addable without redesigning the core:
- **New data sources**: Add an ingestion spec (connector + mapping YAML)
- **New entity/relationship types**: Add to domain schema YAML
- **New query types**: Add query templates and register with the LLM tool router
- **New propagation rules**: Add rule definitions (conditions, effects, thresholds)
- **New UI views**: Add React components that consume the standard API

### 7.4 Workspace isolation — technical binding (MANDATORY)

**This section is architecturally binding.** It defines how workspaces are stored, addressed, and isolated.

#### Storage model: shared graph space + mandatory `workspace_id`

The system uses a **single NebulaGraph space** with a mandatory `workspace_id` field on every core vertex type:

| Vertex type | `workspace_id` required? |
|-------------|--------------------------|
| Entity (all domain types) | Yes |
| AssertionRecord | Yes |
| ChangeEvent | Yes |
| ImportRun | Yes |
| Source | Yes |
| PropertyValue | Yes |

**Why shared space (not separate graph space per workspace):**
- NebulaGraph creates a separate storage partition per space, which adds operational overhead for each workspace
- Cross-workspace queries (future) require cross-space joins, which NebulaGraph does not support natively
- A shared space with indexed `workspace_id` provides isolation with simpler operations

#### ID uniqueness

All IDs (`entity_id`, `assertion_id`, `change_event_id`, etc.) are **globally unique** (UUID v7 recommended for time-sortability). This guarantees:
- No collisions between workspaces
- Cross-workspace references are possible in the future without ID mapping
- IDs are meaningful outside the context of a single workspace (for export, audit, debugging)

#### API addressing

All API endpoints that read or write workspace-scoped data include `workspace_id` as a **path prefix**:

```
/api/w/{workspace_id}/entities/search
/api/w/{workspace_id}/entities/{id}
/api/w/{workspace_id}/paths
/api/w/{workspace_id}/impact
/api/w/{workspace_id}/changes
/api/w/{workspace_id}/imports
/api/w/{workspace_id}/scenarios
/api/w/{workspace_id}/conflicts
/api/w/{workspace_id}/ask
```

Workspace-management endpoints are at the root level:

```
/api/workspaces          — list, create
/api/workspaces/{id}     — get, update, delete
```

**Enforcement**: The backend must filter all graph queries by `workspace_id`. No query may return data from a workspace the request is not scoped to. This is enforced at the query engine layer, not at the application layer, to prevent accidental data leakage.

#### Index requirement

The `workspace_id` field must be part of composite indexes:
- `(workspace_id, assertion_key, scenario_id)` on AssertionRecord
- `(workspace_id, entity_type, primary_key)` on Entity vertices
- `(workspace_id, valid_from, valid_to)` on AssertionRecord

---

## 8. POC Use Case: Restaurant Network Infrastructure

### 8.1 Domain description

A large restaurant chain operates **hundreds of locations** (restaurants). Each location is identified by a **4-digit unique ID** (`location_id`) which serves as the "base truth" — all other data is anchored to this identifier.

Some locations have a **secondary 4-digit legacy ID** inherited from historical mergers of two locations into one.

### 8.2 Data layers

**Location inventory:**
- Address, phone, contacts, region, operational status
- Network devices (routers, switches, modems) with hardware and software parameters
- Servers and computers with their parameters

**Connectivity:**
- 1-3 internet connections per location (primary, backup)
- Each connection has: provider, speed, quality metrics, cost, SLA, dedicated network devices
- Connections are provided by different ISPs with different equipment

**Projects:**
- Multiple overlapping projects affect subsets of locations
- Example: "Nokia Deployment" — testing new modem type across 32 locations
- Example: "Alternative provider rollout" — 48 locations testing a different ISP
- Projects overlap unpredictably: some locations participate in multiple projects simultaneously
- Each project has per-location: status, milestones, install dates, rollback status, progress, metrics

### 8.3 Data sources (POC)

Three Excel files representing different teams' data:

1. **Chronic Stores.xlsx** — location master inventory (addresses, contacts, IDs, status)
2. **RecipeCircuitInventory.xlsx** — connectivity inventory (providers, circuits, devices, speeds, IPs)
3. **Nokia Deployment Activities Tracker.xlsx** — project tracking (deployment status, milestones, per-location progress)

### 8.4 Key challenges this POC must address

1. **Cross-team data integration**: Each file comes from a different team with different conventions
2. **Legacy ID resolution**: Some locations have two IDs that must be linked
3. **N:N project-location relationships**: Projects overlap in complex, unpredictable ways
4. **Projects change inventory**: A project deployment creates new devices, changes connections, modifies provider relationships — these causal links must be tracked
5. **Any row change = tracked change**: The system must detect and version every modification
6. **Intelligent search across fragmented data**: "Find everything related to location 1234" must aggregate across all source files

### 8.5 Example queries the POC must handle

- "Show all dependencies for location 1234" → subgraph with all connections, devices, projects
- "What locations share the same provider as location 5678?" → path query
- "What changed for location 1234 between last month and now?" → temporal diff
- "If provider X has an outage, which locations are affected and which have backup?" → impact analysis
- "What if we switch location 1234 from provider A to provider B?" → what-if scenario
- "Which locations are in both the Nokia deployment and the alternative provider project?" → cross-project overlap analysis
- "Show me all locations where the modem installation failed or was rolled back" → filtered search + project status

---

## 9. Core Data Model: Domain-Agnostic Foundation

### 9.1 Design philosophy

The data model has two layers:

**Layer 1 — Universal core** (never changes between domains):
- Entity (base type for all domain objects)
- AssertionRecord (evidence-backed claim, stored as a vertex — see 9.3)
- PropertyValue (typed value vertex for entity attributes — see 9.8)
- ChangeEvent (causal link between a trigger and resulting changes — see 9.6)
- ImportRun (provenance for batch imports)
- Source (registered data source with authority rank)

**Layer 2 — Domain schema** (configured per workspace via YAML):
- Specific entity types (Location, Device, Provider, Project, etc.)
- Specific relationship types (HAS_CONNECTION, PROVIDED_BY, PARTICIPATES_IN, etc.)
- Property schemas for each type

### 9.2 Universal assertion model

Every fact in the system is represented as an **assertion** — a typed, evidence-backed statement that "entity A has relationship R to entity B". Each assertion carries:

| Field | Purpose |
|-------|---------|
| `assertion_id` | Unique identifier |
| `assertion_key` | Stable key identifying "the same conceptual fact" across imports (for change detection) |
| `raw_hash` | Hash of the **original, untransformed** source content (detects any change, including formatting) |
| `normalized_hash` | Hash of **normalized** content (whitespace, casing, number formatting standardized) |
| `source_type` | Origin: `excel`, `api`, `manual`, `llm_extracted`, `computed` |
| `source_ref` | Specific provenance: file name, sheet, row index, API endpoint, etc. |
| `source_id` | Reference to registered Source with authority level |
| `import_run_id` | Which import batch created this assertion |
| `recorded_at` | When the system learned this fact |
| `valid_from` | When this fact became true in the real world |
| `valid_to` | When this fact ceased to be true (`null` = still valid) |
| `scenario_id` | Which scenario this belongs to (`base` or a what-if branch) |
| `confidence` | `1.0` for verified engineering facts; `<1.0` for hypotheses, inferences, or soft knowledge |
| `supersedes` | Optional: ID of the assertion this one replaces (for explicit lineage) |

#### 9.2.1 Dual-hash change detection

The system maintains **two hashes** per assertion to support different change detection needs:

- **`raw_hash`**: Computed from a **canonical serialization of the source row's cell values**, not from the raw file bytes. For Excel, this means: extract cell values in column order, serialize each as its display/string representation, concatenate with a delimiter, and hash the result. This ensures that re-saving an Excel file without changing any cell values produces the **same** `raw_hash`. However, any change to a cell value — including trailing spaces, casing, or number formatting as displayed — produces a different hash. The exact serialization format is defined per ingestion spec:

```yaml
# In ingestion spec:
raw_hash_serialization:
  cell_order: column_order          # or explicit list of column names
  delimiter: "|"
  null_representation: "<NULL>"
  number_format: "as_displayed"     # preserve Excel display format
  date_format: "as_displayed"
  include_formatting: false         # true if formatting changes should count
```

- **`normalized_hash`**: Computed after applying deterministic normalization rules (whitespace trimming, lowercase, null standardization, number format normalization). This detects **semantically meaningful** changes while ignoring formatting noise.

Each ingestion spec declares a **change detection mode**:

| Mode | Hash used for change detection | Use case |
|------|-------------------------------|----------|
| `strict` | `raw_hash` | Full audit — every formatting change is tracked |
| `normalized` | `normalized_hash` | Operational — only meaningful changes are tracked |

Both hashes are **always computed and stored** regardless of mode. The mode only controls which hash triggers a new assertion version during import. Users can query by either hash for audit/debugging purposes.

Normalization rules are defined per ingestion spec and must be:
- Documented in the spec file
- Deterministic (same input → same output, always)
- Testable (unit tests for each normalization rule)

### 9.3 Physical storage model: AssertionRecord as vertex (MANDATORY)

**This section is architecturally binding. It defines how assertions are physically stored in the graph database.**

#### The problem with edge-only storage

Storing assertions purely as edge properties creates fundamental limitations in graph databases:
1. Most graph DBs (including NebulaGraph) cannot create **multiple edges of the same type** between the same pair of vertices with different property values — or require composite key workarounds
2. Edges cannot be **referenced from other edges** (e.g., a Project cannot "point to" a specific assertion it caused)
3. Querying for "all assertions from source X" or "all assertions that changed in time window T" requires scanning all edges of all types

#### The hybrid model

The system uses a **hybrid vertex-edge model**:

```
┌──────────┐                              ┌──────────┐
│ Entity A │──(ASSERTED_REL)──►┌────────┐──(ASSERTED_REL)──►│ Entity B │
│ (vertex) │                   │Asrt.Rec│                   │ (vertex) │
└──────────┘                   │(vertex)│                   └──────────┘
                               └───┬────┘
                                   │
              assertion_id, assertion_key, raw_hash,
              normalized_hash, source_ref, source_id,
              import_run_id, recorded_at, valid_from,
              valid_to, scenario_id, confidence,
              relationship_type, supersedes
```

**AssertionRecord** is a **vertex** (not an edge) that represents "the claim that Entity A has relationship R with Entity B". It connects to both entities via lightweight `ASSERTED_REL` edges that carry only the `assertion_id` reference.

#### Why this design

| Concern | How the hybrid model solves it |
|---------|-------------------------------|
| Multiple competing claims about the same relationship | Multiple AssertionRecord vertices, each from a different source, all linking the same pair of entities |
| Referencing an assertion from elsewhere (e.g., ChangeEvent, Project causal link) | Standard vertex-to-vertex edge from ChangeEvent → AssertionRecord |
| Querying "all assertions from source X" or "changed in time window" | Direct vertex query on AssertionRecord with indexed properties |
| Temporal versioning with validity intervals | Each AssertionRecord has its own `valid_from`/`valid_to`; closing one and opening another is creating/updating vertices, not edge gymnastics |
| Scenario branching | `scenario_id` is a property on AssertionRecord; overlay queries filter/prioritize by scenario |

#### Indexes (required for performance)

The following indexes must be created on `AssertionRecord`:
- `(assertion_key, scenario_id)` — for change detection and scenario overlay
- `(source_id, recorded_at)` — for "all assertions from source X" queries
- `(valid_from, valid_to)` — for temporal queries ("state at time T")
- `(import_run_id)` — for import diff computation

#### Convenience edge (optional optimization)

For frequently traversed paths where assertion metadata is not needed (e.g., simple graph exploration), the system may **also** maintain direct **convenience edges** between entities (e.g., `Location -[HAS_CONNECTION]-> Connection`). These are materialized views derived from the current resolved AssertionRecords. They must be:
- Regenerated on import (not manually maintained)
- Clearly marked as derived (not source of truth)
- Used only for fast traversal; all evidence queries go through AssertionRecord

### 9.4 Resolved view vs. all-claims view

#### The two modes of reading the graph

At any point, multiple assertions may exist about the same conceptual relationship (from different sources, at different confidence levels, or in different scenarios). The system provides **two reading modes**:

**Resolved view** (`view_mode=resolved`, default):
- Shows the **single preferred assertion** per `assertion_key` for the requested scenario and time
- Resolution algorithm (applied in order, each step is a tiebreaker for the previous):
  1. **Scenario**: prefer assertions in the requested `scenario_id`; fall back to `base`
  2. **Manual override**: if a `source_type=manual` assertion exists, prefer it (explicit human decision)
  3. **Authority**: among remaining, prefer the source with **lowest `authority_rank`** number (rank 1 beats rank 2; lower rank = higher trust)
  4. **Recency**: if authority_rank is equal, prefer the most recently recorded (`recorded_at` descending)
  5. **Confidence**: if recency is equal, prefer higher `confidence`
- This is what the graph canvas, path queries, and impact analysis use by default

**All-claims view** (`view_mode=all_claims`):
- Shows **all assertions** for the requested `assertion_key`, including competing claims from different sources
- Each assertion is annotated with: source, authority level, validity interval, confidence, and whether it is the currently "resolved" winner
- This is what the Conflicts view, reconciliation workflows, and audit trails use

**API enforcement**: Every query endpoint that returns graph data accepts a `view_mode` parameter. The LLM tool interface always receives resolved view by default, but can be instructed to use all-claims when investigating conflicts.

### 9.5 Domain schema definition (YAML)

Domain schemas are defined as code. Example structure:

```yaml
# domain_schema: restaurant_network_v1
workspace: restaurant_network
version: "1.0"

entity_types:
  Location:
    primary_key: location_id
    properties:
      location_id: { type: string, required: true, pattern: "^\\d{4}$" }
      name: { type: string }
      address: { type: string }
      phone: { type: string }
      region: { type: string }
      status: { type: string, enum: [active, closed, pending] }

  Provider:
    primary_key: provider_id
    properties:
      provider_id: { type: string, required: true }
      name: { type: string }

  Connection:
    primary_key: connection_id
    properties:
      connection_id: { type: string, required: true }
      role: { type: string, enum: [primary, backup, tertiary] }
      speed: { type: string }
      cost: { type: number }
      circuit_id: { type: string }

  # ... Device, Host, Project, etc.

relationship_types:
  HAS_CONNECTION:
    from: Location
    to: Connection
    properties:
      role: { type: string }

  PROVIDED_BY:
    from: Connection
    to: Provider

  PARTICIPATES_IN:
    from: Location
    to: Project
    properties:
      status: { type: string }
      install_date: { type: date }
      progress: { type: string }

  HAS_ALIAS:
    from: Location
    to: LocationAlias

  # ... additional relationship types

alias_config:
  entity_type: Location
  alias_entity_type: LocationAlias
  alias_key: alias_id
```

### 9.6 ChangeEvent vertex (causal tracking)

#### The problem

When a project action results in an inventory change (e.g., "Nokia deployment installed new modem at location 1234"), we need to record **why** the change happened. In a graph database, edges cannot reference other edges, so we cannot create a direct link from a Project to an AssertionRecord using a simple edge.

#### The solution: ChangeEvent vertex

`ChangeEvent` is a **core vertex type** (part of the universal model, not domain-specific) that records "something caused a set of assertions to be created/modified/closed."

#### ChangeEvent granularity (MANDATORY decision)

The system creates ChangeEvents at the following granularity:

| Trigger | ChangeEvent count | Scope |
|---------|-------------------|-------|
| Import run | **One** ChangeEvent per import run | Contains references to ALL AssertionRecords created, closed, or modified in that run |
| Manual conflict resolution | **One** ChangeEvent per resolution action | References the specific AssertionRecord(s) affected |
| Scenario delta | **One** ChangeEvent per delta operation | References AssertionRecords created/closed in the scenario |
| Manual UI edit | **One** ChangeEvent per edit action | References the specific AssertionRecord(s) affected |

This means an import that changes 500 rows creates **one** ChangeEvent with 500 `AFFECTED` links, not 500 ChangeEvents. This keeps the graph manageable and the timeline view clean.

```
┌─────────┐                              ┌──────────────┐
│ Project  │──(TRIGGERED)──►┌───────────┐──(AFFECTED)──►│ AssertionRec │
│ (vertex) │                │ChangeEvent│──(AFFECTED)──►│ AssertionRec │
└──────────┘                │ (vertex)  │──(AFFECTED)──►│ AssertionRec │
                            └─────┬─────┘               └──────────────┘
                                  │
                          change_event_id
                          event_type: "import_diff" | "manual_resolve" |
                                      "scenario_delta" | "manual_edit"
                          description: "Import of chronic_stores.xlsx: 12 added, 3 modified, 1 removed"
                          timestamp
                          import_run_id (if applicable)
                          workspace_id
                          actor: "user:john" | "system:import" | "project:nokia_deployment"
                          stats: { created: 12, closed: 1, modified: 3 }
```

**Relationships from ChangeEvent (all reference AssertionRecords, not Entities directly):**
- `ChangeEvent -[TRIGGERED_BY]-> Entity` (what caused the change: Project, ImportRun, or user-created "ManualAction" vertex)
- `ChangeEvent -[CREATED]-> AssertionRecord` (new assertions created in this event)
- `ChangeEvent -[CLOSED]-> AssertionRecord` (old assertions closed/superseded in this event)

To find which **Entities** were affected, traverse: `ChangeEvent -[CREATED|CLOSED]-> AssertionRecord -[ASSERTED_REL]-> Entity`. This is a two-hop query, but it is the correct approach because it preserves the specificity of *which assertion* changed, not just *which entity was touched*.

**Why this matters:**
- Enables FR-PI-1 (causal tracking): "This Device was added as part of Project X" → traverse `ChangeEvent -[CREATED]-> AssertionRecord -[ASSERTED_REL]-> Device`
- Enables FR-PI-2 (project impact view): Query all ChangeEvents where `TRIGGERED_BY` points to a Project
- Enables FR-Q-6 (RCA): "What ChangeEvents happened in the time window before the incident?" → find ChangeEvents in window → traverse CREATED/CLOSED → find affected entities
- Provides a natural **audit log** that is part of the graph, not a separate system

### 9.7 Why this design enables universality

To deploy the platform for a different domain (e.g., cloud infrastructure), one only needs to:

1. Create a new `domain_schema.yaml` with appropriate entity types (VM, Cluster, Namespace, Service, etc.)
2. Create ingestion specs mapping the new data sources
3. Define propagation rules for impact analysis
4. Optionally, add domain-specific alias dictionaries

No code changes to the core engine (AssertionRecord, ChangeEvent, PropertyValue, resolved-view logic, query engine, UI framework).

### 9.8 Property assertions: evidence-backed entity attributes (MANDATORY)

**This section is architecturally binding.** It defines how entity properties (speed, cost, status, install_date, etc.) are stored, versioned, and reconciled with the same rigor as relationships.

#### The problem

In v2.0, the data model stated "every fact is an assertion that entity A has relationship R to entity B," but entity properties (e.g., Connection.speed = "100Mbps") were implicitly stored as vertex properties. This creates a gap: properties are not versioned, not evidence-backed, not conflict-aware, and not queryable by source.

#### The solution: PropertyValue vertex + HAS_PROPERTY assertion

Entity properties are stored as **AssertionRecords linking an Entity to a PropertyValue vertex**, using the relationship type `HAS_PROPERTY`:

```
┌────────────┐                                    ┌───────────────┐
│ Connection │──(ASSERTED_REL)──►┌──────────────┐──(ASSERTED_REL)──►│ PropertyValue │
│  (vertex)  │                   │AssertionRecord│                  │   (vertex)    │
└────────────┘                   │              │                  │ property_key: │
                                 │ rel_type:    │                  │   "speed"     │
                                 │ HAS_PROPERTY │                  │ value: "100"  │
                                 │ property_key:│                  │ value_type:   │
                                 │   "speed"    │                  │   "string"    │
                                 └──────────────┘                  └───────────────┘
```

**PropertyValue** is a core vertex type with:

| Field | Purpose |
|-------|---------|
| `property_value_id` | Globally unique ID |
| `workspace_id` | Workspace isolation |
| `property_key` | Property name (e.g., "speed", "cost", "status") |
| `value` | String-serialized value |
| `value_type` | Type hint: `string`, `number`, `date`, `boolean`, `json` |

The **AssertionRecord** linking Entity → PropertyValue carries `relationship_type = "HAS_PROPERTY"` and includes `property_key` as a convenience field (duplicated from PropertyValue for indexed queries).

#### Why this design

| Concern | How it's solved |
|---------|-----------------|
| **Versioning**: speed changed from 50Mbps to 100Mbps | Old AssertionRecord (speed=50) closed, new one (speed=100) created. Both preserved in history. |
| **Conflict**: Team A says speed=100, Team B says speed=50 | Two active AssertionRecords with same entity + same property_key + overlapping validity. Resolved view picks winner by authority_rank. |
| **Evidence**: Where did this speed value come from? | AssertionRecord has `source_ref` (file/sheet/row), `source_id`, `import_run_id` |
| **Timeline**: When did the cost change? | Query AssertionRecords for this entity + property_key, ordered by `valid_from` |
| **RCA**: Was the status recently changed? | ChangeEvent links to the AssertionRecord that was created/closed |

#### Assertion key for properties

For property assertions, `assertion_key` is constructed as:

```
{workspace_id}:{entity_type}:{entity_primary_key}:prop:{property_key}
```

Example: `restaurant_network:Connection:conn_1234:prop:speed`

This ensures that re-importing a file with a changed speed value for the same connection correctly detects the change and creates a new version.

#### Convenience properties on Entity vertices (optional optimization)

For fast filtering and display without traversing AssertionRecords, Entity vertices **may** carry **convenience properties** — copies of the currently-resolved property values, materialized during import. These are:
- Regenerated from resolved AssertionRecords on every import
- Clearly marked as derived (not source of truth)
- Used only for fast list/filter/display; all evidence and history queries go through AssertionRecords
- Include a `_resolved_at` timestamp indicating when they were last materialized

---

## 10. Functional Requirements

### 10.1 Data ingestion & normalization

**FR-ING-1**: Import structured data files (Excel .xlsx, CSV, JSON) with multiple sheets/tables.
- Convert to normalized staging data
- Maintain raw file retention for audit

**FR-ING-2**: Code-defined ingestion mapping (spec-driven).
- Mapping specs in version control (YAML/JSON)
- No required manual UI mapping
- Specs define: source columns → entity types → relationship creation → normalization rules
- Each spec declares `change_detection_mode: strict | normalized`

**FR-ING-3**: Entity resolution rules.
- Primary key resolution per domain schema
- Support alias mapping (legacy IDs → canonical ID)
- Deduplication by normalized keys
- Fuzzy matching via vector similarity for ambiguous references

**FR-ING-4**: Evidence preservation.
- Store per-row source reference: file, sheet, row index, import run
- Compute and store both `raw_hash` and `normalized_hash` for every assertion
- Raw file archival for audit trail

**FR-ING-5**: Import runs.
- Every import produces an `import_run_id` with timestamp
- Import output is versioned using validity intervals
- Import is idempotent: same file + same spec = same graph state
- Every import generates a set of ChangeEvent vertices documenting what changed

**FR-ING-6**: Future connector framework.
- Architecture must support adding API connectors (Terraform, K8s, Zabbix, etc.) as additional ingestion sources
- Each connector is a spec + adapter, not a core code change

### 10.2 Graph model & temporal versioning

**FR-G-1**: Represent all domain data as a property graph defined by the domain schema, using the hybrid AssertionRecord model (see 9.3).

**FR-G-2**: Temporal validity on all AssertionRecords.
- Each AssertionRecord has `valid_from` and `valid_to`
- "Current" assertions have `valid_to = null` (or max timestamp)

**FR-G-3**: Row-level change tracking.
- Stable `assertion_key` identifies "the same conceptual fact" across imports
- Dual-hash system (`raw_hash` + `normalized_hash`) detects changes (see 9.2.1)
- Change detection mode (`strict` / `normalized`) is per ingestion spec
- If change detected → close old AssertionRecord's validity, create new one, create ChangeEvent

**FR-G-4**: Scenario branching.
- Every AssertionRecord has `scenario_id`
- Base truth uses `scenario_id = "base"`
- What-if scenarios overlay base via prioritization rules (see 9.4)
- Scenarios are lightweight (store only deltas, not full copies)

**FR-G-5**: Resolved view and all-claims view (see 9.4).
- All query endpoints support `view_mode=resolved|all_claims` parameter
- Default is `resolved`

### 10.3 Query capabilities

**FR-Q-1 (Path)**: Given two entities, return top-K dependency paths.
- Must return path steps + edge evidence per hop
- Uses resolved view by default; can be switched to all-claims

**FR-Q-2 (Impact / Blast Radius)**: Given an entity and a failure condition, compute affected subgraph.
- Uses domain-defined propagation rules (see section 14.2)
- Must distinguish: "will break", "will degrade", "may be affected", "has backup/failover"
- Must return affected nodes with severity + evidence

**FR-Q-3 (Change Analysis)**: Compute diffs between timepoints or import runs.
- Added, removed, modified AssertionRecords
- Per-entity or domain-wide
- Uses ChangeEvent vertices for causal context ("why did this change?")

**FR-Q-4 (Timeline)**: Display temporal evolution of an entity or relationship.
- All AssertionRecords (current and closed) involving the entity, ordered by time
- Includes ChangeEvent context for each transition

**FR-Q-5 (What-If)**: Create branch scenario, apply changes, query impacts vs base.
- Side-by-side comparison of base vs scenario (resolved views)

**FR-Q-6 (Root Cause Analysis)**: Given a symptom/failure and time window, trace backwards through dependencies to identify candidate root causes.
- Combine temporal correlation (ChangeEvents in window) with structural dependency (upstream traversal)
- Rank candidates by relevance

**FR-Q-7 (Cross-entity Pattern Matching)**: Find entities with similar characteristics.
- **POC definition of "similar"**: Property-based feature vector (entity properties + relationship counts + project participation) embedded via Qdrant, with kNN retrieval
- Example: "Find locations with a similar setup to location 1234" → embed location features → kNN search
- **Future**: Structural subgraph similarity, which requires dedicated graph matching algorithms (deferred)

**FR-Q-8 (Anomaly Highlighting)**: Flag unusual patterns in the data.
- Locations with only one connection (no backup)
- Devices with mismatched configurations across similar locations
- Projects with stalled progress or unusual rollback rates

### 10.4 Multi-source reconciliation

**FR-R-1 (Conflict Detection)**: When multiple sources assert different values for the **same `assertion_key`** and their **validity intervals overlap** (`valid_from`/`valid_to` intersect), detect and flag as a conflict.
- Two assertions about the same `assertion_key` with **non-overlapping** validity intervals are NOT a conflict — they represent the fact at different points in time (e.g., a legitimate upgrade from 50Mbps to 100Mbps)
- Conflict = same conceptual fact + different content + simultaneously valid

**FR-R-2 (Source Authority)**: Allow defining authority levels per source per data domain.
- Example: "Team A is authoritative for connectivity data; Team B is authoritative for project status"
- When conflicts exist, the more authoritative source wins in resolved view
- All versions remain accessible in all-claims view

**FR-R-3 (Conflict Visibility)**: Users can view all conflicting assertions for any entity.
- Show: which source says what, when, with what confidence, and which is currently resolved

### 10.5 Intelligent search

**FR-S-1**: Full text and semantic search across all entity properties and notes.

**FR-S-2**: Alias and shorthand resolution.
- Maintain a configurable dictionary of domain-specific abbreviations
- Support fuzzy matching and vector similarity
- Learn from corrections (supervised, human-reviewed)

### 10.6 LLM-assisted natural language interface

**FR-LLM-1**: Natural language question → intent classification (path, impact, change, timeline, search, what-if, RCA, anomaly).

**FR-LLM-2**: Entity extraction + resolution from natural language to canonical IDs.

**FR-LLM-3**: Multi-step reasoning — LLM can chain multiple queries to answer complex questions.
- Example: "Are there locations that are in both the Nokia project and have only one internet connection?" requires: (1) find Nokia project locations, (2) check connection count for each, (3) intersect

**FR-LLM-4**: Deterministic execution — LLM does not generate facts; it routes to graph queries.

**FR-LLM-5**: Grounded response — final text is a summary of returned data with source references for every relationship used.

**FR-LLM-6**: "No data" honesty — if the graph has no relevant data, the system says so clearly.

### 10.7 Project ↔ Inventory causal tracking

**FR-PI-1**: When a project action results in an inventory change, the system tracks the causal link via a `ChangeEvent` vertex (see 9.6).
- "This Device was added as part of Project X" → `Project -[TRIGGERED]-> ChangeEvent -[CREATED]-> AssertionRecord`

**FR-PI-2**: Project impact view — query all ChangeEvents triggered by a project to show how it has changed the inventory over time.

---

## 11. Temporal Versioning & Change Analysis

### 11.1 Validity interval rules

- On import: if `assertion_key` exists and hash unchanged (per spec's change detection mode) → keep current validity
- If hash changed → close old AssertionRecord (`valid_to = now`), create new AssertionRecord (`valid_from = now`), create ChangeEvent linking old and new
- If row disappears in new import → close validity (`valid_to = now`), create ChangeEvent
- New rows → create AssertionRecord with `valid_from = now`, `valid_to = null`, create ChangeEvent

### 11.2 Change granularity and dual-hash policy

- **`strict` mode**: `raw_hash` is used for change detection — any change at all (including whitespace, casing) triggers a new assertion version. Use for full audit compliance.
- **`normalized` mode**: `normalized_hash` is used — only semantically meaningful changes trigger a new version. Use for operational day-to-day work.
- Both hashes are always stored regardless of mode, enabling after-the-fact audit.
- Mode is declared per ingestion spec, not globally:

```yaml
# In ingestion spec:
change_detection:
  mode: normalized  # or "strict"
  normalization_rules:
    - trim_whitespace: true
    - lowercase_strings: true
    - normalize_nulls: ["", "N/A", "n/a", "null", "-"]
    - number_format: { decimal_places: 2 }
    - date_format: "YYYY-MM-DD"
```

### 11.3 Timeline queries

- "State at time T": filter AssertionRecords by `valid_from <= T < valid_to`, apply resolved-view algorithm
- "Diff between T1 and T2": compare sets of active (resolved) assertions at T1 vs T2
- "History of entity X": all AssertionRecords (current and closed) involving X, ordered by time, with ChangeEvent context

### 11.4 Temporal correlation (for RCA)

- Given an incident at time T, find all ChangeEvents in `[T - window, T]`
- For each ChangeEvent, traverse `CREATED/CLOSED` edges to find affected AssertionRecords, then `ASSERTED_REL` edges to find affected entities
- Rank candidates by: temporal proximity × structural relevance (dependency distance from affected entity) × number of assertions affected

---

## 12. Scenario Branching (What-If)

### 12.1 Scenario representation

- `scenario_id` string field on every AssertionRecord
- Base scenario: `"base"`
- What-if scenarios: named overlays (e.g., `"whatif_switch_provider_2026Q1"`)

### 12.2 Overlay semantics

When querying in a scenario (via resolved view):
1. Check for AssertionRecords in the target scenario first
2. Fall back to base AssertionRecords when no scenario-specific override exists for a given `assertion_key`
3. A scenario can "close" a base assertion (create a scenario-specific AssertionRecord with `valid_to = now`) without affecting base
4. All scenario modifications create ChangeEvent vertices with `event_type = "scenario_delta"`

### 12.3 Supported what-if operations

- Add new entity or relationship (new AssertionRecord in scenario)
- Remove or modify existing relationship (override AssertionRecord in scenario)
- Adjust properties (change provider, change speed, change project status)
- Chain effects via propagation rules to show cascading impact

### 12.4 Scenario comparison

- Side-by-side diff: resolved view at base vs resolved view at scenario
- Impact delta: "what is different about the blast radius in this scenario vs base?"

---

## 13. Multi-Source Reconciliation & Conflict Resolution

### 13.1 The problem

Different teams maintain overlapping data about the same entities. File A says location 1234 has 100Mbps speed; File B says 50Mbps. Both are "true" from their respective sources' perspective. The system must handle this gracefully — not by silently picking one, but by making the conflict visible and providing a principled resolution.

### 13.2 Source registry

Each data source is registered with:
- `source_id`: unique identifier
- `source_name`: human-readable name (e.g., "Network Team Inventory Q1")
- `source_type`: excel, api, manual, etc.
- `authority_domains`: list of entity/relationship types this source is authoritative for
- `authority_rank`: integer priority within its domain. **Lower number = higher authority** (rank 1 is the most trusted source). This convention matches typical priority systems (P1 > P2) and is used consistently in all resolution algorithms.
- `update_frequency`: how often this source is refreshed

### 13.3 Conflict definition (temporal precision)

A **conflict** exists when:
1. Two or more AssertionRecords share the same `assertion_key`
2. They come from **different sources** (`source_id` differs)
3. Their content differs (`normalized_hash` differs)
4. Their **validity intervals overlap**: `max(a.valid_from, b.valid_from) < min(a.valid_to, b.valid_to)`

Two assertions about the same `assertion_key` with **non-overlapping** validity intervals are **not a conflict** — they represent legitimate temporal evolution (e.g., speed was 50Mbps until March, then upgraded to 100Mbps).

### 13.4 Conflict resolution rules

1. **Detection**: Automated during import — when a new assertion is created, check for existing active assertions with the same `assertion_key` from different sources
2. **Resolved view resolution** (see 9.4): Manual override → Authority (lowest `authority_rank` wins) → recency → confidence
3. **Visibility**: All competing assertions remain in the system; all-claims view shows everything
4. **Manual override**: Users can explicitly resolve by creating a new assertion with `source_type = manual` and a resolution note. This becomes the highest-priority assertion in the resolved view.
5. **Notification**: Newly detected conflicts are flagged in the UI (Conflicts dashboard)

### 13.5 Reconciliation view (UI)

- Dashboard showing all entities with active (unresolved or auto-resolved) conflicts
- For each conflict: source A says X, source B says Y, current resolution is Z (with algorithm explanation)
- Action: manual override with explanation text
- Filter by: entity type, source, severity, age

---

## 14. Intelligent Analysis Layer

### 14.1 Purpose

Beyond basic CRUD and query, the platform must provide **analytical intelligence** — helping users discover patterns, understand impact, and find "needles in haystacks" across large, complex datasets.

### 14.2 Cascade modeling (Impact Simulation)

**What it does**: Given a failure condition on an entity, simulate how the failure propagates through the dependency graph according to domain-defined rules.

#### 14.2.1 Propagation rules specification

Propagation rules are defined in the domain configuration as YAML. Each rule is a self-contained, testable unit.

**Rule structure:**

```yaml
propagation_rules:
  - rule_id: "provider_outage_primary_only"
    version: "1.0"
    description: "If a provider goes down, locations with only primary connection through that provider lose connectivity"

    trigger:
      entity_type: Provider
      condition:
        field: status
        operator: eq
        value: "down"

    steps:
      - step_id: "find_affected_connections"
        traverse:
          edge_type: PROVIDED_BY
          direction: inbound    # Connection → Provider, go backwards
        filter:
          field: role
          operator: eq
          value: "primary"
        effect:
          type: degrades        # breaks | degrades | delays | triggers_failover
          set_field: status
          set_value: "degraded"
          severity: high

      - step_id: "check_backup_exists"
        description: "For each affected connection's location, check if backup exists"
        traverse:
          edge_type: HAS_CONNECTION
          direction: inbound    # Location → Connection, go backwards
        condition:
          type: subquery
          query: "count active connections with role=backup for this location"
          operator: eq
          value: 0
        effect:
          type: breaks
          set_field: connectivity_status
          set_value: "offline"
          severity: critical

    evidence_logging:
      log_each_step: true       # every fired step is logged as evidence
      include_trigger: true     # reference the triggering condition
      include_path: true        # include the traversal path
```

**Execution semantics:**
- Steps execute in order
- Each step receives the set of entities from the previous step (pipeline)
- `condition` filters further within a step
- `effect` annotates affected entities with impact type and severity
- All fired steps are logged as evidence, so the user can see *why* each entity is affected

**Determinism guarantee:** Given the same graph state + same rules → same impact result. No randomness, no ML in the POC propagation engine.

**POC scope:** Simple sequential step execution. Future: parallel branches, weighted probabilities, threshold-based propagation (e.g., "if aggregate latency > X").

### 14.3 Root Cause Analysis (RCA)

**What it does**: Given a symptom (entity in degraded/failed state) and a time window, work backwards through dependencies and temporal changes to identify probable root causes.

**Approach**:
1. Find all structural dependencies of the affected entity (upstream traversal via AssertionRecords)
2. Find all ChangeEvents within the time window across those dependencies
3. Score candidates by: temporal proximity × structural relevance × historical pattern similarity
4. Present ranked list with evidence (ChangeEvent details + dependency path)

**POC scope**: Structural dependency traversal + temporal ChangeEvent correlation. Future: pattern learning from historical incidents.

### 14.4 Anomaly Detection

**What it does**: Proactively flags unusual patterns in the data without being asked.

**Examples**:
- Locations with single connection (no redundancy)
- Devices with firmware versions different from peers in the same project
- Projects with unusually high rollback rates
- Entities with rapidly changing assertions (instability signal: many ChangeEvents in short window)
- Locations participating in too many simultaneous projects (risk indicator)

**POC scope**: Rule-based anomaly checks defined in domain configuration YAML. Future: statistical anomaly detection.

### 14.5 Multi-step analytical reasoning (Agent mode)

**What it does**: For complex questions that cannot be answered by a single graph query, the LLM orchestrates a sequence of queries, each building on the previous results.

**Example flow** for "Find all locations where the Nokia project is behind schedule AND they have only a single internet connection":
1. LLM identifies intent: cross-query (project status + connectivity count)
2. Query 1: find locations in Nokia project with status = "behind"
3. Query 2: for each of those locations, count active connections (resolved view)
4. Filter: keep only those with count = 1
5. Summarize with evidence from both queries

**Implementation**: The LLM has access to a set of **tools** (see section 15.4) and can call them in sequence, accumulating context. The backend enforces that all facts come from tool results, not LLM generation.

---

## 15. LLM Integration Design (Strict Grounding)

### 15.1 Core principle

The LLM is an **intelligent query operator** — it understands user intent, translates it to precise operations, and summarizes structured results in natural language. It is **never** the source of facts.

### 15.2 Allowed LLM responsibilities

- Intent classification (what type of query is this?)
- Entity extraction and normalization (what entities is the user referring to?)
- Multi-step query planning (which queries in what order?)
- Result summarization (convert structured data to readable explanation)
- Alias dictionary augmentation (suggest new aliases, subject to human review)

### 15.3 Forbidden LLM behaviors

- Creating facts not present in graph/vector store
- Presenting unverified relationships
- Answering with "I think" or speculation when data is insufficient — must say "no data found"
- Inventing source references

### 15.4 Tool-based orchestration

Backend exposes tools that the LLM can call:

| Tool | Purpose |
|------|---------|
| `resolve_entities(query)` | Find entity IDs matching a natural language reference |
| `get_entity(id, view_mode)` | Get entity details + immediate neighbors |
| `find_paths(from, to, scenario, time, k, view_mode)` | Find top-K dependency paths |
| `compute_impact(entity, scenario, time, depth, edge_types)` | Compute blast radius via propagation rules |
| `get_changes(entity, t1, t2, scenario)` | Get change diff with ChangeEvent context |
| `get_timeline(entity, scenario)` | Get temporal history |
| `search(query, filters)` | Semantic + full-text search |
| `find_similar(entity_id, k)` | Find similar entities via feature embedding kNN |
| `find_anomalies(entity_type, checks)` | Run anomaly detection checks |
| `get_conflicts(entity_id)` | Get all competing claims (all-claims view) |
| `create_scenario(name, base)` | Create what-if branch |
| `apply_scenario_delta(scenario, changes)` | Modify a scenario |
| `compare_scenarios(s1, s2)` | Compare two scenarios |

### 15.5 Response construction

1. LLM receives user question
2. LLM classifies intent, extracts entities, plans query sequence
3. LLM calls tools (one or more, in sequence)
4. Backend executes deterministic graph/vector queries, returns structured results with evidence
5. LLM summarizes results in natural language
6. Backend **programmatically attaches** source references (not relying on LLM to cite correctly)
7. If no data found → explicit "no data" response

### 15.6 LLM model selection

- **Simple tasks** (intent classification, entity extraction): Ollama with local model (cost = 0)
- **Complex tasks** (multi-step reasoning, nuanced summarization): Cloud API (OpenAI / Anthropic)
- Selection is configurable per query type

### 15.7 Agent mode guardrails (MANDATORY)

When the LLM operates in multi-step agent mode (section 14.5), the following guardrails are enforced by the backend:

#### Resource limits

| Parameter | POC default | Configurable? |
|-----------|-------------|---------------|
| `max_tool_calls_per_question` | 10 | Yes (env var) |
| `session_timeout_seconds` | 30 | Yes (env var) |
| `max_result_rows_per_tool_call` | 500 | Yes (env var) |
| `max_total_tokens_per_session` | 16,000 | Yes (env var) |

If any limit is reached, the agent **must stop**, return whatever partial results it has collected so far, and include a message: "Analysis incomplete — resource limit reached. Consider narrowing the query or increasing limits."

#### All-claims view policy

The agent operates in **resolved view by default**. It may switch to `all_claims` view only when:
1. The user's question explicitly asks about conflicts, discrepancies, or competing data (e.g., "are there conflicting reports about location 1234's speed?")
2. The LLM classifies the intent as `conflict_investigation`
3. The agent has already received a resolved-view result that references known conflicts (indicated by a `has_conflicts: true` flag in the response)

The agent **must not** proactively switch to all-claims for regular queries — this would produce confusing, noisy results.

#### Chain-of-action logging

Every agent session produces a **session log** stored as a JSON document:

```json
{
  "session_id": "ask_2026-02-18_001",
  "workspace_id": "restaurant_network",
  "user_question": "Which locations have only one connection and are in the Nokia project?",
  "intent_classification": "cross_query",
  "tool_calls": [
    {
      "step": 1,
      "tool": "search",
      "params": { "query": "Nokia project locations", "view_mode": "resolved" },
      "result_count": 32,
      "duration_ms": 180
    },
    {
      "step": 2,
      "tool": "get_entity",
      "params": { "id": "loc_1234", "view_mode": "resolved" },
      "result_count": 1,
      "duration_ms": 45
    }
  ],
  "total_tool_calls": 2,
  "total_duration_ms": 850,
  "grounding_check": {
    "all_facts_sourced": true,
    "assertion_ids_referenced": ["asrt_001", "asrt_002", "asrt_015"]
  },
  "final_answer_length": 342
}
```

This log is:
- Stored per session (queryable via API: `GET /api/w/{workspace_id}/ask/sessions`)
- Available for debugging and auditing grounding compliance
- Used to detect patterns of excessive tool usage (potential prompt optimization opportunities)

---

## 16. API Requirements

### 16.1 Global query parameters

All workspace-scoped endpoints are prefixed with `/api/w/{workspace_id}/` (see 7.4).

All graph query endpoints additionally accept:
- `view_mode=resolved|all_claims` (default: `resolved`) — see section 9.4
- `scenario=<scenario_id>` (default: `base`)
- `at_time=<ISO timestamp>` (default: now) — for temporal queries

### 16.2 Workspace management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/workspaces` | GET | List workspaces |
| `/api/workspaces` | POST | Create workspace (with schema YAML) |
| `/api/workspaces/{id}` | GET | Get workspace details + schema |

### 16.3 Ingestion

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/w/{wid}/imports` | POST | Upload file + select mapping spec → create import job |
| `/api/w/{wid}/imports` | GET | List import runs with stats |
| `/api/w/{wid}/imports/{id}` | GET | Import status, stats, errors, change summary |
| `/api/w/{wid}/imports/{id}/diff` | GET | Diff vs previous import (ChangeEvent details) |

### 16.4 Schema & Configuration

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/w/{wid}/schema` | GET | Get domain schema definition |
| `/api/w/{wid}/schema/entity-types` | GET | List entity types |
| `/api/w/{wid}/schema/relationship-types` | GET | List relationship types |

### 16.5 Graph queries

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/w/{wid}/entities/search` | GET | Full-text + semantic search |
| `/api/w/{wid}/entities/{id}` | GET | Entity details + neighbors (view_mode applies) |
| `/api/w/{wid}/entities/{id}/assertions` | GET | All AssertionRecords for entity |
| `/api/w/{wid}/entities/{id}/history` | GET | ChangeEvent history for entity |
| `/api/w/{wid}/paths` | GET | Find dependency paths between entities |
| `/api/w/{wid}/impact` | GET | Compute blast radius from entity |
| `/api/w/{wid}/changes` | GET | Compute diff between timepoints |
| `/api/w/{wid}/timeline/{entity_id}` | GET | Temporal history with ChangeEvent context |
| `/api/w/{wid}/anomalies` | GET | Run anomaly detection |
| `/api/w/{wid}/similar/{entity_id}` | GET | Find similar entities (kNN) |

### 16.6 Scenarios

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/w/{wid}/scenarios` | POST | Create scenario (creates ChangeEvent) |
| `/api/w/{wid}/scenarios` | GET | List scenarios |
| `/api/w/{wid}/scenarios/{id}/delta` | POST | Apply changes to scenario (creates ChangeEvent) |
| `/api/w/{wid}/scenarios/compare` | GET | Compare two scenarios (resolved views) |

### 16.7 Reconciliation

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/w/{wid}/conflicts` | GET | List active conflicts (overlapping validity intervals) |
| `/api/w/{wid}/conflicts/{id}` | GET | Conflict detail: all competing assertions |
| `/api/w/{wid}/conflicts/{id}/resolve` | POST | Manually resolve (creates manual assertion + ChangeEvent) |

### 16.8 Intelligent query

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/w/{wid}/ask` | POST | Natural language question → grounded answer + evidence |
| `/api/w/{wid}/ask/sessions` | GET | List agent session logs (for audit/debugging) |
| `/api/w/{wid}/ask/sessions/{id}` | GET | Get specific session log with full tool call chain |

---

## 17. UI/UX Requirements

### 17.1 Main screens

1. **Explorer** — Interactive graph canvas with filters, expand/collapse, detail panel
2. **Search** — Quick search bar + advanced filters (by type, property, time range, source)
3. **Path View** — Select two entities → display dependency paths with evidence per edge
4. **Impact View** — Select entity + failure condition → highlight affected nodes with severity, show propagation rule evidence
5. **Timeline / Changes** — Select entity → show change history with ChangeEvent context; compare two timepoints
6. **Import Manager** — Upload files, select specs, view import history, view diffs
7. **Scenario Manager** — Create/edit/compare what-if scenarios
8. **Ask (NL Chat)** — Chat-like interface with citations panel and graph visualization of answers
9. **Conflicts** — Dashboard of active conflicts with resolution workflow
10. **Anomalies** — Dashboard of detected anomalies (future, beyond POC MVP)

### 17.2 Evidence UX (critical requirement)

Every relationship displayed in the UI must show on demand:
- Source file name, sheet, row number
- Import run ID and timestamp
- Confidence level
- Scenario context (base or which branch)
- View toggle: **Resolved** (default) vs **All Claims** (shows competing assertions)
- If conflicting: all alternative assertions from other sources with resolution explanation
- ChangeEvent history: why and when this assertion was created/modified

### 17.3 Graph canvas requirements

- Drag, zoom, pan
- Click to expand neighbors
- Pin/unpin nodes
- Color coding by entity type (configurable per domain schema)
- Edge labels showing relationship type
- Filter visible node/edge types
- Time slider to view graph at different points in time (resolved view at slider's timestamp)
- Highlight mode for impact/path results
- Export visible subgraph as image or JSON

### 17.4 Editing UX (future phase, architectural consideration)

- Create / update entity forms (auto-generated from domain schema)
- All manual edits stored as AssertionRecords with `source_type = manual` and full audit
- Every edit creates a ChangeEvent with `event_type = "manual_edit"`
- Changes via UI create new assertion versions, never delete history

---

## 18. Proposed Tech Stack & Rationale

### 18.1 Graph database: NebulaGraph (Apache 2.0)

**Why chosen:**
- Apache 2.0 license — fully free, no restrictions on usage or deployment
- Distributed architecture designed for horizontal scalability
- Strong traversal performance for deep dependency chains
- nGQL query language suitable for path/impact/timeline queries
- Supports the AssertionRecord hybrid model (vertices with rich properties + lightweight edges)
- All configuration is code-manageable

**Why not alternatives:**
- Neo4j Community: GPLv3 + no horizontal scaling in community edition; Bloom (visual explorer) requires paid license
- Memgraph: BSL license (source-available, not truly open-source)
- JanusGraph: More operational complexity for POC-scale deployment

**If engineers prefer a different graph DB**, they must ensure: open-source license, support for property graphs with rich vertex properties and indexing, code-manageable schema, adequate traversal performance.

### 18.2 Vector search: Qdrant (Apache 2.0)

**Why chosen:**
- Open-source vector DB for semantic search
- Enables alias resolution, fuzzy matching, abbreviation handling
- Used for cross-entity pattern matching (kNN on feature embeddings)
- Lays foundation for future RAG (document-based knowledge augmentation)
- Simple API, good Python client

### 18.3 Backend: Python + FastAPI

**Why chosen:**
- Fast iteration, strong data processing ecosystem (pandas, openpyxl)
- Natural fit for spec-driven ingestion, ETL, LLM orchestration
- Async support for concurrent queries
- Easy to extend with new tools and connectors

### 18.4 Async job processing: Redis + Celery (or RQ)

**Why chosen:**
- Reliable background processing for imports (which can be long-running)
- Decouples UI responsiveness from data processing
- Redis also usable for caching resolved views

### 18.5 LLM runtime

- **Local (Ollama)**: Simple intents, entity extraction, cost = 0
- **Cloud (OpenAI / Anthropic API)**: Complex multi-step reasoning, nuanced summarization
- **Architecture**: LLM router selects model based on task complexity (configurable)

### 18.6 Frontend: Next.js / React

**Why chosen:**
- Modern, productive framework with large ecosystem
- Server-side rendering for initial load performance
- Strong TypeScript support for complex UI state management

### 18.7 Graph visualization: Cytoscape.js or Sigma.js

**Why chosen:**
- Both are open-source and well-maintained
- Cytoscape.js: better for smaller graphs with rich interaction
- Sigma.js: better for larger graphs (WebGL rendering)
- Decision deferred to UI spike; both integrate with React

### 18.8 Stack changeability principle

If engineers prefer different components, they must preserve:
- Open-source licensing (no paid product licenses)
- AssertionRecord hybrid model with PropertyValue vertices, dual-hash, and ChangeEvent support
- Workspace isolation via `workspace_id` on all core vertices
- Resolved/all-claims view semantics with authority_rank-based resolution
- Temporal versioning and scenario overlays
- Code-first ingestion specs with configurable change detection mode
- Agent guardrails (max calls, timeout, session logging)
- Domain-agnostic architecture (domain = configuration, not code)

---

## 19. System Architecture

### 19.1 Logical components

```
┌─────────────────────────────────────────────────┐
│                   Web UI (React/Next.js)         │
│  Explorer │ Search │ Path │ Impact │ Timeline    │
│  Imports  │ Scenarios │ Ask (NL) │ Conflicts     │
└────────────────────┬────────────────────────────┘
                     │ REST API (view_mode, scenario, at_time)
┌────────────────────┴────────────────────────────┐
│           Backend API (FastAPI)                   │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ Query    │  │ Ingestion│  │ LLM Router    │  │
│  │ Engine   │  │ Engine   │  │ (Tool-based)  │  │
│  └────┬─────┘  └────┬─────┘  └───────┬───────┘  │
│       │              │                │          │
│  ┌────┴──────────────┴────────────────┴───────┐  │
│  │        Domain Schema Registry              │  │
│  │   (loads YAML schemas, specs, rules)       │  │
│  ├────────────────────────────────────────────┤  │
│  │   Resolved View Engine (9.4 algorithm)     │  │
│  └────────────────────────────────────────────┘  │
└────────┬──────────────┬───────────────┬──────────┘
         │              │               │
    ┌────┴────┐   ┌─────┴─────┐  ┌──────┴──────┐
    │ Nebula  │   │  Qdrant   │  │  LLM        │
    │ Graph   │   │  (Vector) │  │ Ollama/Cloud│
    └─────────┘   └───────────┘  └─────────────┘
         │
    ┌────┴────┐
    │  Redis  │  (job queue + cache)
    └─────────┘
```

### 19.2 Data flow: Import

1. User uploads Excel → backend stores raw file → creates import job
2. Worker loads domain schema + ingestion spec for this file
3. Worker parses Excel → staging rows → canonical row serialization → compute **both** `raw_hash` (from canonical serialization per spec) and `normalized_hash` (from normalized values) → compute `assertion_key`
4. Worker compares with existing AssertionRecords (using the spec's `change_detection_mode`):
   - Unchanged → skip
   - Changed → close old AssertionRecord (`valid_to = now`), create new AssertionRecord
   - New → create AssertionRecord with `valid_from = now`
   - Disappeared → close validity
5. Worker creates **one ChangeEvent** for the entire import run, linking to all CREATED and CLOSED AssertionRecords
6. Worker checks for **conflicts** (same `assertion_key`, different `source_id`, overlapping validity)
7. Worker creates/updates **PropertyValue** vertices and HAS_PROPERTY AssertionRecords for entity attributes
8. Worker updates vector index (Qdrant) for searchable fields
9. Worker regenerates convenience properties and convenience edges (if used) from current resolved view
10. Import summary written to ImportRun entity

### 19.3 Data flow: Query

1. User asks question (NL or structured) via UI
2. API layer applies global parameters (`view_mode`, `scenario`, `at_time`)
3. Backend routes to Query Engine or LLM Router
4. If NL: LLM classifies intent, extracts entities, plans query sequence
5. LLM calls tools → backend executes graph/vector queries
6. **Resolved View Engine** applies resolution algorithm (9.4) to filter AssertionRecords
7. Results returned with full provenance (AssertionRecord details + ChangeEvent history)
8. LLM summarizes (if NL mode) with programmatic citation attachment
9. UI renders: text answer + graph visualization + evidence panel

---

## 20. Ingestion Framework & Vibe Coding

### 20.1 Repository layout

```
/project-root
├── /schemas/                 # Domain schema YAMLs
│   ├── restaurant_network.yaml
│   └── (future domains)
├── /specs/                   # Ingestion mapping specs
│   ├── chronic_stores.yaml
│   ├── recipe_circuit_inventory.yaml
│   └── nokia_deployment.yaml
├── /rules/                   # Propagation rules, anomaly checks
│   └── restaurant_network_rules.yaml
├── /aliases/                 # Domain-specific alias dictionaries
│   └── restaurant_network_aliases.yaml
├── /migrations/              # Graph schema migrations
├── /backend/                 # FastAPI + workers
│   ├── /core/                # Universal engine (query, ingestion, LLM, resolved view)
│   └── /api/                 # API routes
├── /frontend/                # Next.js app
├── /infra/                   # docker-compose, env templates
│   ├── docker-compose.yml
│   └── .env.template
├── /data/                    # Raw imported files (gitignored)
│   └── /raw/
├── /tests/
│   ├── /ingestion/           # Spec unit tests, hash stability
│   ├── /queries/             # Path, impact, change, timeline correctness
│   ├── /conflicts/           # Conflict detection and resolution
│   └── /grounding/           # LLM grounding tests
└── /docs/
```

### 20.2 Spec-driven ingestion

Each ingestion spec defines:
- Input file pattern + sheet selection
- Column mappings → entity properties
- Entity key construction rules (how to build `assertion_key`)
- Relationship creation rules (which columns define edges)
- Normalization rules (per-field: casing, whitespace, null handling, number format, date format)
- Hash computation rules (which columns contribute to `raw_hash` and `normalized_hash`)
- `change_detection_mode`: `strict` or `normalized`

### 20.3 Determinism requirement

Same input file + same spec version + same schema version = identical graph state. This is testable and must be verified in CI. Both `raw_hash` and `normalized_hash` computation must be deterministic.

### 20.4 Import execution

```bash
# CLI-driven import (vibe coding friendly)
make import FILE=data/raw/chronic_stores.xlsx SPEC=specs/chronic_stores.yaml

# Or via API
curl -X POST /api/imports -F file=@chronic_stores.xlsx -F spec=chronic_stores
```

---

## 21. Deployment (Docker-first)

### 21.1 POC docker-compose services

| Service | Image | Purpose |
|---------|-------|---------|
| nebula-graphd | vesoft/nebula-graphd | Graph query service |
| nebula-metad | vesoft/nebula-metad | Graph metadata |
| nebula-storaged | vesoft/nebula-storaged | Graph storage |
| nebula-studio | vesoft/nebula-graph-studio | Admin/debug UI |
| qdrant | qdrant/qdrant | Vector search |
| redis | redis:alpine | Job queue + cache |
| backend-api | custom | FastAPI app |
| worker | custom | Celery/RQ worker |
| frontend | custom | Next.js app |

### 21.2 Environment configuration

- `.env` for all configuration: endpoints, API keys (Ollama, cloud LLM), feature flags
- Domain schema and specs are mounted as volumes (not baked into images)
- Secrets management via Vault (future)

### 21.3 One-command startup

```bash
docker-compose up -d
# System is ready at http://localhost:3000
```

---

## 22. Non-Functional Requirements

| Requirement | POC | Production |
|-------------|-----|------------|
| **Cost** | No paid licenses; cloud LLM tokens only | Same |
| **Deployability** | Docker Compose | Kubernetes-ready |
| **Scalability** | Hundreds of entities | Millions of nodes/edges |
| **Performance** | Interactive queries < 2s | < 500ms for cached |
| **Reliability** | Ingestion idempotent | HA, backup, monitoring |
| **Auditability** | Every fact traceable to source via AssertionRecord + ChangeEvent | Full audit log |
| **Security** | No auth | RBAC, SSO, audit |
| **Extensibility** | Schema + spec changes | Plugin architecture |
| **Multi-domain** | Core supports workspaces (shared space + workspace_id); POC loads 2nd schema, verifies isolation via API prefix | Full multi-workspace UI + cross-workspace queries |

---

## 23. Testing & Validation

### 23.1 Ingestion tests
- Mapping spec unit tests (columns → entities correctly)
- **Dual-hash stability tests** (same input → same `raw_hash` AND same `normalized_hash`)
- Change detection tests: strict mode catches formatting changes; normalized mode ignores them
- ChangeEvent creation tests (every import change produces a ChangeEvent)
- Conflict detection tests (overlapping validity intervals from different sources)

### 23.2 Graph query tests
- Path correctness (known topology → expected paths)
- Impact traversal correctness (known propagation rules → expected blast radius with logged evidence per step)
- Change diff correctness (two imports → expected diff with ChangeEvent context)
- Temporal query correctness (state at time T matches expectations using resolved view)
- Resolved view correctness (authority + recency + confidence ranking produces expected winner)
- All-claims view completeness (returns all competing assertions)

### 23.3 LLM grounding tests
- Responses contain only evidence-backed statements
- "No data" responses when graph has no relevant data
- Multi-step reasoning produces correct tool call sequences
- Entity resolution maps ambiguous references to correct IDs

### 23.4 Domain-agnostic tests
- Adding a second domain schema works without code changes
- Ingesting data into a new domain uses only spec files
- Queries work correctly across different domain schemas
- Workspace data isolation confirmed

### 23.5 Conflict and reconciliation tests
- Conflict correctly detected only when validity intervals overlap
- Non-overlapping temporal assertions are not flagged as conflicts
- Manual override correctly prioritized in resolved view

### 23.6 UI tests
- Smoke tests for main flows (search, explore, path, impact, import)
- Evidence panel shows correct source references
- View mode toggle (resolved / all claims) produces different outputs

---

## 24. Milestones

### M0 — Foundations (1-2 weeks)
- Docker stack running (NebulaGraph, Qdrant, Redis, backend shell, frontend shell)
- Core graph schema: AssertionRecord vertex, PropertyValue vertex, ChangeEvent vertex, ASSERTED_REL edges, indexes (including workspace_id composites)
- Workspace isolation: `workspace_id` on all vertices, API prefix `/api/w/{wid}/`, query-level filtering
- Domain schema registry implemented (load YAML, validate)
- Ingestion spec format defined (including dual-hash with canonical row serialization and change_detection_mode)
- Resolved View Engine implemented (resolution algorithm with authority_rank)

### M1 — POC Ingestion + Explorer (2-4 weeks)
- Ingest 3 Excel files via specs (AssertionRecords for relationships AND properties + one ChangeEvent per import)
- HAS_PROPERTY → PropertyValue assertions working for entity attributes
- Dual-hash computation (canonical row serialization) and change detection working
- Entity resolution with alias support
- Graph explorer UI (expand, pin, filter, search) using resolved view
- Entity detail panel with evidence (AssertionRecord details for both relationships and properties)
- Import run management (upload, status, history, diff)

### M2 — Path / Impact / Change / Timeline (2-4 weeks)
- Deterministic query endpoints (path, impact, change, timeline)
- Propagation rules engine (YAML-defined rules, step-by-step evidence logging)
- Path view and Impact view in UI
- Timeline view with ChangeEvent context
- Change analysis between import runs

### M3 — Scenarios + NL Interface (2-4 weeks)
- Scenario overlay semantics (create, apply delta, query) with ChangeEvent tracking
- Scenario comparison view in UI (resolved view side-by-side)
- LLM tool-based orchestration (intent → tools → summary)
- Agent guardrails enforced (max tool calls, timeout, all-claims policy)
- Agent session logging (full tool call chain stored as JSON)
- NL "Ask" interface with citations
- Multi-step query support
- view_mode toggle in UI (resolved / all claims)

### M4 — Intelligence + Reconciliation (2-4 weeks)
- Multi-source conflict detection (temporal overlap check) and resolution UI
- RCA query type (ChangeEvent correlation + upstream traversal)
- Anomaly detection (rule-based checks)
- Cross-entity pattern matching (feature embedding + kNN via Qdrant)
- Conflicts dashboard

### M5 — Hardening + Extensibility (ongoing)
- Second domain schema loaded and verified (universality proof)
- Additional connectors (API-based ingestion)
- Document RAG (optional)
- RBAC / SSO
- Performance optimization for large graphs
- Convenience edge materialization (if needed for performance)

---

## 25. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Schema churn as new data sources appear | High | Spec-driven ingestion + schema versioning + migrations |
| Entity resolution ambiguity (aliases, inconsistent naming) | High | Canonical ID rules + alias dictionary + vector search + human review |
| LLM hallucinations bypass grounding | Critical | Tool-based orchestration + evidence enforcement at backend + automated grounding tests |
| Multi-source conflicts create confusion | Medium | Source authority registry + temporal conflict logic + conflict visibility UI + manual resolution |
| UI performance on large graphs | Medium | Subgraph sampling + progressive expansion + WebGL renderer + server-side filtering + convenience edges |
| Domain schema too rigid for new use cases | Medium | Schema extensibility by design + inheritance + optional properties |
| NebulaGraph operational complexity | Medium | Docker-managed deployment + documented runbooks + adapter layer for potential graph DB migration |
| Propagation rules become too complex to maintain | Low (POC) | YAML-defined rules with version control; step-by-step evidence logging for debugging; determinism tests |
| AssertionRecord vertex count grows large | Medium | Archival strategy for closed assertions (valid_to far in past); index optimization; partitioning |
| Dual-hash computation overhead | Low | Hashing is fast; both hashes computed in single pass during ingestion |

---

## 26. Open Questions

1. **Assertion key construction**: Exact formula per table (depends on real Excel columns) — to be defined when analyzing actual files during M0. Property assertions use the pattern defined in 9.8.
2. **Graph visualization library**: Cytoscape.js vs Sigma.js — to be decided during UI spike in M1
3. **Project milestones representation**: Properties (via HAS_PROPERTY assertions) on Location-Project pairs vs separate Milestone entities — to be decided based on data complexity
4. **LLM model selection for local inference**: Which Ollama model balances quality vs VRAM (24GB constraint) — to be benchmarked during M3
5. **Convenience property materialization strategy**: How often to regenerate convenience properties on Entity vertices — on every import, on demand, or background refresh — to be decided during M1 based on performance testing

---

## 27. Acceptance Criteria (POC)

The POC is accepted when:

1. **Ingestion**: The system ingests three example Excel workbooks via code-defined specs, correctly creating AssertionRecord vertices (for relationships AND properties) and one ChangeEvent per import run
2. **Dual-hash**: Both `raw_hash` (canonical row serialization) and `normalized_hash` are computed; change detection works correctly in the spec's declared mode
3. **Property assertions**: Entity attributes (speed, cost, status) are stored as HAS_PROPERTY → PropertyValue assertions with full evidence tracking and temporal versioning
4. **Entity resolution**: Legacy alias IDs are correctly linked to canonical location IDs
5. **Graph exploration**: A user can visually explore the graph in resolved view, expand neighbors, filter by type, and search by location ID, alias, or provider name
6. **Path queries**: The system returns top-K dependency paths with evidence per edge (AssertionRecord details)
7. **Impact analysis**: Given a provider outage scenario, the system correctly identifies affected locations using propagation rules and distinguishes those with backup connections. Evidence includes fired rule steps.
8. **Change tracking**: Diffs between two import runs correctly show added, removed, and modified assertions with ChangeEvent context
9. **Timeline**: A timeline view shows the history of changes for a selected entity with ChangeEvent details
10. **What-if**: A scenario branch can be created, modified, and queried without altering base truth; side-by-side comparison works
11. **NL interface**: Natural language questions produce answers that are strictly evidence-backed with source references. Agent sessions are logged with full tool call chains.
12. **View modes**: Resolved view and all-claims view produce correct, different outputs for the same entity
13. **Workspace isolation**: All API endpoints use `/api/w/{workspace_id}/` prefix; loading a second trivial schema demonstrates data isolation without code changes; queries scoped to workspace A never return workspace B data

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Assertion** | An evidence-backed statement that a relationship or property exists, with full provenance and temporal metadata |
| **AssertionRecord** | The physical vertex in the graph database that stores an assertion (see 9.3) |
| **Assertion key** | A stable identifier for "the same conceptual fact" across imports, enabling change detection |
| **All-claims view** | API/UI mode showing all competing assertions for a given relationship, regardless of resolution |
| **Authority rank** | Integer priority of a data source within its domain. **Lower number = higher authority** (rank 1 is most trusted). Replaces "authority_level" from earlier drafts. |
| **Base truth** | The `scenario_id = "base"` layer representing the actual current state of the world |
| **Blast radius** | The set of entities affected by a failure or change at a given entity |
| **ChangeEvent** | A vertex recording that something caused assertions to be created, modified, or closed. One per import run or manual action (see 9.6) |
| **Convenience edge** | An optional materialized direct edge between entities, derived from resolved AssertionRecords for fast traversal |
| **Convenience property** | An optional copy of a resolved property value stored directly on an Entity vertex for fast filtering/display |
| **Domain schema** | A YAML configuration defining entity types, relationship types, and property schemas for a specific use case |
| **Evidence** | The source reference (file, sheet, row, API response) that supports an assertion |
| **Import run** | A single execution of data ingestion from a source, producing a set of AssertionRecords and one ChangeEvent |
| **Normalized hash** | Hash computed after applying normalization rules; detects semantically meaningful changes |
| **Propagation rule** | A domain-defined rule specifying how an effect (failure, degradation) travels through relationships, with step-by-step evidence logging |
| **PropertyValue** | A core vertex type storing a typed attribute value (e.g., speed="100Mbps"), linked to entities via HAS_PROPERTY assertions (see 9.8) |
| **Raw hash** | Hash computed from canonical serialization of source row cell values; detects any data change while ignoring file-level noise (see 9.2.1) |
| **Resolved view** | API/UI mode showing the single preferred assertion per relationship, selected by authority_rank/recency/confidence algorithm |
| **Scenario** | A named overlay of assertions used for what-if analysis without modifying base truth |
| **Session log** | JSON record of an agent session: question, intent, tool calls, results, grounding check (see 15.7) |
| **Workspace** | An isolated domain environment with its own schema, data, and configuration. Isolated via `workspace_id` on all vertices + API path prefix (see 7.4) |

---

## Appendix B: POC Domain Schema Summary (Restaurant Network)

**Entity types**: Location, LocationAlias, Provider, Connection, Device, Host, Project, ImportRun

**Core vertices (universal)**: AssertionRecord, PropertyValue, ChangeEvent, Source

**Key relationships** (via AssertionRecords):
- Location → HAS_ALIAS → LocationAlias
- Location → HAS_CONNECTION {role} → Connection
- Connection → PROVIDED_BY → Provider
- Location → HAS_DEVICE → Device
- Location → HAS_HOST → Host
- Location → PARTICIPATES_IN {status, dates} → Project
- Project → USES_PROVIDER → Provider

**Property assertions** (via HAS_PROPERTY → PropertyValue):
- Connection → HAS_PROPERTY → PropertyValue(speed="100Mbps")
- Connection → HAS_PROPERTY → PropertyValue(cost=49.99)
- Location → HAS_PROPERTY → PropertyValue(status="active")
- Device → HAS_PROPERTY → PropertyValue(firmware="v3.2.1")

**Causal tracking** (via ChangeEvents):
- ImportRun → TRIGGERED_BY ← ChangeEvent → CREATED/CLOSED → AssertionRecord
- Project → TRIGGERED_BY ← ChangeEvent → CREATED/CLOSED → AssertionRecord
- To find affected entities: ChangeEvent → CREATED/CLOSED → AssertionRecord → ASSERTED_REL → Entity

**Primary key**: `location_id` (4-digit string)

**Data sources** (with authority_rank per domain):
1. Chronic Stores.xlsx → Location entities + properties (authority_rank=1 for Location data)
2. RecipeCircuitInventory.xlsx → Connection + Provider + Device entities + relationships (authority_rank=1 for connectivity data)
3. Nokia Deployment Activities Tracker.xlsx → Project entity + PARTICIPATES_IN relationships (authority_rank=1 for project data)

**Change detection mode**: `normalized` (recommended for POC; `strict` available for audit)

---

## Appendix C: Revision History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | — | Initial POC-focused PRD (restaurant-specific) |
| v2.0 | — | Universal platform redesign: domain-agnostic core, workspaces, reconciliation, propagation rules, RCA, anomaly detection, causal tracking, multi-step agent reasoning |
| v2.1 | — | Physical storage model (AssertionRecord vertex); dual-hash change detection; ChangeEvent vertex for causal tracking; temporal conflict definition; resolved/all-claims view; propagation rules DSL; cross-entity pattern matching clarified; multi-workspace POC scope fixed |
| v2.2 | — | Workspace isolation technical binding (shared space + workspace_id + API prefix); property assertions via HAS_PROPERTY → PropertyValue vertex; authority_rank naming fix; ChangeEvent granularity decided (one per import/action); raw_hash as canonical row serialization; agent mode guardrails |

---

*End of PRD v2.2*
