# Aurora MVP: Admin Dashboard for Validator P&L & Partner Commissions

**Version**: 1.0
**Date**: 2025-10-28
**Status**: Planning Complete - Ready for Implementation
**Timeline**: 2-3 weeks (17 developer-days)

---

## Executive Summary

### Goal
Build a functional admin dashboard demonstrating the complete Aurora validator P&L and partner commission calculation system. The MVP will showcase validator configuration, partner management, agreement creation, and automated commission calculations using realistic seeded data.

### Key Decisions
- **Timeline**: Fast track (2-3 weeks) for rapid stakeholder demonstration
- **Data Source**: Seeded test data for reliability (real ingestion as stretch goal)
- **Scope**: Admin-only authentication (partner portal deferred)
- **Features**: Validator configuration, partner CRUD, agreement management, commission viewing

### Success Metrics
- Admin can authenticate and access full dashboard
- Can configure validators (add/view via vote pubkeys)
- Can manage partners and create commission agreements
- Can view calculated commission breakdowns by fees/MEV/rewards
- Complete demo walkthrough in under 5 minutes
- All calculations mathematically accurate

---

## Current Implementation Status

### ✅ Foundation Complete (85% of data layer)

**Database & ORM Models**:
- ✅ Chain registry models (`src/core/models/chains.py`)
- ✅ Staging layer models (`src/core/models/staging.py`)
- ✅ Canonical layer models (`src/core/models/canonical.py`)
- ✅ Computation layer models (`src/core/models/computation.py`)
  - ValidatorPnL, Partners, Agreements, AgreementRules
  - PartnerCommissionLines, PartnerCommissionStatements

**Infrastructure**:
- ✅ PostgreSQL 15 + Redis 7 (Docker Compose)
- ✅ Alembic migrations configured and tested
- ✅ Async SQLAlchemy session management
- ✅ JWT security utilities
- ✅ Structured logging with correlation IDs

**Adapters**:
- ✅ Base adapter interface with retry logic and circuit breaker
- ✅ Solana Beach adapter (fees, rewards, metadata)
- ✅ Jito MEV adapter (MEV tips)

**Testing**:
- ✅ 214 tests passing with 88% coverage
- ✅ Comprehensive test fixtures

### ❌ Missing for MVP (What We're Building)

**Critical Missing**:
- ❌ User authentication models
- ❌ Entire API layer (FastAPI endpoints)
- ❌ Service layer (business logic)
- ❌ Repository layer (data access abstraction)
- ❌ Pydantic schemas (request/response DTOs)
- ❌ Entire frontend (React UI)

---

## Implementation Phases

### Phase 1: Backend Foundation (Days 1-3)

#### Objectives
- User authentication system
- FastAPI application setup
- JWT token flow

#### Tasks

**1.1 User Model & Migration** (Day 1, 3 hours)
```python
# src/core/models/users.py
class User(BaseModel):
    user_id: UUID (PK)
    username: str (unique)
    email: str (unique)
    password_hash: str
    role: UserRole (ADMIN, PARTNER)
    partner_id: UUID (FK to partners, nullable)
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

**Acceptance Criteria**:
- User table created via Alembic migration
- UserRole enum: ADMIN, PARTNER
- Unique constraints on username and email
- Foreign key to partners table (nullable)
- Migration tested (upgrade/downgrade)

**1.2 FastAPI Application Setup** (Day 1, 2 hours)
```python
# src/main.py
- FastAPI app initialization
- CORS middleware configuration
- Health check endpoint: GET /health
- API version routing: /api/v1/
```

**Acceptance Criteria**:
- Server runs with `uvicorn src.main:app`
- Health check returns 200 OK
- CORS allows frontend origin
- OpenAPI docs available at /docs

**1.3 Authentication Dependencies** (Day 2, 3 hours)
```python
# src/api/deps.py
- get_db() → AsyncSession
- get_current_user() → User (from JWT)
- get_current_admin_user() → User (role check)
```

**Acceptance Criteria**:
- Database session injection works
- JWT token validation implemented
- Role-based access control helper
- Invalid token returns 401

**1.4 Auth Endpoints** (Day 2-3, 5 hours)
```python
# src/api/v1/auth.py
POST /api/v1/auth/login
  Request: {"username": str, "password": str}
  Response: {"access_token": str, "token_type": "bearer", "user": UserResponse}

POST /api/v1/auth/refresh
  Request: {"refresh_token": str}
  Response: {"access_token": str}

GET /api/v1/auth/me
  Response: UserResponse
```

**Acceptance Criteria**:
- Login with valid credentials returns JWT
- Invalid credentials return 401
- Token refresh works
- GET /me returns current user info
- Password verified using bcrypt

**1.5 Seed Admin User** (Day 3, 1 hour)
```python
# scripts/seed_admin.py
- Create default admin user
- Username: admin
- Password: (set via environment variable)
- Role: ADMIN
```

**Acceptance Criteria**:
- Admin user created in database
- Can log in via API
- Password hashed with bcrypt

**Phase 1 Checkpoint**: Can authenticate via API and get JWT token

---

### Phase 2: Core API Layer - Schemas & Repositories (Days 4-5)

#### Objectives
- Define all Pydantic schemas (DTOs)
- Implement repository pattern
- Data access abstraction

#### Tasks

**2.1 Pydantic Schemas** (Day 4, 4 hours)
```python
# src/core/schemas/auth.py
- LoginRequest, TokenResponse, UserResponse

# src/core/schemas/chains.py
- ChainResponse, PeriodResponse

# src/core/schemas/validators.py
- ValidatorCreateRequest, ValidatorResponse
- ValidatorPnLResponse, ValidatorPnLDetail

# src/core/schemas/partners.py
- PartnerCreateRequest, PartnerUpdateRequest
- PartnerResponse, PartnerDetail

# src/core/schemas/agreements.py
- AgreementCreateRequest, AgreementUpdateRequest
- AgreementResponse, AgreementRuleCreate

# src/core/schemas/commissions.py
- CommissionLineResponse, CommissionBreakdown
- StatementResponse, StatementDetail
```

**Acceptance Criteria**:
- All schemas have proper validation
- Request/Response separation
- Nested schemas for complex objects
- Examples in docstrings

**2.2 Base Repository** (Day 4, 3 hours)
```python
# src/core/repositories/base.py
class BaseRepository[T]:
    async def get_by_id(id: UUID) -> T | None
    async def get_all(skip: int, limit: int) -> list[T]
    async def create(data: dict) -> T
    async def update(id: UUID, data: dict) -> T
    async def delete(id: UUID) -> bool
    async def count() -> int
```

**Acceptance Criteria**:
- Generic base repository with common CRUD
- Type-safe with Generic[T]
- Async SQLAlchemy queries
- Proper error handling

**2.3 Concrete Repositories** (Day 5, 6 hours)
```python
# src/core/repositories/chains.py
class ChainRepository(BaseRepository[Chain]):
    async def get_by_chain_id(chain_id: str) -> Chain | None
    async def get_active_chains() -> list[Chain]

# src/core/repositories/periods.py
class PeriodRepository(BaseRepository[CanonicalPeriod]):
    async def get_by_chain(chain_id: str) -> list[CanonicalPeriod]
    async def get_finalized(chain_id: str) -> list[CanonicalPeriod]

# src/core/repositories/validators.py
class ValidatorRepository(BaseRepository[CanonicalValidatorIdentity]):
    async def get_by_chain(chain_id: str) -> list[ValidatorIdentity]
    async def get_pnl(validator_key: str, period_id: str) -> ValidatorPnL

# src/core/repositories/partners.py
class PartnerRepository(BaseRepository[Partners]):
    async def get_by_name(name: str) -> Partners | None
    async def get_active() -> list[Partners]

# src/core/repositories/agreements.py
class AgreementRepository(BaseRepository[Agreements]):
    async def get_active_by_partner(partner_id: UUID) -> list[Agreements]
    async def get_rules(agreement_id: UUID) -> list[AgreementRules]

# src/core/repositories/commissions.py
class CommissionRepository:
    async def get_lines_by_partner(partner_id: UUID) -> list[CommissionLines]
    async def get_statement(partner_id: UUID, period: str) -> Statement
```

**Acceptance Criteria**:
- All repositories extend BaseRepository
- Custom query methods for business logic
- Proper filtering and ordering
- Unit tests for each repository

**Phase 2 Checkpoint**: Can query database via repositories

---

### Phase 3: Core API Layer - Services & Endpoints (Days 6-7)

#### Objectives
- Business logic layer
- REST API endpoints

#### Tasks

**3.1 Service Layer** (Day 6, 4 hours)
```python
# src/core/services/partner_service.py
class PartnerService:
    async def create_partner(data: PartnerCreateRequest) -> Partners
    async def update_partner(id: UUID, data: PartnerUpdateRequest) -> Partners
    async def delete_partner(id: UUID) -> bool
    async def get_partner_detail(id: UUID) -> PartnerDetail

# src/core/services/agreement_service.py
class AgreementService:
    async def create_agreement(data: AgreementCreateRequest) -> Agreements
    async def add_rule(agreement_id: UUID, rule: RuleCreate) -> AgreementRules
    async def activate_agreement(id: UUID) -> Agreements

# src/core/services/commission_service.py
class CommissionService:
    async def calculate_commissions(
        partner_id: UUID,
        period_id: str
    ) -> list[CommissionLines]

    async def get_commission_breakdown(
        line_id: UUID
    ) -> CommissionBreakdown
```

**Acceptance Criteria**:
- Services orchestrate repositories
- Business logic in service layer (not repos)
- Input validation via Pydantic
- Returns DTOs, not ORM models

**3.2 Chain & Validator Endpoints** (Day 6, 3 hours)
```python
# src/api/v1/chains.py
GET /api/v1/chains
  → List all configured chains

GET /api/v1/chains/{chain_id}/periods
  → List finalized periods for chain

# src/api/v1/validators.py
GET /api/v1/validators
  Query: ?chain_id=solana-mainnet
  → List configured validators

POST /api/v1/validators
  Body: {"chain_id": str, "validator_key": str, "name": str}
  → Add new validator

GET /api/v1/validators/{validator_key}/pnl
  Query: ?period_id=600
  → Get validator P&L for period
```

**Acceptance Criteria**:
- All endpoints require authentication
- Proper error responses (400, 404, 500)
- Pagination on list endpoints
- OpenAPI docs updated

**3.3 Partner & Agreement Endpoints** (Day 7, 6 hours)
```python
# src/api/v1/partners.py
GET    /api/v1/partners           → List all partners
POST   /api/v1/partners           → Create partner
GET    /api/v1/partners/{id}      → Get partner detail
PUT    /api/v1/partners/{id}      → Update partner
DELETE /api/v1/partners/{id}      → Delete partner

# src/api/v1/agreements.py
GET    /api/v1/agreements         → List all agreements
POST   /api/v1/agreements         → Create agreement
GET    /api/v1/agreements/{id}    → Get agreement detail
PUT    /api/v1/agreements/{id}    → Update agreement
DELETE /api/v1/agreements/{id}    → Deactivate agreement

POST   /api/v1/agreements/{id}/rules  → Add commission rule
```

**Acceptance Criteria**:
- Full CRUD for both resources
- Cascade handling (delete partner → agreements?)
- Validation errors return 422
- Foreign key constraints enforced

**3.4 Commission Endpoints** (Day 7, 2 hours)
```python
# src/api/v1/commissions.py
GET /api/v1/commissions/partners/{partner_id}
  Query: ?chain_id=X&period_id=Y
  → List commission lines for partner

GET /api/v1/commissions/lines/{line_id}
  → Get detailed breakdown (fees, MEV, rewards)

GET /api/v1/commissions/statements/{partner_id}
  Query: ?month=2024-10
  → Get monthly statement summary
```

**Acceptance Criteria**:
- Filtering by chain, period, partner
- Breakdown shows component-level detail
- Calculations match database exactly

**Phase 3 Checkpoint**: Full REST API working, testable via Postman

---

### Phase 4: Data Seeding (Day 8)

#### Objectives
- Populate database with realistic test data
- Pre-compute all derived values

#### Tasks

**4.1 Seed Script** (Day 8, 6 hours)
```python
# scripts/seed_mvp_data.py

# 1. Chains (1 record)
- Solana Mainnet

# 2. Canonical Periods (3 records)
- Epochs 600, 601, 602 (with real timestamps)

# 3. Validator Identities (3 records)
- Use your REAL vote pubkeys
- Names: "Validator Alpha", "Validator Beta", "Validator Gamma"

# 4. Canonical Data (9 records each)
CanonicalValidatorFees:
  - 3 validators × 3 epochs = 9 records
  - Realistic fee amounts (e.g., 50-200 SOL per epoch)

CanonicalValidatorMEV:
  - 9 records with MEV tips
  - Amounts: 10-50 SOL per epoch

CanonicalStakeRewards:
  - 9 records (aggregated, no per-staker detail)
  - Amounts: 100-300 SOL per epoch

CanonicalValidatorMeta:
  - 9 records with commission rates, stake amounts
  - Commission: 5-10% (500-1000 bps)
  - Total stake: 100K-500K SOL

# 5. ValidatorPnL (9 records)
- Computed: total_fees + total_mev + total_rewards
- Stored in lamports

# 6. Partners (2 records)
- "Staking Company A" (active)
- "Validator Services LLC" (active)

# 7. Agreements (2 records)
Agreement 1:
  - Partner: Staking Company A
  - Attribution: CLIENT_REVENUE
  - Commission: 10% of total revenue
  - Active from epoch 600

Agreement 2:
  - Partner: Validator Services LLC
  - Attribution: CLIENT_REVENUE
  - Commission: 5% of MEV only
  - Active from epoch 601

# 8. Commission Lines (auto-calculate)
- For each partner × period combination
- Based on ValidatorPnL and Agreement rules
- Component breakdown: fees, MEV, rewards
```

**Acceptance Criteria**:
- Script is idempotent (can run multiple times)
- All foreign keys valid
- Amounts are realistic for Solana
- Commission calculations correct
- Can run: `poetry run python scripts/seed_mvp_data.py`

**Phase 4 Checkpoint**: Database fully populated, ready for UI

---

### Phase 5: Frontend Setup & Authentication (Days 9-10)

#### Objectives
- React application initialization
- Authentication flow
- Protected routing

#### Tasks

**5.1 React Project Setup** (Day 9, 3 hours)
```bash
# Create React app with Vite
cd frontend/
npm create vite@latest . -- --template react-ts
npm install

# Dependencies
npm install @mui/material @emotion/react @emotion/styled
npm install react-router-dom
npm install @tanstack/react-query
npm install axios
npm install react-hook-form @hookform/resolvers zod
```

**File Structure**:
```
frontend/
├── src/
│   ├── components/
│   │   ├── Layout.tsx
│   │   ├── ProtectedRoute.tsx
│   │   └── Nav.tsx
│   ├── pages/
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Validators.tsx
│   │   ├── Partners.tsx
│   │   ├── Agreements.tsx
│   │   └── Commissions.tsx
│   ├── services/
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   └── types.ts
│   ├── hooks/
│   │   └── useAuth.ts
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── vite.config.ts
```

**Acceptance Criteria**:
- Dev server runs: `npm run dev`
- TypeScript configured
- Material-UI theme applied
- Build works: `npm run build`

**5.2 API Client Setup** (Day 9, 2 hours)
```typescript
// src/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: handle 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

**Acceptance Criteria**:
- Axios instance configured
- Token injection works
- 401 redirects to login
- Environment variable support

**5.3 Authentication Context** (Day 9, 2 hours)
```typescript
// src/hooks/useAuth.ts
export const useAuth = () => {
  const login = async (username: string, password: string) => {
    const response = await api.post('/auth/login', {username, password});
    localStorage.setItem('access_token', response.data.access_token);
    return response.data.user;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
  };

  const getCurrentUser = async () => {
    return api.get('/auth/me');
  };

  return {login, logout, getCurrentUser};
};
```

**Acceptance Criteria**:
- Login stores token
- Logout clears token
- Token persists on reload
- getCurrentUser fetches user info

**5.4 Login Page** (Day 10, 3 hours)
```typescript
// src/pages/Login.tsx
- Material-UI Card with form
- Username and password fields
- Submit calls useAuth().login()
- Error handling and display
- Redirect to dashboard on success
```

**Acceptance Criteria**:
- Form validation works
- Login request sent to API
- Success redirects to /dashboard
- Error messages displayed
- Loading state shown

**5.5 Protected Routes** (Day 10, 2 hours)
```typescript
// src/components/ProtectedRoute.tsx
- Check for auth token
- Redirect to /login if not authenticated
- Wrap all admin pages

// src/App.tsx
<Routes>
  <Route path="/login" element={<Login />} />
  <Route element={<ProtectedRoute />}>
    <Route path="/" element={<Dashboard />} />
    <Route path="/validators" element={<Validators />} />
    <Route path="/partners" element={<Partners />} />
    <Route path="/agreements" element={<Agreements />} />
    <Route path="/commissions" element={<Commissions />} />
  </Route>
</Routes>
```

**Acceptance Criteria**:
- Unauthenticated users redirected
- Token checked on mount
- Navigation works between pages

**5.6 Layout & Navigation** (Day 10, 2 hours)
```typescript
// src/components/Layout.tsx
- AppBar with title "Aurora Admin"
- Drawer navigation:
  - Dashboard
  - Validators
  - Partners
  - Agreements
  - Commissions
- Logout button
- User info display
```

**Acceptance Criteria**:
- Navigation drawer works
- Active page highlighted
- Logout clears token and redirects
- Responsive layout

**Phase 5 Checkpoint**: Can log in via UI, navigate to empty pages

---

### Phase 6: Admin Pages - Dashboard & Validators (Days 11-12)

#### Objectives
- Dashboard with overview stats
- Validator list and configuration

#### Tasks

**6.1 Dashboard Page** (Day 11, 4 hours)
```typescript
// src/pages/Dashboard.tsx

Components:
1. Stats Cards (Grid layout)
   - Total Chains (1)
   - Configured Validators (3)
   - Active Partners (2)
   - Total Commissions (calculated sum)

2. Recent Activity
   - Latest commission calculations
   - Recent partner additions

3. Quick Actions
   - "Add Validator" button
   - "Create Partner" button
```

**API Calls**:
- GET /chains (count)
- GET /validators (count)
- GET /partners (count)
- GET /commissions/recent (latest 5)

**Acceptance Criteria**:
- Stats cards display correct counts
- Recent activity shows latest data
- Quick action buttons navigate correctly
- Loading states shown during fetch
- Error handling for failed requests

**6.2 Validators List Page** (Day 11, 3 hours)
```typescript
// src/pages/Validators.tsx

Components:
1. Data Table
   - Columns: Name, Vote Pubkey, Chain, Status
   - Actions: View P&L, Edit, Delete

2. "Add Validator" Button
   - Opens dialog with form
```

**API Calls**:
- GET /validators (list all)
- POST /validators (create new)
- DELETE /validators/{key} (remove)

**Acceptance Criteria**:
- Table displays all validators
- Can filter by chain
- Add dialog works
- Delete confirms before action
- Table refreshes after changes

**6.3 Add Validator Dialog** (Day 12, 2 hours)
```typescript
// src/components/AddValidatorDialog.tsx

Form Fields:
- Chain selection (dropdown)
- Validator vote pubkey (text input, 44 chars)
- Validator name (text input)

Validation:
- Vote pubkey format (base58, 44 chars)
- Name required
- Chain required
```

**Acceptance Criteria**:
- Form validation works
- Invalid pubkey shows error
- Submit creates validator
- Success closes dialog and refreshes list
- Cancel closes without action

**6.4 Validator P&L Detail** (Day 12, 3 hours)
```typescript
// src/pages/ValidatorDetail.tsx

Components:
1. Validator Header
   - Name, vote pubkey, chain

2. P&L Summary (per period)
   - Table with columns:
     - Period (epoch)
     - Total Fees
     - Total MEV
     - Total Rewards
     - Total P&L
   - Amounts in SOL (converted from lamports)

3. Chart (optional)
   - Bar chart showing fees/MEV/rewards per period
```

**API Calls**:
- GET /validators/{key}
- GET /validators/{key}/pnl?period_id=X

**Acceptance Criteria**:
- Shows P&L for all seeded periods
- Amounts formatted correctly (SOL)
- Chart displays if time permits
- Back button returns to list

**Phase 6 Checkpoint**: Dashboard and validators fully functional

---

### Phase 7: Admin Pages - Partners & Agreements (Days 13-14)

#### Objectives
- Partner CRUD operations
- Agreement creation and management

#### Tasks

**7.1 Partners List Page** (Day 13, 3 hours)
```typescript
// src/pages/Partners.tsx

Components:
1. Data Table
   - Columns: Name, Email, Status, Agreements Count
   - Actions: View, Edit, Delete

2. "Create Partner" Button
   - Opens dialog/page

3. Search/Filter
   - By name
   - By status (active/inactive)
```

**API Calls**:
- GET /partners (list)
- GET /partners/{id} (detail)
- POST /partners (create)
- PUT /partners/{id} (update)
- DELETE /partners/{id} (delete)

**Acceptance Criteria**:
- Table shows all partners
- Search filters in real-time
- CRUD operations work
- Delete confirms before action
- Table updates after changes

**7.2 Partner Create/Edit Form** (Day 13, 3 hours)
```typescript
// src/components/PartnerForm.tsx

Form Fields:
- Partner name (required)
- Email (required, email validation)
- Contact name
- Phone
- Address
- Status (active/inactive toggle)

Validation:
- Email format
- Name min length
- Required fields
```

**Acceptance Criteria**:
- Form validation works
- Create saves new partner
- Edit updates existing partner
- Cancel discards changes
- Success message shown

**7.3 Agreements List Page** (Day 14, 3 hours)
```typescript
// src/pages/Agreements.tsx

Components:
1. Data Table
   - Columns: Partner, Start Date, End Date, Status, Rules Count
   - Actions: View, Edit, Deactivate

2. "Create Agreement" Button

3. Filter
   - By partner
   - By status (active/inactive)
```

**API Calls**:
- GET /agreements (list)
- GET /agreements/{id} (detail)
- POST /agreements (create)
- PUT /agreements/{id} (update)

**Acceptance Criteria**:
- Table shows all agreements
- Filter by partner works
- Can view agreement rules
- Deactivate requires confirmation

**7.4 Agreement Create Form** (Day 14, 4 hours)
```typescript
// src/components/AgreementForm.tsx

Form Sections:
1. Agreement Info
   - Partner selection (dropdown)
   - Effective start date
   - Effective end date (optional)
   - Status

2. Commission Rules (repeatable)
   - Attribution method (dropdown: CLIENT_REVENUE)
   - Revenue component (dropdown: ALL, EXEC_FEES, MEV, REWARDS)
   - Commission rate (percentage: 0-100%)
   - Effective from period

Multiple Rules:
- "Add Rule" button to add more
- Each rule can target different revenue component
```

**Validation**:
- Partner required
- Start date required
- At least one rule required
- Rate between 0-100%

**Acceptance Criteria**:
- Multi-step or tabbed form
- Can add multiple rules
- Partner dropdown populated
- Date pickers work
- Submit creates agreement with rules
- Validation prevents invalid data

**Phase 7 Checkpoint**: Partners and agreements fully manageable

---

### Phase 8: Admin Pages - Commissions Viewer (Day 15)

#### Objectives
- Display calculated commissions
- Breakdown by component
- Filtering and drill-down

#### Tasks

**8.1 Commissions List Page** (Day 15, 4 hours)
```typescript
// src/pages/Commissions.tsx

Components:
1. Filter Panel
   - Partner dropdown
   - Chain dropdown
   - Period dropdown
   - Date range picker

2. Commission Lines Table
   - Columns:
     - Partner Name
     - Chain
     - Period
     - Total Commission
     - Status
   - Row expandable for breakdown

3. Expanded Row Detail
   - Fees Commission
   - MEV Commission
   - Rewards Commission
   - Agreement used
   - Calculation timestamp
```

**API Calls**:
- GET /commissions/partners/{id}?chain_id=X&period_id=Y
- GET /commissions/lines/{line_id} (breakdown)

**Acceptance Criteria**:
- Table shows all commission lines
- Filters work independently
- Row expansion shows breakdown
- Amounts formatted (SOL)
- Empty state if no results

**8.2 Commission Breakdown Dialog** (Day 15, 2 hours)
```typescript
// src/components/CommissionBreakdownDialog.tsx

Display:
1. Header
   - Partner name
   - Period
   - Total commission

2. Component Breakdown (cards)
   - Execution Fees:
     - Base amount: $X
     - Commission rate: Y%
     - Commission: $Z

   - MEV:
     - Base amount: $X
     - Commission rate: Y%
     - Commission: $Z

   - Rewards:
     - Base amount: $X
     - Commission rate: Y%
     - Commission: $Z

3. Agreement Info
   - Which agreement applied
   - Effective rules
```

**Acceptance Criteria**:
- Shows full calculation detail
- Math is transparent (show formula)
- Amounts match database
- Can navigate to agreement from dialog

**8.3 Monthly Statement View** (Day 15, 2 hours)
```typescript
// src/pages/Statements.tsx

Components:
1. Statement Summary
   - Month/year picker
   - Partner selection
   - Total commission for month
   - Number of periods included

2. Period-by-Period Table
   - Each period's contribution
   - Running total
```

**API Calls**:
- GET /commissions/statements/{partner_id}?month=2024-10

**Acceptance Criteria**:
- Groups lines by month
- Shows aggregate totals
- Can drill down to individual periods
- Export button (nice to have)

**Phase 8 Checkpoint**: Full commission viewing with breakdowns

---

### Phase 9: Testing, Polish & Demo Prep (Days 16-17)

#### Objectives
- Integration testing
- Bug fixes
- UX improvements
- Demo preparation

#### Tasks

**9.1 Integration Testing** (Day 16, 4 hours)
- Test complete workflows:
  1. Login → Dashboard → Add Validator
  2. Create Partner → Create Agreement
  3. View Commissions → Drill down

- Test error scenarios:
  - Invalid login
  - Network errors
  - Invalid form submissions
  - Delete with dependencies

- Browser testing:
  - Chrome
  - Firefox
  - Safari (if available)

**Acceptance Criteria**:
- All happy paths work
- Error states handled gracefully
- No console errors
- Loading states appropriate

**9.2 Bug Fixes** (Day 16, 3 hours)
- Fix issues found in testing
- Address edge cases
- Improve error messages
- Handle loading states

**9.3 UX Polish** (Day 17, 3 hours)
- Consistent spacing and alignment
- Loading spinners during API calls
- Success/error notifications (toast messages)
- Confirm dialogs for destructive actions
- Empty states for tables
- Form validation feedback
- Disable submit during loading

**9.4 Demo Script Creation** (Day 17, 2 hours)
```markdown
# Aurora MVP Demo Script (5 minutes)

1. Login (30 seconds)
   - Show admin login screen
   - Enter credentials
   - Navigate to dashboard

2. Dashboard Overview (30 seconds)
   - Point out stats: 1 chain, 3 validators, 2 partners
   - Quick actions visible

3. Validators (1 minute)
   - Show configured validators with REAL vote pubkeys
   - Click "View P&L" on one validator
   - Show fees/MEV/rewards breakdown across 3 epochs

4. Partners (1 minute)
   - Show existing partners
   - Create new partner: "Demo Staking Co"
   - Show partner created in table

5. Agreements (1.5 minutes)
   - Show existing agreements
   - Create agreement for new partner:
     - 8% of total revenue
     - Effective from epoch 600
   - Show agreement with rules

6. Commissions (1.5 minutes)
   - Filter by newly created partner
   - Show calculated commission (should be ~$X)
   - Expand row to show breakdown
   - Click detail to show full calculation

7. Wrap-up (30 seconds)
   - Highlight: Full validator P&L tracking
   - Highlight: Automated commission calculation
   - Highlight: Ready for real data integration
```

**9.5 Docker Compose Update** (Day 17, 1 hour)
```yaml
# docker-compose.yml
services:
  db:
    # existing PostgreSQL

  redis:
    # existing Redis

  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET=${JWT_SECRET}

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - api
```

**Acceptance Criteria**:
- `docker-compose up` starts everything
- API accessible at localhost:8000
- Frontend accessible at localhost:3000
- Database migrations run automatically
- Seed data loaded

**Phase 9 Checkpoint**: MVP complete and demo-ready!

---

## Phase 10: OPTIONAL - Real Data Integration (Stretch Goal)

### Objectives
If time permits after completing Phase 9, add ability to fetch one epoch of real data from live Solana validators.

### Tasks

**10.1 Ingestion Service** (2-3 hours)
```python
# src/core/services/ingestion_service.py
class IngestionService:
    async def ingest_validator_data(
        chain_id: str,
        period_id: str,
        validator_key: str
    ) -> IngestionRun:
        """Fetch data from adapters and store in staging."""

        # 1. Create IngestionRun record
        # 2. Fetch fees from Solana Beach adapter
        # 3. Fetch MEV from Jito adapter
        # 4. Fetch rewards from RPC
        # 5. Store in StagingPayload
        # 6. Transform to canonical
        # 7. Update IngestionRun status
```

**10.2 Ingestion Endpoint** (1 hour)
```python
# src/api/v1/ingestion.py
POST /api/v1/ingestion/run
  Body: {
    "chain_id": "solana-mainnet",
    "period_id": "650",
    "validator_keys": ["vote_pubkey1"]
  }
  → Trigger ingestion for one epoch
```

**10.3 UI Trigger Button** (2 hours)
```typescript
// On Validator detail page
<Button onClick={handleIngestData}>
  Fetch Latest Epoch
</Button>

// Shows loading spinner during ingestion
// Shows success/error notification
// Refreshes P&L table on success
```

**10.4 Live Data Badge** (1 hour)
```typescript
// In validators table, add badge
if (validator.hasLiveData) {
  <Chip label="Live Data" color="success" size="small" />
}
```

**Stretch Goal Acceptance Criteria**:
- Can trigger ingestion via UI
- One epoch of real data fetched
- Data stored in canonical tables
- Commission recalculates automatically
- Live data visually distinguished from seed data
- Doesn't break existing seeded data

---

## Technology Stack

### Backend
- **Framework**: FastAPI 0.115.0+ with Uvicorn
- **Database**: PostgreSQL 15 (asyncpg driver)
- **ORM**: SQLAlchemy 2.0 (async mode)
- **Migrations**: Alembic 1.13+
- **Auth**: python-jose[cryptography] (JWT)
- **Validation**: Pydantic 2.x
- **Password**: passlib[bcrypt]
- **HTTP Client**: httpx (async)

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite 5.x
- **UI Library**: Material-UI (MUI) 5.x
- **Routing**: React Router v6
- **State Management**: TanStack Query (React Query)
- **HTTP Client**: Axios
- **Form Handling**: React Hook Form + Zod

### Infrastructure
- **Database**: PostgreSQL 15-alpine
- **Cache**: Redis 7-alpine
- **Container**: Docker + Docker Compose
- **Dependency Management**: Poetry (backend), npm (frontend)

---

## Out of Scope (Post-MVP)

### Deferred to Post-MVP
1. **Partner Portal**
   - Partner user login
   - Partner-scoped data access
   - Self-service commission viewing

2. **Real Data Ingestion** (unless stretch goal completed)
   - Scheduled ingestion jobs
   - Real-time validator data fetching
   - Data normalization pipeline

3. **Advanced Commission Features**
   - STAKE_WEIGHT attribution method
   - Tiered commission rates
   - Commission caps and floors
   - Manual override workflows
   - Commission approval process

4. **Payment Tracking**
   - Invoice generation
   - Payment status tracking
   - Payment reconciliation

5. **Multi-Chain Support Beyond Solana**
   - Ethereum validator tracking
   - Cross-chain aggregation

6. **Advanced RBAC**
   - Fine-grained permissions
   - Row-level security enforcement
   - Audit logging

7. **Notifications**
   - Email alerts
   - Commission statement emails

8. **Analytics & Reporting**
   - Commission trends
   - Validator performance analytics
   - Partner comparison reports

9. **Export/Import**
   - CSV exports
   - PDF commission statements
   - Data import utilities

---

## Success Criteria

### Functional Requirements
- ✅ Admin can authenticate with username/password
- ✅ Can view list of configured chains (Solana)
- ✅ Can view finalized periods (3 epochs)
- ✅ Can add validators by vote pubkey
- ✅ Can view validator P&L breakdowns (fees, MEV, rewards)
- ✅ Can create and manage partners (CRUD)
- ✅ Can create commission agreements with rules
- ✅ Can view calculated commissions for partners
- ✅ Can see commission breakdowns by component
- ✅ Can filter commissions by partner/period

### Non-Functional Requirements
- ✅ All API calls < 500ms (with local DB)
- ✅ UI responsive on desktop and tablet
- ✅ No console errors in browser
- ✅ All calculations match database values
- ✅ Error messages are user-friendly
- ✅ Loading states during async operations

### Demo Requirements
- ✅ Complete demo in < 5 minutes
- ✅ Shows end-to-end workflow
- ✅ Demonstrates key value propositions:
  - Automated P&L tracking
  - Partner commission automation
  - Transparent calculation breakdowns
- ✅ Uses real validator vote pubkeys (user-provided)
- ✅ All data is mathematically accurate

---

## Demo Walkthrough Script

**Total Time**: 4-5 minutes

### Preparation (Before Demo)
1. Start all services: `docker-compose up`
2. Verify database seeded
3. Open browser to `localhost:3000`
4. Have admin credentials ready

### Demo Steps

**1. Login (30 seconds)**
```
Action: Navigate to login page
Action: Enter admin credentials
Result: Redirected to dashboard
```

**2. Dashboard Overview (30 seconds)**
```
Show: Overview stats
  - 1 chain configured (Solana Mainnet)
  - 3 validators configured
  - 2 active partners
  - Total commissions: $XX,XXX

Show: Recent activity section
```

**3. Validators (1 minute)**
```
Action: Click "Validators" in nav
Show: Table with 3 validators
  - Names, vote pubkeys (REAL ones), chain

Action: Click "View P&L" on first validator
Show: P&L table with 3 epochs
  - Epoch 600: Fees $X, MEV $Y, Rewards $Z, Total $W
  - Epoch 601: ...
  - Epoch 602: ...

Highlight: "This demonstrates accurate tracking of all validator revenue"
```

**4. Partners (1 minute)**
```
Action: Click "Partners" in nav
Show: Existing partners (Staking Company A, Validator Services LLC)

Action: Click "Add Partner"
Fill: Name: "Demo Staking Co"
Fill: Email: "demo@staking.co"
Action: Submit

Show: New partner appears in table
Highlight: "Simple partner onboarding"
```

**5. Agreements (1.5 minutes)**
```
Action: Click "Agreements" in nav
Show: Existing agreements for 2 partners

Action: Click "Create Agreement"
Select: Partner: Demo Staking Co
Fill: Start date: Today
Fill: Commission rule:
  - Attribution: Client Revenue
  - Component: All Revenue
  - Rate: 8%
  - From period: Epoch 600

Action: Submit

Show: New agreement in table
Highlight: "Flexible commission structure"
```

**6. Commissions (1.5 minutes)**
```
Action: Click "Commissions" in nav
Show: Commission lines for all partners

Action: Filter by "Demo Staking Co"
Show: Commission lines for epochs 600-602
  - Total: ~$X,XXX across 3 epochs

Action: Expand first row
Show: Breakdown:
  - Fees commission: $A (8% of $X fees)
  - MEV commission: $B (8% of $Y MEV)
  - Rewards commission: $C (8% of $Z rewards)

Action: Click "View Detail"
Show: Full calculation with formulas

Highlight: "Completely transparent commission calculations"
Highlight: "Automated monthly statements ready"
```

**7. Wrap-Up (30 seconds)**
```
Summary:
  ✓ Full validator P&L tracking with real vote pubkeys
  ✓ Automated partner commission calculation
  ✓ Transparent, auditable breakdowns
  ✓ Ready for production with real-time data ingestion
  ✓ Foundation for multi-chain expansion

Next Steps:
  - Connect to live validator data streams
  - Add partner portal for self-service access
  - Implement payment tracking and invoicing
  - Expand to Ethereum validators
```

---

## Risk Assessment

### Technical Risks

**Risk 1: Commission Calculation Complexity**
- **Severity**: Medium
- **Probability**: Low
- **Mitigation**: MVP implements only CLIENT_REVENUE method with fixed percentages. Defers complex attribution, tiers, and overrides.

**Risk 2: Frontend Development Overrun**
- **Severity**: Medium
- **Probability**: Medium
- **Mitigation**: Use Material-UI for rapid UI development. Focus on functional over beautiful. Can simplify pages if needed.

**Risk 3: API Development Delays**
- **Severity**: High
- **Probability**: Low
- **Mitigation**: Well-defined schema and endpoints. Repository pattern is straightforward. Service layer is thin for MVP.

**Risk 4: Data Seeding Issues**
- **Severity**: Low
- **Probability**: Low
- **Mitigation**: Script is idempotent. Can manually verify data. Has clear structure.

### Schedule Risks

**Risk 1: Underestimated Frontend Complexity**
- **Impact**: 2-3 day delay
- **Mitigation**: Can cut optional features (charts, advanced filters). Focus on core CRUD.

**Risk 2: Integration Testing Reveals Issues**
- **Impact**: 1-2 day delay
- **Mitigation**: Daily testing during development. Fix bugs incrementally.

**Risk 3: Scope Creep**
- **Impact**: Variable
- **Mitigation**: Strict adherence to MVP scope. Document requests as post-MVP features.

### Mitigation Strategies

1. **Daily Progress Checks**
   - Review completed tasks daily
   - Identify blockers early
   - Adjust schedule if needed

2. **Parallel Development**
   - Backend and frontend can progress simultaneously after Phase 3
   - One developer can work API while another starts frontend setup

3. **Incremental Testing**
   - Test each component as built
   - Don't wait for Phase 9 for all testing

4. **Scope Management**
   - Keep "nice to have" list separate
   - Only add to MVP if ahead of schedule

---

## Post-MVP Roadmap

### Milestone 2: Real Data Integration (2-3 weeks)
**Objectives**:
- Connect to live Solana validators
- Automated periodic ingestion
- Data normalization pipeline

**Tasks**:
- Ingestion orchestration service
- Scheduling (cron or Celery)
- Error handling and retry logic
- Data validation and reconciliation

### Milestone 3: Partner Portal (1-2 weeks)
**Objectives**:
- Partner user login
- Self-service commission viewing
- Download statements

**Tasks**:
- Extend RBAC for partner users
- Partner-scoped API endpoints
- Partner UI (simplified admin UI)
- Statement PDF generation

### Milestone 4: Advanced Commission Engine (2-3 weeks)
**Objectives**:
- STAKE_WEIGHT attribution
- Tiered commission rates
- Commission caps and floors
- Override workflows

**Tasks**:
- Enhanced commission service
- Approval workflow
- Manual override UI
- Recalculation jobs

### Milestone 5: Payment Tracking (1-2 weeks)
**Objectives**:
- Invoice generation
- Payment status tracking
- Reconciliation

**Tasks**:
- Payment models and API
- Invoice PDF generation
- Payment UI
- Email notifications

### Milestone 6: Ethereum Support (3-4 weeks)
**Objectives**:
- Add Ethereum chain
- EVM data adapters
- Multi-chain aggregation

**Tasks**:
- Ethereum chain configuration
- EVM RPC adapter
- Flashbots MEV adapter
- Multi-chain UI updates

---

## Appendix: File Structure Reference

### Backend Structure
```
src/
├── main.py                      # FastAPI app entry
├── core/
│   ├── models/
│   │   ├── users.py            # NEW: User, UserRole
│   │   ├── chains.py           # EXISTING
│   │   ├── staging.py          # EXISTING
│   │   ├── canonical.py        # EXISTING
│   │   └── computation.py      # EXISTING
│   ├── schemas/                # NEW: All Pydantic DTOs
│   │   ├── auth.py
│   │   ├── chains.py
│   │   ├── validators.py
│   │   ├── partners.py
│   │   ├── agreements.py
│   │   └── commissions.py
│   ├── repositories/           # NEW: Data access layer
│   │   ├── base.py
│   │   ├── chains.py
│   │   ├── validators.py
│   │   ├── partners.py
│   │   ├── agreements.py
│   │   └── commissions.py
│   ├── services/               # NEW: Business logic
│   │   ├── partner_service.py
│   │   ├── agreement_service.py
│   │   ├── commission_service.py
│   │   └── ingestion_service.py  # OPTIONAL
│   ├── security.py             # EXISTING (JWT utils)
│   └── logging.py              # EXISTING
├── api/
│   ├── deps.py                 # NEW: Dependencies
│   └── v1/                     # NEW: API endpoints
│       ├── auth.py
│       ├── chains.py
│       ├── validators.py
│       ├── partners.py
│       ├── agreements.py
│       ├── commissions.py
│       └── ingestion.py        # OPTIONAL
├── adapters/                   # EXISTING
├── config/                     # EXISTING
└── db/                         # EXISTING

scripts/
├── seed_admin.py               # NEW
└── seed_mvp_data.py            # NEW
```

### Frontend Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── Layout.tsx
│   │   ├── Nav.tsx
│   │   ├── ProtectedRoute.tsx
│   │   ├── AddValidatorDialog.tsx
│   │   ├── PartnerForm.tsx
│   │   ├── AgreementForm.tsx
│   │   └── CommissionBreakdownDialog.tsx
│   ├── pages/
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Validators.tsx
│   │   ├── ValidatorDetail.tsx
│   │   ├── Partners.tsx
│   │   ├── Agreements.tsx
│   │   ├── Commissions.tsx
│   │   └── Statements.tsx
│   ├── services/
│   │   ├── api.ts             # Axios instance
│   │   ├── auth.ts            # Auth API calls
│   │   ├── validators.ts      # Validator API calls
│   │   ├── partners.ts        # Partner API calls
│   │   ├── agreements.ts      # Agreement API calls
│   │   └── commissions.ts     # Commission API calls
│   ├── hooks/
│   │   └── useAuth.ts
│   ├── types/
│   │   └── index.ts           # TypeScript interfaces
│   ├── App.tsx
│   └── main.tsx
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-28
**Status**: Ready for Implementation
**Next Step**: Begin Phase 1 - Backend Foundation
