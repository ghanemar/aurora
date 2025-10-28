# MVP Implementation Order

**Project**: Aurora Admin Dashboard MVP
**Timeline**: 17 developer-days (2-3 weeks calendar time)
**Start Date**: TBD
**Target Completion**: 2-3 weeks from start

## Critical Path Overview

```
Day 1-3: Backend Foundation (CRITICAL - blocks all API work)
  ↓
Day 4-5: Schemas & Repositories (CRITICAL - blocks services)
  ↓
Day 6-7: Services & Endpoints (CRITICAL - blocks frontend data flow)
  ↓
Day 8: Data Seeding (CRITICAL - blocks testing)
  ↓
Day 9-10: Frontend Auth (CRITICAL - blocks all pages)
  ↓
Day 11-15: Admin Pages (PARALLEL - can work independently)
  ↓
Day 16-17: Testing & Polish (CRITICAL - final validation)
  ↓
Optional: Real Data Integration (if time permits)
```

## Dependencies Graph

```
[User Auth & DB] ────────┐
         │               │
         ↓               │
[Schemas & Repos] ───────┤
         │               │
         ↓               │
[Services] ──────────────┤
         │               │
         ↓               │
[API Endpoints] ─────────┤
         │               │
         ↓               │
[Data Seeding] ──────────┤
                         │
                    (API Ready)
                         │
                         ↓
            [Frontend Auth Setup] ────────┐
                         │                │
                         ↓                │
            [Dashboard Page] ─────────────┤
            [Validators Page] ────────────┤
            [Partners Page] ──────────────┤
            [Agreements Page] ────────────┤
            [Commissions Page] ───────────┤
                                          │
                                     (All Pages)
                                          │
                                          ↓
                            [Testing & Polish]
```

---

## Phase 1: Backend Foundation (Days 1-3)
**Critical Path**: YES - Blocks all subsequent backend work
**Can Parallelize**: No
**Estimated Effort**: 3 days

### Day 1: Database & Auth Models
**File**: `src/core/models/users.py`
- [ ] Create User model with UUID primary key
- [ ] Add UserRole enum (ADMIN, PARTNER)
- [ ] Include password_hash, role, is_active fields
- [ ] Add unique constraints on username and email
- [ ] Create foreign key relationship to partners table

**File**: `alembic/versions/XXX_add_users.py`
- [ ] Create Alembic migration for users table
- [ ] Add indexes on username, email, partner_id
- [ ] Test migration up and down

**Dependencies**:
- Requires: Database setup (already complete)
- Blocks: Auth endpoints, all API endpoints

**Acceptance Criteria**:
- User model defined with proper types
- Migration creates users table successfully
- Can rollback migration cleanly

---

### Day 2: Auth Endpoints & JWT
**File**: `src/api/auth.py`
- [ ] Implement `POST /api/v1/auth/login` endpoint
- [ ] Hash password verification with bcrypt
- [ ] Generate JWT tokens with python-jose
- [ ] Add token expiration (24 hours)
- [ ] Implement `GET /api/v1/auth/me` endpoint

**File**: `src/core/security.py`
- [ ] Create password hashing utilities
- [ ] Create JWT token generation function
- [ ] Create JWT token verification function
- [ ] Add get_current_user dependency

**File**: `src/api/dependencies.py`
- [ ] Create require_role decorator
- [ ] Create get_current_admin dependency
- [ ] Create get_current_partner dependency

**Dependencies**:
- Requires: User model (Day 1)
- Blocks: All protected endpoints

**Acceptance Criteria**:
- Can login with valid credentials
- Receive JWT token
- Token validates on protected endpoints
- Invalid tokens rejected with 401

---

### Day 3: FastAPI Setup & CORS
**File**: `src/main.py`
- [ ] Create FastAPI application instance
- [ ] Configure CORS for localhost:3000
- [ ] Add auth router
- [ ] Add health check endpoint
- [ ] Configure exception handlers

**File**: `tests/integration/test_auth_flow.py`
- [ ] Test login flow end-to-end
- [ ] Test token validation
- [ ] Test role-based access control
- [ ] Test invalid credentials rejection

**Dependencies**:
- Requires: Auth endpoints (Day 2)
- Blocks: All API integration

**Acceptance Criteria**:
- FastAPI server runs on port 8000
- Can login via curl/Postman
- CORS allows frontend requests
- Health check returns 200

---

## Phase 2: Core API - Schemas & Repositories (Days 4-5)
**Critical Path**: YES - Blocks services and frontend
**Can Parallelize**: Schemas and Repos can be done together
**Estimated Effort**: 2 days

### Day 4: Request/Response Schemas
**File**: `src/api/schemas/validators.py`
- [ ] ValidatorCreateRequest schema
- [ ] ValidatorUpdateRequest schema
- [ ] ValidatorResponse schema with relationships
- [ ] ValidatorListResponse with pagination

**File**: `src/api/schemas/partners.py`
- [ ] PartnerCreateRequest schema
- [ ] PartnerUpdateRequest schema
- [ ] PartnerResponse schema
- [ ] PartnerListResponse with pagination

**File**: `src/api/schemas/agreements.py`
- [ ] AgreementCreateRequest schema
- [ ] AgreementUpdateRequest schema
- [ ] AgreementResponse schema with partner info
- [ ] AgreementListResponse

**File**: `src/api/schemas/commissions.py`
- [ ] CommissionLineResponse schema
- [ ] CommissionSummaryResponse schema
- [ ] CommissionFilterRequest schema

**Dependencies**:
- Requires: Existing models (already complete)
- Blocks: API endpoints

**Acceptance Criteria**:
- All schemas have proper Pydantic validation
- Field constraints match database constraints
- Response schemas include computed fields

---

### Day 5: Repository Layer
**File**: `src/core/repositories/validators.py`
- [ ] get_all() with pagination
- [ ] get_by_id(validator_id)
- [ ] create(data)
- [ ] update(validator_id, data)
- [ ] delete(validator_id)
- [ ] get_by_chain(chain_id)

**File**: `src/core/repositories/partners.py`
- [ ] get_all() with pagination
- [ ] get_by_id(partner_id)
- [ ] create(data)
- [ ] update(partner_id, data)
- [ ] delete(partner_id)
- [ ] get_active_partners()

**File**: `src/core/repositories/agreements.py`
- [ ] get_by_partner(partner_id)
- [ ] get_active_for_period(partner_id, period)
- [ ] create(data)
- [ ] update(agreement_id, data)
- [ ] deactivate(agreement_id)

**Dependencies**:
- Requires: Existing models
- Blocks: Services

**Acceptance Criteria**:
- All CRUD operations work
- Pagination works correctly
- Relationships eagerly loaded where needed
- Database queries optimized (N+1 avoided)

---

## Phase 3: Core API - Services & Endpoints (Days 6-7)
**Critical Path**: YES - Blocks frontend functionality
**Can Parallelize**: Services first, then endpoints (sequential)
**Estimated Effort**: 2 days

### Day 6: Service Layer
**File**: `src/core/services/validators.py`
- [ ] list_validators(chain_id, page, size)
- [ ] get_validator(validator_id)
- [ ] create_validator(data, current_user)
- [ ] update_validator(validator_id, data, current_user)
- [ ] delete_validator(validator_id, current_user)

**File**: `src/core/services/partners.py`
- [ ] list_partners(page, size)
- [ ] get_partner(partner_id)
- [ ] create_partner(data, current_user)
- [ ] update_partner(partner_id, data, current_user)
- [ ] delete_partner(partner_id, current_user)

**File**: `src/core/services/agreements.py`
- [ ] list_agreements(partner_id, page, size)
- [ ] create_agreement(data, current_user)
- [ ] update_agreement(agreement_id, data, current_user)
- [ ] deactivate_agreement(agreement_id, current_user)

**File**: `src/core/services/commissions.py`
- [ ] calculate_commissions(partner_id, period_id)
- [ ] get_commission_summary(partner_id, start_date, end_date)
- [ ] Logic: Fetch ValidatorPnL for validators in agreement
- [ ] Logic: Apply commission rate from agreement
- [ ] Logic: Return CommissionLine for each validator

**Dependencies**:
- Requires: Repositories (Day 5)
- Blocks: API endpoints

**Acceptance Criteria**:
- All business logic in services
- Services validate business rules
- Commission calculations correct
- Error handling comprehensive

---

### Day 7: API Endpoints
**File**: `src/api/routers/validators.py`
- [ ] GET /api/v1/validators - list with pagination
- [ ] GET /api/v1/validators/{id} - get single
- [ ] POST /api/v1/validators - create (admin only)
- [ ] PUT /api/v1/validators/{id} - update (admin only)
- [ ] DELETE /api/v1/validators/{id} - delete (admin only)

**File**: `src/api/routers/partners.py`
- [ ] GET /api/v1/partners - list with pagination
- [ ] GET /api/v1/partners/{id} - get single
- [ ] POST /api/v1/partners - create (admin only)
- [ ] PUT /api/v1/partners/{id} - update (admin only)
- [ ] DELETE /api/v1/partners/{id} - soft delete (admin only)

**File**: `src/api/routers/agreements.py`
- [ ] GET /api/v1/partners/{partner_id}/agreements - list
- [ ] POST /api/v1/agreements - create (admin only)
- [ ] PUT /api/v1/agreements/{id} - update (admin only)
- [ ] DELETE /api/v1/agreements/{id} - deactivate (admin only)

**File**: `src/api/routers/commissions.py`
- [ ] GET /api/v1/commissions/calculate - calculate for partner/period
- [ ] GET /api/v1/commissions/summary - summary for date range

**File**: `src/main.py`
- [ ] Register all routers with /api/v1 prefix

**Dependencies**:
- Requires: Services (Day 6), Schemas (Day 4)
- Blocks: Frontend integration

**Acceptance Criteria**:
- All endpoints return correct status codes
- Validation errors return 422 with details
- Auth errors return 401/403 appropriately
- All endpoints documented in OpenAPI

---

## Phase 4: Data Seeding (Day 8)
**Critical Path**: YES - Blocks frontend testing
**Can Parallelize**: No
**Estimated Effort**: 1 day

### Day 8: Seed Script
**File**: `scripts/seed_mvp_data.py`
- [ ] Create admin user (username: admin, password: admin123)
- [ ] Seed 3 Solana validators with real vote pubkeys
- [ ] Seed 2 partners with contact info
- [ ] Seed 2 active agreements (one per partner)
- [ ] Add partner wallets to agreements
- [ ] Seed ValidatorPnL data for last 3 epochs
- [ ] Include fees, MEV, rewards data
- [ ] Seed CanonicalValidatorMEV records
- [ ] Seed CanonicalValidatorFees records

**Dependencies**:
- Requires: All models, migrations complete
- Blocks: Frontend testing with real data

**Acceptance Criteria**:
- Script is idempotent (can run multiple times)
- All foreign keys valid
- Data realistic and consistent
- Can login with seeded admin user
- Commission calculations work with seeded data

---

## Phase 5: Frontend Setup & Auth (Days 9-10)
**Critical Path**: YES - Blocks all UI pages
**Can Parallelize**: No
**Estimated Effort**: 2 days

### Day 9: React Project Setup
**Directory**: `frontend/`
- [ ] Initialize Vite + React + TypeScript project
- [ ] Install dependencies (MUI, React Router, React Query, Axios)
- [ ] Configure TypeScript strict mode
- [ ] Set up folder structure (components, pages, hooks, services)
- [ ] Configure Vite proxy for API (port 8000)
- [ ] Create .env file with API_URL

**File**: `frontend/src/services/api.ts`
- [ ] Configure Axios instance with base URL
- [ ] Add request interceptor for JWT token
- [ ] Add response interceptor for 401 handling
- [ ] Create API error types

**File**: `frontend/src/types/index.ts`
- [ ] Define User type
- [ ] Define AuthResponse type
- [ ] Define ApiError type

**Dependencies**:
- Requires: Backend API running (Day 7)
- Blocks: All frontend pages

**Acceptance Criteria**:
- Frontend dev server runs on port 3000
- Can make API requests to backend
- TypeScript compiles without errors
- MUI theme configured

---

### Day 10: Auth Flow
**File**: `frontend/src/contexts/AuthContext.tsx`
- [ ] Create AuthContext with login/logout
- [ ] Store JWT in localStorage
- [ ] Provide current user state
- [ ] Handle token expiration

**File**: `frontend/src/pages/LoginPage.tsx`
- [ ] Login form with username/password
- [ ] Form validation
- [ ] Error display
- [ ] Redirect to dashboard on success

**File**: `frontend/src/components/PrivateRoute.tsx`
- [ ] Check authentication
- [ ] Redirect to login if not authenticated
- [ ] Protect admin routes

**File**: `frontend/src/App.tsx`
- [ ] Set up React Router
- [ ] Define routes (/, /login, /dashboard, etc.)
- [ ] Wrap with AuthProvider
- [ ] Add navigation guard

**Dependencies**:
- Requires: React setup (Day 9), Auth API (Day 2-3)
- Blocks: All protected pages

**Acceptance Criteria**:
- Can login with seeded admin user
- Token persists across page refresh
- Redirect to login when token expires
- Can logout successfully

---

## Phase 6: Admin Pages - Dashboard & Validators (Days 11-12)
**Critical Path**: NO - Can work in parallel with other pages
**Can Parallelize**: YES - Dashboard and Validators can be done together by 2 devs
**Estimated Effort**: 2 days

### Day 11: Dashboard Page
**File**: `frontend/src/pages/DashboardPage.tsx`
- [ ] Display configured chains from chains.yaml
- [ ] Show count of validators per chain
- [ ] Show count of partners
- [ ] Show count of active agreements
- [ ] Display recent commission calculations
- [ ] Use MUI Card components

**File**: `frontend/src/hooks/useDashboardData.ts`
- [ ] Fetch validators count
- [ ] Fetch partners count
- [ ] Fetch agreements count
- [ ] Use React Query for caching

**Dependencies**:
- Requires: Auth setup (Day 10), Validators API (Day 7)
- Blocks: Nothing

**Acceptance Criteria**:
- Dashboard loads and displays stats
- Data refreshes automatically
- Loading states shown
- Error states handled

---

### Day 12: Validators Page
**File**: `frontend/src/pages/ValidatorsPage.tsx`
- [ ] List validators in MUI DataGrid
- [ ] Filter by chain
- [ ] Add validator form (dialog)
- [ ] Edit validator form (dialog)
- [ ] Delete validator confirmation
- [ ] Display vote account, chain, description

**File**: `frontend/src/services/validators.ts`
- [ ] fetchValidators(chainId?, page, size)
- [ ] createValidator(data)
- [ ] updateValidator(id, data)
- [ ] deleteValidator(id)

**File**: `frontend/src/components/ValidatorForm.tsx`
- [ ] Form with chain select, vote account, description
- [ ] Validation (required fields, vote account format)
- [ ] Submit handler

**Dependencies**:
- Requires: Auth setup (Day 10), Validators API (Day 7)
- Blocks: Nothing

**Acceptance Criteria**:
- Can view all validators
- Can add new validator
- Can edit existing validator
- Can delete validator
- Form validation works

---

## Phase 7: Admin Pages - Partners & Agreements (Days 13-14)
**Critical Path**: NO - Can work in parallel
**Can Parallelize**: YES - Partners and Agreements pages independent
**Estimated Effort**: 2 days

### Day 13: Partners Page
**File**: `frontend/src/pages/PartnersPage.tsx`
- [ ] List partners in MUI DataGrid
- [ ] Add partner form (dialog)
- [ ] Edit partner form (dialog)
- [ ] Delete partner confirmation
- [ ] Display partner name, email, is_active

**File**: `frontend/src/services/partners.ts`
- [ ] fetchPartners(page, size)
- [ ] createPartner(data)
- [ ] updatePartner(id, data)
- [ ] deletePartner(id)

**File**: `frontend/src/components/PartnerForm.tsx`
- [ ] Form with name, email, contact_name, is_active
- [ ] Validation (email format, required fields)

**Dependencies**:
- Requires: Auth setup (Day 10), Partners API (Day 7)
- Blocks: Nothing

**Acceptance Criteria**:
- Can view all partners
- Can add new partner
- Can edit existing partner
- Can deactivate partner
- Email validation works

---

### Day 14: Agreements Page
**File**: `frontend/src/pages/AgreementsPage.tsx`
- [ ] List agreements in MUI DataGrid
- [ ] Filter by partner
- [ ] Add agreement form (dialog)
- [ ] Edit agreement form (dialog)
- [ ] Deactivate agreement button
- [ ] Display partner name, commission method, rate, start/end dates

**File**: `frontend/src/services/agreements.ts`
- [ ] fetchAgreements(partnerId?, page, size)
- [ ] createAgreement(data)
- [ ] updateAgreement(id, data)
- [ ] deactivateAgreement(id)

**File**: `frontend/src/components/AgreementForm.tsx`
- [ ] Partner select dropdown
- [ ] Commission method select (CLIENT_REVENUE, VALIDATOR_REVENUE, etc.)
- [ ] Commission rate input (0-100%)
- [ ] Start/end date pickers
- [ ] Validator selection (multi-select)
- [ ] Wallet address input (multi-entry)

**Dependencies**:
- Requires: Auth setup (Day 10), Agreements API (Day 7), Partners data
- Blocks: Nothing

**Acceptance Criteria**:
- Can view all agreements
- Can create agreement with validators and wallets
- Can edit agreement details
- Can deactivate agreement
- Date validation works (end > start)
- Commission rate validation (0-100)

---

## Phase 8: Admin Pages - Commissions Viewer (Day 15)
**Critical Path**: NO - Independent page
**Can Parallelize**: NO - Depends on agreements and partners
**Estimated Effort**: 1 day

### Day 15: Commissions Page
**File**: `frontend/src/pages/CommissionsPage.tsx`
- [ ] Partner select dropdown
- [ ] Period/Epoch select dropdown
- [ ] Calculate button
- [ ] Results table showing validator-level commissions
- [ ] Display validator vote account, fees, MEV, rewards, commission amount
- [ ] Summary card with total commission
- [ ] Export to CSV button (optional)

**File**: `frontend/src/services/commissions.ts`
- [ ] calculateCommissions(partnerId, periodId)
- [ ] fetchCommissionSummary(partnerId, startDate, endDate)

**File**: `frontend/src/components/CommissionResults.tsx`
- [ ] MUI DataGrid for commission lines
- [ ] Summary statistics card
- [ ] Formatted currency display (lamports → SOL)

**Dependencies**:
- Requires: Auth setup (Day 10), Commissions API (Day 7), Partners and Agreements data
- Blocks: Nothing

**Acceptance Criteria**:
- Can select partner and period
- Calculate shows commission breakdown by validator
- Total commission displayed correctly
- Handles case when no data exists for period
- Currency formatting correct

---

## Phase 9: Testing & Polish (Days 16-17)
**Critical Path**: YES - Final validation before demo
**Can Parallelize**: Some tasks can be parallel
**Estimated Effort**: 2 days

### Day 16: Integration Testing
**File**: `tests/integration/test_mvp_flow.py`
- [ ] Test complete flow: login → create validator → create partner → create agreement → calculate commission
- [ ] Test data persistence across requests
- [ ] Test error handling
- [ ] Test authorization (non-admin cannot access)

**Frontend Testing**:
- [ ] Manual testing of all pages
- [ ] Test form validation errors
- [ ] Test loading and error states
- [ ] Test responsive design (desktop only for MVP)
- [ ] Cross-browser testing (Chrome, Firefox)

**Dependencies**:
- Requires: All features complete (Days 1-15)
- Blocks: Demo readiness

**Acceptance Criteria**:
- All integration tests pass
- No console errors in browser
- All forms submit successfully
- Error messages user-friendly
- Loading states consistent

---

### Day 17: Polish & Documentation
**Tasks**:
- [ ] Fix any bugs found during testing
- [ ] Improve error messages
- [ ] Add loading skeletons where needed
- [ ] Update README with setup instructions
- [ ] Document seeded credentials
- [ ] Record demo walkthrough video (optional)
- [ ] Prepare for demo

**File**: `README.md`
- [ ] Add MVP setup instructions
- [ ] Document seeded data
- [ ] List API endpoints
- [ ] Add troubleshooting section

**File**: `docs/mvp-demo-script.md`
- [ ] Step-by-step demo walkthrough
- [ ] Expected results at each step
- [ ] Screenshots (optional)

**Dependencies**:
- Requires: All features complete
- Blocks: Nothing - ready to demo

**Acceptance Criteria**:
- No critical bugs
- Demo script validated
- Setup instructions work for new developer
- All endpoints documented

---

## Phase 10: OPTIONAL - Real Data Integration (Stretch Goal)
**Critical Path**: NO - Optional stretch goal
**Can Parallelize**: YES - If time permits after Day 17
**Estimated Effort**: 2-3 days (if pursued)

### Optional Task: Real Data Ingestion
**Files**:
- `scripts/ingest_solana_data.py`
- `src/core/services/ingestion.py`

**Tasks**:
- [ ] Fetch real epoch data from Solana Beach API
- [ ] Fetch real MEV data from Jito API
- [ ] Store in staging tables
- [ ] Run normalization to canonical layer
- [ ] Run PnL calculation service
- [ ] Update commissions based on real data

**Dependencies**:
- Requires: MVP complete (Day 17)
- Blocks: Nothing - pure enhancement

**Acceptance Criteria**:
- Real data appears in dashboard
- Commission calculations use real numbers
- Data refreshes on demand
- Handles API errors gracefully

---

## Daily Checklist Template

```markdown
## Day X: [Phase Name]

### Morning (4 hours)
- [ ] Review previous day's work
- [ ] Pull latest changes (if team)
- [ ] Task 1: [specific task]
- [ ] Task 2: [specific task]

### Afternoon (4 hours)
- [ ] Task 3: [specific task]
- [ ] Task 4: [specific task]
- [ ] Write tests for new code
- [ ] Run linting and type checks
- [ ] Commit and push changes
- [ ] Update progress in GitHub issue

### Evening (optional)
- [ ] Code review (if team)
- [ ] Plan tomorrow's tasks
```

---

## Risk Mitigation Schedule

### Week 1 (Days 1-7): Backend Priority
**Risk**: Backend delays block everything
**Mitigation**:
- Complete auth and API by Day 7 **at all costs**
- If behind schedule, cut optional features (soft delete, advanced filtering)
- Daily check-ins on progress

### Week 2 (Days 8-14): Frontend Parallel Work
**Risk**: UI complexity underestimated
**Mitigation**:
- Use MUI components heavily (don't build from scratch)
- Simplify forms if needed (fewer validations)
- Defer styling polish to Day 17

### Week 3 (Days 15-17): Testing Buffer
**Risk**: Bugs found late
**Mitigation**:
- Start integration testing early (Day 15)
- Fix blockers immediately
- Defer nice-to-haves to post-MVP

---

## Success Metrics by Day

**Day 3**: ✓ Can login and get JWT token
**Day 7**: ✓ All CRUD endpoints return 200/201
**Day 8**: ✓ Can view seeded data via Postman
**Day 10**: ✓ Can login via frontend UI
**Day 12**: ✓ Can CRUD validators in UI
**Day 14**: ✓ Can CRUD partners and agreements in UI
**Day 15**: ✓ Can calculate and view commissions
**Day 17**: ✓ Demo-ready with no critical bugs

---

## Communication Cadence (if team)

**Daily Standup** (15 min):
- What did I complete yesterday?
- What will I complete today?
- Any blockers?

**Mid-Sprint Check** (Day 9):
- Review progress against timeline
- Adjust scope if needed
- Identify risks

**Pre-Demo Review** (Day 16):
- Dry run of demo
- Identify any remaining issues
- Assign final polish tasks

---

## Definition of Done

**For Backend Endpoints**:
- [ ] Endpoint implemented with all parameters
- [ ] Request/response schemas defined
- [ ] Validation errors handled
- [ ] Authorization checked
- [ ] Unit tests written and passing
- [ ] Integration test covering happy path
- [ ] Documented in OpenAPI spec

**For Frontend Pages**:
- [ ] Page renders without errors
- [ ] All CRUD operations work
- [ ] Form validation implemented
- [ ] Loading states shown
- [ ] Error states handled gracefully
- [ ] Responsive (desktop only)
- [ ] No console errors

**For Features**:
- [ ] Acceptance criteria met
- [ ] Code reviewed (if team)
- [ ] Tests passing
- [ ] Linting passing
- [ ] Type checking passing
- [ ] Committed to git
- [ ] Demo-able

---

## Recovery Plan (if behind schedule)

**If behind by 2 days at Day 7**:
- Cut: Soft delete, advanced filtering, audit logging
- Focus: Core CRUD only

**If behind by 2 days at Day 14**:
- Cut: Commissions page (can show raw data in dashboard)
- Focus: Validators, Partners, Agreements pages only

**If behind by 3 days at Day 16**:
- Cut: Polish, advanced UI, real data integration
- Focus: Working demo with basic UI

**Nuclear Option** (if >5 days behind):
- Pivot to API-only demo using Postman
- Show data seeding script execution
- Demonstrate commission calculation via curl
- Defer frontend to post-MVP

---

## Handoff Checklist (for new session)

Before starting implementation:
- [ ] Read docs/mvp-plan.md thoroughly
- [ ] Read docs/mvp-implementation-order.md (this file)
- [ ] Review docs/ai-context/project-structure.md
- [ ] Check current git branch status
- [ ] Verify database is seeded (or run seed script)
- [ ] Confirm backend API is running (port 8000)
- [ ] Confirm frontend is running (port 3000)
- [ ] Review open GitHub issues
- [ ] Identify current day in schedule
- [ ] Read previous day's commit messages

---

## Appendix: Quick Reference

### Key Commands
```bash
# Backend
poetry run python -m src.main  # Run API server
poetry run pytest  # Run tests
poetry run mypy src/  # Type checking
poetry run ruff check src/  # Linting
poetry run alembic upgrade head  # Apply migrations
poetry run python scripts/seed_mvp_data.py  # Seed data

# Frontend
cd frontend
npm run dev  # Run dev server
npm run build  # Production build
npm run lint  # ESLint
npm run type-check  # TypeScript checking
```

### Key URLs
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

### Seeded Credentials
- Username: admin
- Password: admin123
- Role: ADMIN

### GitHub Issue Labels
- `mvp` - Part of MVP scope
- `critical` - Blocks other work
- `backend` - Backend task
- `frontend` - Frontend task
- `stretch-goal` - Optional enhancement
