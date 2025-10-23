# RBAC Policy Matrix (MVP)

## Roles
- **Admin** — full control (system owner).
- **Finance** — agreements, overrides, statements, read all data.
- **Ops** — ingestion, reconciliation, system health, read all data.
- **Partner** — read-only access scoped to _their_ introductions & commissions.
- **Auditor** — read-only access to all data (time-boxed, optional).

## Permissions by Role

| Capability                                   | Admin | Finance | Ops | Partner | Auditor |
|----------------------------------------------|:----:|:------:|:---:|:------:|:------:|
| Manage users & roles                          |  ✅  |   ❌   | ❌  |   ❌   |   ❌   |
| Configure chains & providers                  |  ✅  |   ❌   | ✅  |   ❌   |   ❌   |
| View chain/validator P&L (all)                |  ✅  |   ✅   | ✅  |   ❌   |   ✅   |
| View partner commissions (all partners)       |  ✅  |   ✅   | ✅  |   ❌   |   ✅   |
| View partner commissions (self only)          |  ✅  |   ✅   | ✅  |   ✅   |   ✅   |
| Create/update agreements & versions           |  ✅  |   ✅   | ❌  |   ❌   |   ❌   |
| Create/update agreement rules                 |  ✅  |   ✅   | ❌  |   ❌   |   ❌   |
| Create overrides                              |  ✅  |   ✅   | ❌  |   ❌   |   ❌   |
| Approve/release statements                    |  ✅  |   ✅   | ❌  |   ❌   |   ❌   |
| Run recompute (period range)                  |  ✅  |   ✅   | ✅  |   ❌   |   ❌   |
| Start/stop ingestion & backfills              |  ✅  |   ❌   | ✅  |   ❌   |   ❌   |
| View ingestion health & reconciliation        |  ✅  |   ✅   | ✅  |   ❌   |   ✅   |
| Export CSV/PDF reports                        |  ✅  |   ✅   | ✅  |   ✅*  |   ✅   |
| Read audit log                                |  ✅  |   ✅   | ✅  |   ❌   |   ✅   |

\* Partner can export **only** their scoped data.

## API Access Matrix (by Role)

**Notes:**
- All endpoints require JWT. Tokens carry `role`, and for Partner also `introducer_id` (and optional `allowed_chain_ids`, `allowed_validator_keys`).
- Every API is **chain-scoped** and applies **row-level filters** based on role + claims.

| Endpoint (GET unless noted)                                              | Admin | Finance | Ops | Partner | Auditor | Scope / Filters |
|--------------------------------------------------------------------------|:----:|:------:|:---:|:------:|:------:|------------------|
| `/chains`                                                                 | ✅ | ✅ | ✅ | ✅ | ✅ | All chains (Partner may be filtered) |
| `/chains/{chain_id}/periods`                                             | ✅ | ✅ | ✅ | ✅ | ✅ | All; Partner filtered by chains claim |
| `/chains/{c}/validators/{v}/pnl`                                         | ✅ | ✅ | ✅ | ❌ | ✅ | Partner: ❌ (unless explicitly granted) |
| `/chains/{c}/partners/{pid}/commissions`                                 | ✅ | ✅ | ✅ | ✅ | ✅ | Partner: `pid` must equal token claim |
| `/agreements/{id}` + `/agreements/{id}/versions`                         | ✅ | ✅ | ❌ | ❌ | RO | Auditor read-only |
| `POST /recompute`                                                        | ✅ | ✅ | ✅ | ❌ | ❌ | Runs recompute jobs |
| `/ingestion/health`                                                      | ✅ | ✅ | ✅ | ❌ | ✅ | System status |
| `/audit/logs`                                                            | ✅ | ✅ | ✅ | ❌ | ✅ | Read-only |

## Data Scoping Rules
- **Partner** role:
  - Filter to rows where `introducer_id == token.introducer_id`.
  - Optional chain/validator narrowing via token claims.
  - No access to other partners’ data or global validator P&L by default.
- **Internal roles (Admin/Finance/Ops)**: Full access (optionally narrowed by policy).
- **Auditor**: Read-only across system; time-boxed accounts recommended.

## Operational Controls
- All mutating actions (agreements, rules, overrides, recompute) write to an **append-only audit log** with: user, timestamp, request hash, before/after snapshots.
- Optional **dual-approval** for releasing monthly statements to partners.
