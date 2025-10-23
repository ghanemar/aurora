# GitHub Issues Creation Plan

## Summary
Created issues #1-#11 so far. Below is the complete list of remaining issues to create, organized by epic and phase.

## Created Issues (11 total)

### Epic 1: Foundation & Config
- ✅ #1 - Setup Python project structure with Poetry
- ✅ #2 - Implement configuration loaders for chains and providers
- ✅ #3 - Setup PostgreSQL database and Docker Compose
- ✅ #4 - Implement JWT authentication and user models
- ✅ #5 - Implement RBAC middleware with partner scoping

### Epic 2: Ingestion & Normalization - Data Layer
- ✅ #6 - Create SQLAlchemy models for chain registry and configuration
- ✅ #7 - Create SQLAlchemy models for staging layer
- ✅ #8 - Create SQLAlchemy models for canonical data layer
- ✅ #9 - Create SQLAlchemy models for computation and agreements layer
- ✅ #10 - Setup Alembic and create initial database migrations

### Epic 2: Ingestion & Normalization - Adapters
- ✅ #11 - Implement base adapter interface and provider factory

## Remaining Issues to Create

### Phase 3: Adapters (Solana)
- [ ] #12 - Implement Solana Beach fees adapter
- [ ] #13 - Implement Jito MEV adapter
- [ ] #14 - Implement Solana RPC rewards adapter
- [ ] #15 - Implement Stakewiz metadata adapter
- [ ] #16 - Create adapter integration tests with mocked responses

### Phase 4: Ingestion & Normalization
- [ ] #17 - Implement ingestion orchestration service
- [ ] #18 - Implement staging payload repository
- [ ] #19 - Implement normalization service (staging → canonical)
- [ ] #20 - Implement reconciliation logic and drift detection
- [ ] #21 - Create Prefect/RQ ingestion jobs
- [ ] #22 - Implement ingestion health monitoring

### Phase 5: Commission Engine
- [ ] #23 - Implement base repository pattern with RBAC scoping
- [ ] #24 - Implement canonical data repositories
- [ ] #25 - Implement validator P&L computation service
- [ ] #26 - Implement commission engine with attribution strategies
- [ ] #27 - Implement agreement management service
- [ ] #28 - Implement override workflow
- [ ] #29 - Create recomputation background jobs

### Phase 6: API & Auth
- [ ] #30 - Implement FastAPI application structure and middleware stack
- [ ] #31 - Implement chain and period endpoints
- [ ] #32 - Implement validator P&L endpoints with RBAC
- [ ] #33 - Implement partner commission endpoints with scoping
- [ ] #34 - Implement agreement CRUD endpoints
- [ ] #35 - Implement operations endpoints (recompute, health)
- [ ] #36 - Create comprehensive API integration tests
- [ ] #37 - Implement API documentation with OpenAPI/Swagger

### Phase 7: UI & Deployment
- [ ] #38 - Setup React frontend project structure
- [ ] #39 - Implement admin dashboard and navigation
- [ ] #40 - Implement validator P&L viewer
- [ ] #41 - Implement partner commission viewer
- [ ] #42 - Implement agreement editor
- [ ] #43 - Implement partner portal (read-only)
- [ ] #44 - Create Dockerfile and docker-compose for production
- [ ] #45 - Setup Nginx configuration with TLS
- [ ] #46 - Create deployment runbooks

### Phase 8: Testing & Documentation
- [ ] #47 - Achieve >80% unit test coverage
- [ ] #48 - Create end-to-end integration test suite
- [ ] #49 - Implement structured logging with correlation IDs
- [ ] #50 - Setup Prometheus metrics export
- [ ] #51 - Create operational runbooks (deployment, backup, troubleshooting)
- [ ] #52 - Create user documentation for admin and partner portals
- [ ] #53 - Perform load testing and API latency validation

### Epic 6: Ethereum Enablement (M1)
- [ ] #54 - Add Ethereum chain configuration
- [ ] #55 - Implement EVM block fees adapter
- [ ] #56 - Implement MEV relay adapter for PBS tips
- [ ] #57 - Implement consensus API rewards adapter
- [ ] #58 - Implement beacon API metadata adapter
- [ ] #59 - Extend normalization for EVM (wei conversion)
- [ ] #60 - Test cross-chain RBAC scoping
- [ ] #61 - Update UI for multi-chain filtering

## Issue Complexity Distribution

**Low (1-2 days):** 15 issues
**Medium (3-5 days):** 30 issues
**High (6-10 days):** 16 issues

**Total Estimated Effort:** ~230-320 developer-days (11-16 weeks with 1 developer)

## Priority Order for Creation

### P0 - Critical Path (Must create immediately)
1. Solana adapters (#12-15) - Blocks ingestion
2. Ingestion services (#17-19) - Blocks data flow
3. Commission engine (#24-26) - Core business logic
4. API endpoints (#30-35) - External interface

### P1 - High Priority (Create soon)
5. Testing infrastructure (#16, #36, #47-48) - Quality assurance
6. Reconciliation (#20) - Data integrity
7. Repository pattern (#23-24) - Data access layer

### P2 - Medium Priority (Can defer slightly)
8. UI components (#38-43) - User interface
9. Deployment (#44-46) - Infrastructure
10. Documentation (#51-52) - Operational support

### P3 - Future (M1 phase)
11. Ethereum adapters (#54-61) - Multi-chain expansion

## Labels Applied to Each Issue

**Epic Labels:**
- epic/foundation
- epic/ingestion
- epic/commission-engine
- epic/api-ui
- epic/testing-ops
- epic/ethereum

**Phase Labels:**
- phase-1 through phase-8

**Component Labels:**
- component/database
- component/adapters
- component/api
- component/services
- component/auth
- component/ui
- component/infrastructure

**Complexity Labels:**
- complexity/low
- complexity/medium
- complexity/high

**Type Labels:**
- type/feature
- type/infrastructure
- type/documentation

---

**Next Action:** Continue creating issues #12-#61 using the batch creation script or create them individually with proper labels and detailed specifications.
