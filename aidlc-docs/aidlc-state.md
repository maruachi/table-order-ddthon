# AI-DLC State Tracking

## Project Information
- **Project Type**: Greenfield
- **Project Name**: 테이블오더 서비스 (Table Order Service)
- **Start Date**: 2026-09-07T03:08:55Z
- **Current Stage**: CONSTRUCTION - U0 complete; U2 Menu (이원종) NFR Design complete — awaiting approval before Code Generation; U1/U3/U4 parallel dev ready

## Workspace State
- **Existing Code**: No
- **Programming Languages**: None detected
- **Build System**: None detected
- **Project Structure**: Empty (requirements docs only)
- **Reverse Engineering Needed**: No
- **Workspace Root**: /Users/dgyim/works/aidlc-workshop-day1/table-order-ddthon

## Code Location Rules
- **Application Code**: Workspace root (NEVER in aidlc-docs/)
- **Documentation**: aidlc-docs/ only
- **Structure patterns**: See code-generation.md Critical Rules

## Extension Configuration
| Extension | Enabled | Decided At |
|---|---|---|
| Security Baseline | No | Requirements Analysis |
| Resiliency Baseline | No | Requirements Analysis |
| Property-Based Testing | No | Requirements Analysis |

## Technology Decisions
- **Backend**: Python (FastAPI)
- **Frontend**: Vue (SPA)
- **Database**: SQLite
- **Deployment/Run target**: Local development (workshop/demo)
- **Store scope**: Multi-store (multi-tenant via store identifier)
- **Scale**: Medium (multiple stores, dozens of tables each)
- **Initial data**: Seed scripts + Admin UI registration
- **Menu images**: Image URL reference only (no upload/optimization)

## Execution Plan Summary
- **Stages to Execute**: Application Design, Units Generation, Functional Design, NFR Requirements, NFR Design, Code Generation, Build and Test
- **Stages to Skip**: Reverse Engineering (Greenfield), Infrastructure Design (local dev only)
- **Parallel Dev**: 4 devs (임동규·이원종·최지영·이재환) split by unit; unit boundaries set in Units Generation

## Stage Progress
### 🔵 INCEPTION PHASE
- [x] Workspace Detection
- [ ] Reverse Engineering (N/A - Greenfield)
- [x] Requirements Analysis
- [x] User Stories
- [x] Workflow Planning
- [x] Application Design
- [x] Units Generation

### 🟢 CONSTRUCTION PHASE (per-unit loop)
**U0 Platform/Common** (foundation — before parallel dev):
- [x] Functional Design (U0)
- [x] NFR Requirements (U0)
- [x] NFR Design (U0)
- [x] Infrastructure Design (U0) - SKIP (local dev only)
- [x] Code Generation (U0) — verified: pytest 5 passed, app boots, both SPAs build

**Parallel units (pending — Sprint 0 contracts fixed by U0):**
- [ ] U1 Auth (임동규) — Functional Design → NFR → Code Generation
- [~] U2 Menu (이원종) — [x] Functional Design → [x] NFR Requirements → [x] NFR Design → [ ] Code Generation  *(branch: u2-menu)*
- [ ] U3 Order+Cart (최지영) — Functional Design → NFR → Code Generation
- [ ] U4 Session+Realtime (이재환) — Functional Design → NFR → Code Generation

- [ ] Build and Test - EXECUTE (after all units)

### 🟡 OPERATIONS PHASE
- [ ] Operations (placeholder)
