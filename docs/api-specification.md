# API Specification - Multi-Chain Validator P&L & Partner Commissions

## API Overview

**Base URL**: `/v1`
**Authentication**: JWT Bearer tokens
**Content-Type**: `application/json`
**Response Format**: `{ "data": <result>, "error": null }` or `{ "data": null, "error": {" message": "...", "code": "..."} }`

## Authentication

### POST /auth/login

Authenticate user and receive JWT token.

**Request**:
```json
{
  "username": "user@example.com",
  "password": "secure_password"
}
```

**Response**:
```json
{
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer",
    "expires_in": 2592000,
    "user": {
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "username": "user@example.com",
      "role": "PARTNER",
      "partner_id": "uuid-here"
    }
  },
  "error": null
}
```

**Errors**:
- `401 UNAUTHORIZED` - Invalid credentials
- `403 FORBIDDEN` - User account inactive

---

### POST /auth/refresh

Refresh access token.

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "data": {
    "access_token": "new_token_here",
    "expires_in": 2592000
  },
  "error": null
}
```

---

## Chain Operations

### GET /chains

List all configured blockchain networks.

**RBAC**: All roles
**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "data": [
    {
      "chain_id": "solana-mainnet",
      "name": "Solana Mainnet",
      "period_type": "EPOCH",
      "native_unit": "lamports",
      "native_decimals": 9,
      "finality_lag": 2,
      "is_active": true
    },
    {
      "chain_id": "ethereum-mainnet",
      "name": "Ethereum Mainnet",
      "period_type": "BLOCK_WINDOW",
      "native_unit": "wei",
      "native_decimals": 18,
      "finality_lag": 100,
      "is_active": true
    }
  ],
  "error": null
}
```

**Notes**: Partner users may only see chains in their `allowed_chain_ids` scope.

---

### GET /chains/{chain_id}/periods

List finalized periods for a chain.

**RBAC**: All roles
**Headers**: `Authorization: Bearer <token>`
**Path Parameters**:
- `chain_id` (required): Chain identifier

**Query Parameters**:
- `from` (optional): Start date (ISO 8601)
- `to` (optional): End date (ISO 8601)
- `limit` (optional, default=100): Max results
- `offset` (optional, default=0): Pagination offset

**Response**:
```json
{
  "data": {
    "periods": [
      {
        "period_id": "uuid-here",
        "chain_id": "solana-mainnet",
        "period_identifier": "850",
        "period_start": "2025-01-15T00:00:00Z",
        "period_end": "2025-01-17T00:00:00Z",
        "is_finalized": true,
        "finalized_at": "2025-01-19T00:00:00Z"
      }
    ],
    "total": 150,
    "limit": 100,
    "offset": 0
  },
  "error": null
}
```

**Errors**:
- `404 NOT_FOUND` - Chain not found
- `403 FORBIDDEN` - Chain not in user's allowed scope

---

## Validator P&L

### GET /chains/{chain_id}/validators/{validator_key}/pnl

Get validator P&L for period range.

**RBAC**: Admin, Finance, Ops (full access); Partner (only if scoped to validator)
**Headers**: `Authorization: Bearer <token>`
**Path Parameters**:
- `chain_id` (required): Chain identifier
- `validator_key` (required): Validator public key

**Query Parameters**:
- `from` (required): Start period identifier
- `to` (required): End period identifier

**Response**:
```json
{
  "data": [
    {
      "pnl_id": "uuid-here",
      "chain_id": "solana-mainnet",
      "period_id": "uuid-here",
      "period_identifier": "850",
      "validator_key": "ABC123...",
      "exec_fees_native": "1500000000",
      "mev_tips_native": "800000000",
      "vote_rewards_native": "2000000000",
      "commission_native": "100000000",
      "total_revenue_native": "4400000000",
      "computed_at": "2025-01-20T10:00:00Z"
    }
  ],
  "error": null
}
```

**Errors**:
- `403 FORBIDDEN` - Partner not scoped to this validator
- `404 NOT_FOUND` - Validator not found

**Notes**: Amounts in native units (lamports for Solana, wei for Ethereum). Convert using `native_decimals` from chain config.

---

## Partner Commissions

### GET /chains/{chain_id}/partners/{partner_id}/commissions

Get commission lines for a partner.

**RBAC**: Admin, Finance, Ops (all partners); Partner (self only)
**Headers**: `Authorization: Bearer <token>`
**Path Parameters**:
- `chain_id` (required): Chain identifier
- `partner_id` (required): Partner UUID

**Query Parameters**:
- `from` (required): Start period identifier
- `to` (required): End period identifier
- `limit` (optional, default=100): Max results
- `offset` (optional, default=0): Pagination offset

**Response**:
```json
{
  "data": {
    "commission_lines": [
      {
        "line_id": "uuid-here",
        "agreement_id": "uuid-here",
        "agreement_version": 1,
        "rule_id": "uuid-here",
        "partner_id": "uuid-here",
        "chain_id": "solana-mainnet",
        "period_id": "uuid-here",
        "period_identifier": "850",
        "validator_key": "ABC123...",
        "revenue_component": "MEV_TIPS",
        "attribution_method": "FIXED_SHARE",
        "base_amount_native": "800000000",
        "commission_rate_bps": 500,
        "pre_override_amount_native": "40000000",
        "override_amount_native": null,
        "override_reason": null,
        "final_amount_native": "40000000",
        "computed_at": "2025-01-20T10:00:00Z"
      }
    ],
    "total": 25,
    "limit": 100,
    "offset": 0
  },
  "error": null
}
```

**Errors**:
- `403 FORBIDDEN` - Partner querying other partner's data
- `404 NOT_FOUND` - Partner not found

---

### GET /chains/{chain_id}/partners/{partner_id}/statements/{period_id}

Get monthly commission statement for partner.

**RBAC**: Admin, Finance (all partners); Partner (self only)
**Headers**: `Authorization: Bearer <token>`
**Path Parameters**:
- `chain_id` (required): Chain identifier
- `partner_id` (required): Partner UUID
- `period_id` (required): Period UUID

**Response**:
```json
{
  "data": {
    "statement_id": "uuid-here",
    "partner_id": "uuid-here",
    "partner_name": "Acme Introductions LLC",
    "chain_id": "solana-mainnet",
    "period_id": "uuid-here",
    "period_identifier": "850",
    "period_start": "2025-01-15T00:00:00Z",
    "period_end": "2025-01-17T00:00:00Z",
    "total_commission_native": "120000000",
    "line_count": 5,
    "status": "RELEASED",
    "approved_by": "user-uuid",
    "approved_at": "2025-01-21T09:00:00Z",
    "released_by": "user-uuid",
    "released_at": "2025-01-21T10:00:00Z",
    "commission_lines": [
      {
        "line_id": "uuid-here",
        "validator_key": "ABC123...",
        "revenue_component": "MEV_TIPS",
        "final_amount_native": "40000000"
      }
    ]
  },
  "error": null
}
```

**Errors**:
- `403 FORBIDDEN` - Partner querying other partner's statement
- `404 NOT_FOUND` - Statement not found

---

### GET /chains/{chain_id}/partners/{partner_id}/statements/{period_id}/export

Export commission statement as CSV.

**RBAC**: Admin, Finance, Partner (self only)
**Headers**: `Authorization: Bearer <token>`
**Path Parameters**: Same as GET statement

**Response**: CSV file download

**Content-Disposition**: `attachment; filename="commission_statement_{partner}_{period}.csv"`

---

## Agreements Management

### GET /agreements

List agreements with optional filtering.

**RBAC**: Admin, Finance only
**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
- `partner_id` (optional): Filter by partner
- `status` (optional): Filter by status (DRAFT, ACTIVE, SUSPENDED, TERMINATED)
- `limit` (optional, default=50): Max results
- `offset` (optional, default=0): Pagination offset

**Response**:
```json
{
  "data": {
    "agreements": [
      {
        "agreement_id": "uuid-here",
        "partner_id": "uuid-here",
        "partner_name": "Acme Introductions LLC",
        "agreement_name": "Standard Commission Agreement",
        "current_version": 2,
        "status": "ACTIVE",
        "effective_from": "2025-01-01T00:00:00Z",
        "effective_until": null,
        "created_at": "2024-12-15T00:00:00Z",
        "updated_at": "2025-01-10T00:00:00Z"
      }
    ],
    "total": 15,
    "limit": 50,
    "offset": 0
  },
  "error": null
}
```

---

### GET /agreements/{agreement_id}

Get agreement details with current version.

**RBAC**: Admin, Finance only
**Headers**: `Authorization: Bearer <token>`
**Path Parameters**:
- `agreement_id` (required): Agreement UUID

**Response**:
```json
{
  "data": {
    "agreement_id": "uuid-here",
    "partner_id": "uuid-here",
    "partner_name": "Acme Introductions LLC",
    "agreement_name": "Standard Commission Agreement",
    "current_version": 2,
    "status": "ACTIVE",
    "effective_from": "2025-01-01T00:00:00Z",
    "effective_until": null,
    "rules": [
      {
        "rule_id": "uuid-here",
        "version_number": 2,
        "rule_order": 1,
        "chain_id": "solana-mainnet",
        "validator_key": null,
        "revenue_component": "MEV_TIPS",
        "attribution_method": "FIXED_SHARE",
        "commission_rate_bps": 500,
        "floor_amount_native": null,
        "cap_amount_native": "1000000000000",
        "tier_config": null,
        "is_active": true
      }
    ],
    "created_at": "2024-12-15T00:00:00Z",
    "updated_at": "2025-01-10T00:00:00Z"
  },
  "error": null
}
```

---

### GET /agreements/{agreement_id}/versions

Get agreement version history.

**RBAC**: Admin, Finance only
**Headers**: `Authorization: Bearer <token>`
**Path Parameters**:
- `agreement_id` (required): Agreement UUID

**Response**:
```json
{
  "data": [
    {
      "version_id": "uuid-here",
      "agreement_id": "uuid-here",
      "version_number": 2,
      "effective_from": "2025-01-10T00:00:00Z",
      "effective_until": null,
      "created_by": "user-uuid",
      "created_by_username": "admin@example.com",
      "created_at": "2025-01-10T00:00:00Z",
      "changes_summary": "Updated commission rate from 3% to 5%"
    },
    {
      "version_id": "uuid-here",
      "agreement_id": "uuid-here",
      "version_number": 1,
      "effective_from": "2025-01-01T00:00:00Z",
      "effective_until": "2025-01-10T00:00:00Z",
      "created_by": "user-uuid",
      "created_by_username": "admin@example.com",
      "created_at": "2024-12-15T00:00:00Z",
      "changes_summary": "Initial agreement"
    }
  ],
  "error": null
}
```

---

### POST /agreements

Create new agreement.

**RBAC**: Admin, Finance only
**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "partner_id": "uuid-here",
  "agreement_name": "Standard Commission Agreement",
  "effective_from": "2025-02-01T00:00:00Z",
  "effective_until": null,
  "rules": [
    {
      "rule_order": 1,
      "chain_id": "solana-mainnet",
      "validator_key": null,
      "revenue_component": "MEV_TIPS",
      "attribution_method": "FIXED_SHARE",
      "commission_rate_bps": 500,
      "floor_amount_native": null,
      "cap_amount_native": "1000000000000"
    }
  ]
}
```

**Response**:
```json
{
  "data": {
    "agreement_id": "new-uuid-here",
    "status": "DRAFT",
    "current_version": 1,
    "created_at": "2025-01-22T10:00:00Z"
  },
  "error": null
}
```

**Errors**:
- `400 BAD_REQUEST` - Validation errors
- `404 NOT_FOUND` - Partner not found

---

### PUT /agreements/{agreement_id}

Update agreement (creates new version).

**RBAC**: Admin, Finance only
**Headers**: `Authorization: Bearer <token>`
**Path Parameters**:
- `agreement_id` (required): Agreement UUID

**Request**:
```json
{
  "effective_from": "2025-02-15T00:00:00Z",
  "rules": [
    {
      "rule_order": 1,
      "chain_id": "solana-mainnet",
      "validator_key": null,
      "revenue_component": "MEV_TIPS",
      "attribution_method": "FIXED_SHARE",
      "commission_rate_bps": 600,
      "floor_amount_native": null,
      "cap_amount_native": "1000000000000"
    }
  ],
  "reason": "Updated commission rate per contract amendment"
}
```

**Response**:
```json
{
  "data": {
    "agreement_id": "uuid-here",
    "new_version": 3,
    "effective_from": "2025-02-15T00:00:00Z",
    "updated_at": "2025-01-22T10:00:00Z"
  },
  "error": null
}
```

---

### PATCH /agreements/{agreement_id}/status

Change agreement status.

**RBAC**: Admin, Finance only
**Headers**: `Authorization: Bearer <token>`
**Path Parameters**:
- `agreement_id` (required): Agreement UUID

**Request**:
```json
{
  "status": "ACTIVE",
  "reason": "Agreement signed by partner"
}
```

**Response**:
```json
{
  "data": {
    "agreement_id": "uuid-here",
    "status": "ACTIVE",
    "updated_at": "2025-01-22T10:00:00Z"
  },
  "error": null
}
```

**Allowed Transitions**:
- DRAFT → ACTIVE
- ACTIVE → SUSPENDED
- SUSPENDED → ACTIVE
- ACTIVE → TERMINATED (irreversible)

---

## Commission Overrides

### POST /overrides

Create commission override.

**RBAC**: Admin, Finance only
**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "commission_line_id": "uuid-here",
  "override_amount_native": "50000000",
  "reason": "Manual adjustment per partner agreement amendment"
}
```

**Response**:
```json
{
  "data": {
    "line_id": "uuid-here",
    "pre_override_amount_native": "40000000",
    "override_amount_native": "50000000",
    "final_amount_native": "50000000",
    "override_reason": "Manual adjustment per partner agreement amendment",
    "override_user_id": "user-uuid",
    "override_timestamp": "2025-01-22T10:00:00Z"
  },
  "error": null
}
```

**Errors**:
- `400 BAD_REQUEST` - Missing reason or invalid amount
- `404 NOT_FOUND` - Commission line not found

---

## Operations

### POST /recompute

Recompute P&L and commissions for period range.

**RBAC**: Admin, Finance, Ops only
**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "chain_id": "solana-mainnet",
  "from_period": "840",
  "to_period": "850",
  "force": false
}
```

**Response**:
```json
{
  "data": {
    "job_id": "uuid-here",
    "chain_id": "solana-mainnet",
    "from_period": "840",
    "to_period": "850",
    "status": "RUNNING",
    "started_at": "2025-01-22T10:00:00Z"
  },
  "error": null
}
```

**Query Parameters**:
- `force` (optional, default=false): Force recomputation even if already computed

**Notes**: Asynchronous operation. Use `/jobs/{job_id}` to poll status.

---

### GET /ingestion/health

Get ingestion health and lag metrics.

**RBAC**: Admin, Ops only
**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "data": {
    "chains": [
      {
        "chain_id": "solana-mainnet",
        "expected_period": "850",
        "latest_ingested": "848",
        "lag_periods": 2,
        "last_success": "2025-01-20T10:00:00Z",
        "last_failure": null,
        "status": "HEALTHY"
      }
    ]
  },
  "error": null
}
```

**Status Values**:
- `HEALTHY` - Lag within acceptable threshold (< 5 periods)
- `DEGRADED` - Lag between 5-10 periods
- `UNHEALTHY` - Lag > 10 periods or recent failures

---

### GET /jobs/{job_id}

Get background job status.

**RBAC**: Admin, Finance, Ops only
**Headers**: `Authorization: Bearer <token>`
**Path Parameters**:
- `job_id` (required): Job UUID

**Response**:
```json
{
  "data": {
    "job_id": "uuid-here",
    "job_type": "RECOMPUTE",
    "status": "SUCCESS",
    "started_at": "2025-01-22T10:00:00Z",
    "completed_at": "2025-01-22T10:05:00Z",
    "progress": 100,
    "result": {
      "periods_processed": 11,
      "validator_pnl_updated": 55,
      "commission_lines_created": 120
    },
    "error_message": null
  },
  "error": null
}
```

**Job Status Values**:
- `PENDING` - Job queued
- `RUNNING` - Job in progress
- `SUCCESS` - Job completed successfully
- `FAILED` - Job failed with error

---

## Error Responses

All errors follow consistent format:

```json
{
  "data": null,
  "error": {
    "message": "Human-readable error message",
    "code": "ERROR_CODE",
    "details": {
      "field": "validation_error_details"
    }
  }
}
```

### HTTP Status Codes

- `200 OK` - Request successful
- `201 CREATED` - Resource created
- `400 BAD_REQUEST` - Validation error or malformed request
- `401 UNAUTHORIZED` - Missing or invalid authentication
- `403 FORBIDDEN` - Insufficient permissions
- `404 NOT_FOUND` - Resource not found
- `409 CONFLICT` - Conflicting state (e.g., duplicate resource)
- `429 TOO_MANY_REQUESTS` - Rate limit exceeded
- `500 INTERNAL_SERVER_ERROR` - Server error
- `503 SERVICE_UNAVAILABLE` - Service temporarily unavailable

### Common Error Codes

- `INVALID_CREDENTIALS` - Login failed
- `TOKEN_EXPIRED` - JWT token expired
- `INSUFFICIENT_PERMISSIONS` - User lacks required role
- `RESOURCE_NOT_FOUND` - Requested resource doesn't exist
- `VALIDATION_ERROR` - Request body validation failed
- `SCOPE_VIOLATION` - Partner accessing out-of-scope data
- `CHAIN_NOT_FOUND` - Invalid chain_id
- `PERIOD_NOT_FINALIZED` - Attempting to query non-finalized period

---

## Rate Limiting

**Default Limits**:
- **Authenticated requests**: 1000 requests/hour per user
- **Login endpoint**: 10 requests/minute per IP

**Headers**:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1737561600
```

**429 Response**:
```json
{
  "data": null,
  "error": {
    "message": "Rate limit exceeded. Retry after 60 seconds.",
    "code": "RATE_LIMIT_EXCEEDED",
    "details": {
      "retry_after": 60
    }
  }
}
```

---

## Pagination

List endpoints support cursor-based pagination:

**Request**:
```
GET /chains/solana-mainnet/validators/{validator}/pnl?from=800&to=850&limit=20&offset=0
```

**Response**:
```json
{
  "data": {
    "items": [...],
    "total": 51,
    "limit": 20,
    "offset": 0,
    "has_more": true
  },
  "error": null
}
```

**Pagination Parameters**:
- `limit` - Max items per page (default varies by endpoint, max 500)
- `offset` - Number of items to skip

---

## Filtering & Sorting

List endpoints support filtering and sorting:

**Query Parameters**:
- `sort_by` - Field to sort by
- `sort_order` - `asc` or `desc` (default: `desc`)

**Example**:
```
GET /agreements?partner_id={uuid}&status=ACTIVE&sort_by=created_at&sort_order=desc
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-22
**Status**: Draft
