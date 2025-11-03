# Issue #29: Wallet Attribution System - Database & Backend Foundation

**Session Date**: 2025-11-03
**Status**: 🟡 IN PROGRESS (50% Complete - Phase 1 of 2)
**Estimated Remaining**: 1 day (Phase 2)

---

## 📊 Overall Progress

**Completed**: 2/4 database migrations (50%)
**Next Session**: Complete migrations 3-4, then ORM models and services

### Phase 1: Database Migrations ✅ 50% Complete

| Migration | Status | File | Description |
|-----------|--------|------|-------------|
| 1. partner_wallets | ✅ DONE | `af2383dc7482_add_partner_wallets_table_for_wallet_.py` | Wallet→partner mapping with exclusivity |
| 2. canonical_stake_events | ✅ DONE | `8ea71cd7ef5d_add_canonical_stake_events_table_for_.py` | Staking lifecycle tracking |
| 3. canonical_staker_rewards_detail | 🔄 TODO | Not created yet | Per-staker reward granularity |
| 4. agreements/commission_lines enhancements | 🔄 TODO | Not created yet | Add wallet attribution fields |

### Phase 2: Application Layer 🔄 Pending

| Component | Status | Location | Description |
|-----------|--------|----------|-------------|
| ORM Models | 🔄 TODO | `src/core/models/` | Add PartnerWallet, CanonicalStakeEvent, CanonicalStakerRewardsDetail |
| Repositories | 🔄 TODO | `src/repositories/` | Data access for wallet entities |
| Services | 🔄 TODO | `src/core/services/` | Wallet management + attribution logic |
| API Endpoints | 🔄 TODO | `src/api/routers/` | Partner wallets CRUD operations |
| Seed Data | 🔄 TODO | `scripts/seed_mvp_data.py` | Wallet test data |
| Tests | 🔄 TODO | Various | Validation and quality checks |

---

## ✅ Completed Work (Session 2025-11-03)

### Migration 1: partner_wallets Table

**File**: `alembic/versions/af2383dc7482_add_partner_wallets_table_for_wallet_.py`
**Migration ID**: af2383dc7482
**Status**: ✅ Applied to database

**Schema**:
```sql
CREATE TABLE partner_wallets (
    wallet_id UUID PRIMARY KEY,
    partner_id UUID NOT NULL REFERENCES partners(partner_id) ON DELETE CASCADE,
    chain_id VARCHAR(50) NOT NULL REFERENCES chains(chain_id) ON DELETE CASCADE,
    wallet_address VARCHAR(100) NOT NULL,
    introduced_date DATE NOT NULL,  -- Supports retroactive attribution
    is_active BOOLEAN NOT NULL DEFAULT true,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Wallet exclusivity: one wallet can only belong to one partner per chain
    CONSTRAINT uq_partner_wallets_chain_address UNIQUE (chain_id, wallet_address),
    CONSTRAINT ck_partner_wallets_address_not_empty CHECK (wallet_address <> '')
);

CREATE INDEX idx_partner_wallets_partner ON partner_wallets(partner_id);
CREATE INDEX idx_partner_wallets_chain ON partner_wallets(chain_id);
CREATE INDEX idx_partner_wallets_address ON partner_wallets(wallet_address);
CREATE INDEX idx_partner_wallets_active ON partner_wallets(is_active);
```

**Key Design Decisions**:
- ✅ **Wallet Exclusivity**: UNIQUE(chain_id, wallet_address) enforces one wallet → one partner
- ✅ **Retroactive Support**: introduced_date allows historical wallet attribution
- ✅ **Soft Delete**: is_active flag for audit trail preservation
- ✅ **Cascade Delete**: Automatically removes wallets when partner is deleted

**Testing**: ✅ Migration applied successfully, constraints verified

---

### Migration 2: canonical_stake_events Table

**File**: `alembic/versions/8ea71cd7ef5d_add_canonical_stake_events_table_for_.py`
**Migration ID**: 8ea71cd7ef5d
**Status**: ✅ Applied to database

**Schema**:
```sql
-- Enum type for event lifecycle
CREATE TYPE stake_event_type AS ENUM ('STAKE', 'UNSTAKE', 'RESTAKE');

CREATE TABLE canonical_stake_events (
    stake_event_id UUID PRIMARY KEY,
    chain_id VARCHAR(50) NOT NULL REFERENCES chains(chain_id) ON DELETE CASCADE,
    period_id UUID NOT NULL REFERENCES canonical_periods(period_id) ON DELETE CASCADE,
    validator_key VARCHAR(100) NOT NULL,
    staker_address VARCHAR(100) NOT NULL,
    event_type stake_event_type NOT NULL,
    stake_amount_native NUMERIC(38, 18) NOT NULL,
    event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    source_provider_id UUID NOT NULL REFERENCES providers(provider_id) ON DELETE RESTRICT,
    source_payload_id UUID NOT NULL REFERENCES staging_payloads(payload_id) ON DELETE RESTRICT,
    normalized_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_canonical_stake_events_amount_positive CHECK (stake_amount_native >= 0),
    CONSTRAINT ck_canonical_stake_events_staker_not_empty CHECK (staker_address <> '')
);

CREATE INDEX idx_canonical_stake_events_chain_period ON canonical_stake_events(chain_id, period_id);
CREATE INDEX idx_canonical_stake_events_validator ON canonical_stake_events(validator_key);
CREATE INDEX idx_canonical_stake_events_staker ON canonical_stake_events(staker_address);
CREATE INDEX idx_canonical_stake_events_timestamp ON canonical_stake_events(event_timestamp);
CREATE INDEX idx_canonical_stake_events_type ON canonical_stake_events(event_type);
```

**Key Design Decisions**:
- ✅ **Lifecycle Tracking**: STAKE/UNSTAKE/RESTAKE events for wallet validation
- ✅ **Temporal Ordering**: event_timestamp for chronological lifecycle analysis
- ✅ **Data Lineage**: source_provider_id + source_payload_id for traceability
- ✅ **Query Optimization**: Composite index on (chain_id, period_id) for period queries

**Testing**: ✅ Migration applied successfully, enum type created

**Technical Note**: Used `postgresql.ENUM(..., create_type=False)` in column definition to avoid duplicate enum creation errors. The enum is created explicitly via `op.execute()` in the upgrade function.

---

## 🔄 Remaining Work (Next Session)

### Migration 3: canonical_staker_rewards_detail Table

**Purpose**: Per-staker reward granularity by revenue component (EXEC_FEES, MEV, REWARDS)

**Estimated Time**: 30 minutes

**Schema Design**:
```sql
CREATE TABLE canonical_staker_rewards_detail (
    staker_reward_id UUID PRIMARY KEY,
    chain_id VARCHAR(50) NOT NULL REFERENCES chains(chain_id) ON DELETE CASCADE,
    period_id UUID NOT NULL REFERENCES canonical_periods(period_id) ON DELETE CASCADE,
    validator_key VARCHAR(100) NOT NULL,
    staker_address VARCHAR(100) NOT NULL,
    revenue_component revenuecomponent NOT NULL,  -- Existing enum: EXEC_FEES, MEV, REWARDS
    reward_amount_native NUMERIC(38, 18) NOT NULL,
    source_provider_id UUID NOT NULL REFERENCES providers(provider_id) ON DELETE RESTRICT,
    source_payload_id UUID NOT NULL REFERENCES staging_payloads(payload_id) ON DELETE RESTRICT,
    normalized_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- One record per staker per validator per period per component
    CONSTRAINT uq_canonical_staker_rewards_detail
        UNIQUE (chain_id, period_id, validator_key, staker_address, revenue_component),
    CONSTRAINT ck_canonical_staker_rewards_detail_amount_positive
        CHECK (reward_amount_native >= 0),
    CONSTRAINT ck_canonical_staker_rewards_detail_staker_not_empty
        CHECK (staker_address <> '')
);

CREATE INDEX idx_canonical_staker_rewards_detail_chain_period
    ON canonical_staker_rewards_detail(chain_id, period_id);
CREATE INDEX idx_canonical_staker_rewards_detail_validator
    ON canonical_staker_rewards_detail(validator_key);
CREATE INDEX idx_canonical_staker_rewards_detail_staker
    ON canonical_staker_rewards_detail(staker_address);
CREATE INDEX idx_canonical_staker_rewards_detail_component
    ON canonical_staker_rewards_detail(revenue_component);
```

**Key Points**:
- Reuses existing `revenuecomponent` enum (no new enum needed)
- UNIQUE constraint prevents duplicate staker-component records
- Enables wallet attribution calculation: SUM(rewards WHERE staker IN partner_wallets)

**Implementation Steps**:
1. Run: `./scripts/migrate.sh create "add canonical staker rewards detail table for per-staker revenue attribution"`
2. Edit migration file with above schema
3. Add proper downgrade function (drop table, drop indexes)
4. Run: `./scripts/migrate.sh upgrade`
5. Verify with: `./scripts/migrate.sh current`

---

### Migration 4: Enhance agreements and partner_commission_lines

**Purpose**: Add wallet attribution fields to support wallet-level commission tracking

**Estimated Time**: 30 minutes

**Schema Changes**:
```sql
-- Add to agreements table
ALTER TABLE agreements
    ADD COLUMN wallet_attribution_enabled BOOLEAN NOT NULL DEFAULT false;

CREATE INDEX idx_agreements_wallet_attribution
    ON agreements(wallet_attribution_enabled);

COMMENT ON COLUMN agreements.wallet_attribution_enabled IS
    'Enable wallet-level attribution for this agreement (applies to all rules)';

-- Add to partner_commission_lines table
ALTER TABLE partner_commission_lines
    ADD COLUMN wallet_address VARCHAR(100);

CREATE INDEX idx_partner_commission_lines_wallet
    ON partner_commission_lines(wallet_address);

COMMENT ON COLUMN partner_commission_lines.wallet_address IS
    'Wallet address for wallet-attributed commissions (null for total revenue method)';
```

**Key Points**:
- `wallet_attribution_enabled` is agreement-level setting (applies to ALL rules)
- `wallet_address` in commission_lines tracks which wallet earned the commission
- Nullable wallet_address supports both attribution methods
- Backward compatible: defaults to false, existing records unaffected

**Implementation Steps**:
1. Run: `./scripts/migrate.sh create "add wallet attribution support to agreements and commission lines"`
2. Edit migration file with above schema
3. Add proper downgrade function (drop columns, drop indexes)
4. Run: `./scripts/migrate.sh upgrade`
5. Run: `./scripts/migrate.sh current` to verify

---

### ORM Models (src/core/models/)

**Estimated Time**: 1-1.5 hours

#### 1. PartnerWallet Model (computation.py)

**Location**: Add to `src/core/models/computation.py` after Partners model

**Implementation**:
```python
class PartnerWallet(BaseModel):
    """Partner-introduced staker wallets for commission attribution.

    Tracks which wallets belong to which partners, enabling wallet-level
    commission calculations based on rewards from specific staker wallets.

    Attributes:
        wallet_id: Unique wallet record identifier (UUID)
        partner_id: Reference to partner who introduced this wallet
        chain_id: Reference to chain
        wallet_address: Staker/delegator wallet public key address
        introduced_date: Date when partner introduced this wallet (supports retroactive)
        is_active: Soft delete flag
        notes: Optional notes about this wallet
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "partner_wallets"

    wallet_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique wallet record identifier",
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("partners.partner_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to partner who introduced this wallet",
    )

    chain_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("chains.chain_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to chain",
    )

    wallet_address: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Staker/delegator wallet public key address",
    )

    introduced_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date when partner introduced this wallet (supports retroactive)",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="Soft delete flag",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional notes about this wallet",
    )

    # Relationships
    partner: Mapped["Partners"] = relationship("Partners", back_populates="wallets")

    chain: Mapped["Chain"] = relationship("Chain", back_populates="partner_wallets")

    __table_args__ = (
        Index("idx_partner_wallets_partner", "partner_id"),
        Index("idx_partner_wallets_chain", "chain_id"),
        Index("idx_partner_wallets_address", "wallet_address"),
        Index("idx_partner_wallets_active", "is_active"),
        CheckConstraint("wallet_address <> ''", name="ck_partner_wallets_address_not_empty"),
        UniqueConstraint("chain_id", "wallet_address", name="uq_partner_wallets_chain_address"),
    )
```

**Also Update**:
- `Partners` model: Add `wallets: Mapped[list["PartnerWallet"]] = relationship(...)`
- `Chain` model: Add `partner_wallets: Mapped[list["PartnerWallet"]] = relationship(...)`

#### 2. CanonicalStakeEvent Model (chains.py)

**Location**: Add to `src/core/models/chains.py` after CanonicalStakeRewards

**First, create enum**:
```python
class StakeEventType(str, Enum):
    """Staking lifecycle event types."""
    STAKE = "STAKE"
    UNSTAKE = "UNSTAKE"
    RESTAKE = "RESTAKE"
```

**Model**:
```python
class CanonicalStakeEvent(BaseModel):
    """Staking lifecycle events for wallet attribution validation.

    Tracks when wallets stake/unstake from validators, enabling validation
    that wallets were actively staking during commission calculation periods.

    Attributes:
        stake_event_id: Unique stake event identifier (UUID)
        chain_id: Reference to chain
        period_id: Reference to canonical period when event occurred
        validator_key: Validator identifier where staking action occurred
        staker_address: Staker/delegator wallet address
        event_type: Type of staking lifecycle event (STAKE/UNSTAKE/RESTAKE)
        stake_amount_native: Stake amount in native chain units
        event_timestamp: Timestamp when staking event occurred
        source_provider_id: Reference to data provider (traceability)
        source_payload_id: Reference to staging payload (traceability)
        normalized_at: Timestamp when data was normalized
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "canonical_stake_events"

    stake_event_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique stake event identifier",
    )

    chain_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("chains.chain_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to chain",
    )

    period_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("canonical_periods.period_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to canonical period when event occurred",
    )

    validator_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Validator identifier where staking action occurred",
    )

    staker_address: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Staker/delegator wallet address",
    )

    event_type: Mapped[StakeEventType] = mapped_column(
        nullable=False,
        comment="Type of staking lifecycle event",
    )

    stake_amount_native: Mapped[float] = mapped_column(
        NUMERIC(38, 18),
        nullable=False,
        comment="Stake amount in native chain units (lamports, wei, etc.)",
    )

    event_timestamp: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        comment="Timestamp when staking event occurred",
    )

    source_provider_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("providers.provider_id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to data provider for traceability",
    )

    source_payload_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("staging_payloads.payload_id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to staging payload for traceability",
    )

    normalized_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when data was normalized",
    )

    # Relationships
    chain: Mapped["Chain"] = relationship("Chain", back_populates="canonical_stake_events")

    period: Mapped["CanonicalPeriod"] = relationship(
        "CanonicalPeriod", back_populates="canonical_stake_events"
    )

    source_provider: Mapped["Provider"] = relationship(
        "Provider", foreign_keys=[source_provider_id]
    )

    source_payload: Mapped["StagingPayload"] = relationship(
        "StagingPayload", foreign_keys=[source_payload_id]
    )

    __table_args__ = (
        Index("idx_canonical_stake_events_chain_period", "chain_id", "period_id"),
        Index("idx_canonical_stake_events_validator", "validator_key"),
        Index("idx_canonical_stake_events_staker", "staker_address"),
        Index("idx_canonical_stake_events_timestamp", "event_timestamp"),
        Index("idx_canonical_stake_events_type", "event_type"),
        CheckConstraint(
            "stake_amount_native >= 0",
            name="ck_canonical_stake_events_amount_positive",
        ),
        CheckConstraint(
            "staker_address <> ''",
            name="ck_canonical_stake_events_staker_not_empty",
        ),
    )
```

**Also Update**:
- `Chain` model: Add `canonical_stake_events: Mapped[list["CanonicalStakeEvent"]] = relationship(...)`
- `CanonicalPeriod` model: Add `canonical_stake_events: Mapped[list["CanonicalStakeEvent"]] = relationship(...)`
- `src/core/models/__init__.py`: Export StakeEventType and CanonicalStakeEvent

#### 3. CanonicalStakerRewardsDetail Model (chains.py)

**Location**: Add to `src/core/models/chains.py` after CanonicalStakeEvent

**Model**:
```python
class CanonicalStakerRewardsDetail(BaseModel):
    """Per-staker reward detail by revenue component for wallet attribution.

    Granular reward tracking at staker level broken down by revenue component,
    enabling precise wallet-level commission calculations.

    Attributes:
        staker_reward_id: Unique staker reward identifier (UUID)
        chain_id: Reference to chain
        period_id: Reference to canonical period
        validator_key: Validator identifier
        staker_address: Staker/delegator wallet address
        revenue_component: Revenue component (EXEC_FEES, MEV, REWARDS)
        reward_amount_native: Reward amount in native chain units
        source_provider_id: Reference to data provider (traceability)
        source_payload_id: Reference to staging payload (traceability)
        normalized_at: Timestamp when data was normalized
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "canonical_staker_rewards_detail"

    staker_reward_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique staker reward identifier",
    )

    chain_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("chains.chain_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to chain",
    )

    period_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("canonical_periods.period_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to canonical period",
    )

    validator_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Validator identifier",
    )

    staker_address: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Staker/delegator wallet address",
    )

    revenue_component: Mapped[RevenueComponent] = mapped_column(
        nullable=False,
        comment="Revenue component (EXEC_FEES, MEV, REWARDS)",
    )

    reward_amount_native: Mapped[float] = mapped_column(
        NUMERIC(38, 18),
        nullable=False,
        comment="Reward amount in native chain units",
    )

    source_provider_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("providers.provider_id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to data provider for traceability",
    )

    source_payload_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("staging_payloads.payload_id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to staging payload for traceability",
    )

    normalized_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when data was normalized",
    )

    # Relationships
    chain: Mapped["Chain"] = relationship("Chain", back_populates="canonical_staker_rewards_detail")

    period: Mapped["CanonicalPeriod"] = relationship(
        "CanonicalPeriod", back_populates="canonical_staker_rewards_detail"
    )

    source_provider: Mapped["Provider"] = relationship(
        "Provider", foreign_keys=[source_provider_id]
    )

    source_payload: Mapped["StagingPayload"] = relationship(
        "StagingPayload", foreign_keys=[source_payload_id]
    )

    __table_args__ = (
        Index("idx_canonical_staker_rewards_detail_chain_period", "chain_id", "period_id"),
        Index("idx_canonical_staker_rewards_detail_validator", "validator_key"),
        Index("idx_canonical_staker_rewards_detail_staker", "staker_address"),
        Index("idx_canonical_staker_rewards_detail_component", "revenue_component"),
        CheckConstraint(
            "reward_amount_native >= 0",
            name="ck_canonical_staker_rewards_detail_amount_positive",
        ),
        CheckConstraint(
            "staker_address <> ''",
            name="ck_canonical_staker_rewards_detail_staker_not_empty",
        ),
        UniqueConstraint(
            "chain_id",
            "period_id",
            "validator_key",
            "staker_address",
            "revenue_component",
            name="uq_canonical_staker_rewards_detail",
        ),
    )
```

**Also Update**:
- `Chain` model: Add `canonical_staker_rewards_detail: Mapped[list["CanonicalStakerRewardsDetail"]] = relationship(...)`
- `CanonicalPeriod` model: Add `canonical_staker_rewards_detail: Mapped[list["CanonicalStakerRewardsDetail"]] = relationship(...)`
- `src/core/models/__init__.py`: Export CanonicalStakerRewardsDetail

#### 4. Enhance Existing Models

**Agreements Model** (`src/core/models/computation.py`):
```python
# Add to Agreements class:

wallet_attribution_enabled: Mapped[bool] = mapped_column(
    Boolean,
    nullable=False,
    default=False,
    server_default=text("false"),
    comment="Enable wallet-level attribution for this agreement",
)

# Add to __table_args__:
Index("idx_agreements_wallet_attribution", "wallet_attribution_enabled"),
```

**PartnerCommissionLines Model** (`src/core/models/computation.py`):
```python
# Add to PartnerCommissionLines class:

wallet_address: Mapped[str | None] = mapped_column(
    String(100),
    nullable=True,
    comment="Wallet address for wallet-attributed commissions (null for total revenue method)",
)

# Add to __table_args__:
Index("idx_partner_commission_lines_wallet", "wallet_address"),
```

---

### Repositories (src/repositories/)

**Estimated Time**: 1 hour

Create three new repository files:

#### 1. partner_wallets.py

```python
"""Repository for partner wallet operations."""
from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.computation import PartnerWallet
from src.repositories.base import BaseRepository


class PartnerWalletRepository(BaseRepository[PartnerWallet]):
    """Repository for partner wallet CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(PartnerWallet, session)

    async def get_by_partner(
        self,
        partner_id: UUID,
        chain_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PartnerWallet]:
        """Get wallets for a partner with optional filters."""
        query = select(PartnerWallet).where(PartnerWallet.partner_id == partner_id)

        if chain_id is not None:
            query = query.where(PartnerWallet.chain_id == chain_id)

        if is_active is not None:
            query = query.where(PartnerWallet.is_active == is_active)

        query = query.order_by(PartnerWallet.introduced_date.desc())
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_address(
        self,
        chain_id: str,
        wallet_address: str,
    ) -> Optional[PartnerWallet]:
        """Get wallet by chain and address (enforces uniqueness)."""
        query = select(PartnerWallet).where(
            and_(
                PartnerWallet.chain_id == chain_id,
                PartnerWallet.wallet_address == wallet_address,
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_wallets_for_period(
        self,
        partner_id: UUID,
        chain_id: str,
        period_start_date: date,
    ) -> list[PartnerWallet]:
        """Get active wallets introduced before or during period."""
        query = select(PartnerWallet).where(
            and_(
                PartnerWallet.partner_id == partner_id,
                PartnerWallet.chain_id == chain_id,
                PartnerWallet.is_active == True,
                PartnerWallet.introduced_date <= period_start_date,
            )
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_partner(
        self,
        partner_id: UUID,
        is_active: Optional[bool] = None,
    ) -> int:
        """Count wallets for a partner."""
        return await self.count(
            PartnerWallet.partner_id == partner_id,
            PartnerWallet.is_active == is_active if is_active is not None else True,
        )
```

#### 2. stake_events.py

```python
"""Repository for canonical stake event operations."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.chains import CanonicalStakeEvent, StakeEventType
from src.repositories.base import BaseRepository


class StakeEventRepository(BaseRepository[CanonicalStakeEvent]):
    """Repository for stake event CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(CanonicalStakeEvent, session)

    async def get_by_staker(
        self,
        chain_id: str,
        staker_address: str,
        validator_key: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[CanonicalStakeEvent]:
        """Get stake events for a staker wallet."""
        query = select(CanonicalStakeEvent).where(
            and_(
                CanonicalStakeEvent.chain_id == chain_id,
                CanonicalStakeEvent.staker_address == staker_address,
            )
        )

        if validator_key is not None:
            query = query.where(CanonicalStakeEvent.validator_key == validator_key)

        if start_time is not None:
            query = query.where(CanonicalStakeEvent.event_timestamp >= start_time)

        if end_time is not None:
            query = query.where(CanonicalStakeEvent.event_timestamp <= end_time)

        query = query.order_by(CanonicalStakeEvent.event_timestamp.asc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_last_event_before(
        self,
        chain_id: str,
        staker_address: str,
        validator_key: str,
        timestamp: datetime,
        event_type: Optional[StakeEventType] = None,
    ) -> Optional[CanonicalStakeEvent]:
        """Get most recent event before a timestamp."""
        query = select(CanonicalStakeEvent).where(
            and_(
                CanonicalStakeEvent.chain_id == chain_id,
                CanonicalStakeEvent.staker_address == staker_address,
                CanonicalStakeEvent.validator_key == validator_key,
                CanonicalStakeEvent.event_timestamp <= timestamp,
            )
        )

        if event_type is not None:
            query = query.where(CanonicalStakeEvent.event_type == event_type)

        query = query.order_by(CanonicalStakeEvent.event_timestamp.desc())
        query = query.limit(1)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()
```

#### 3. staker_rewards.py

```python
"""Repository for canonical staker rewards detail operations."""
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.chains import CanonicalStakerRewardsDetail
from src.core.models.computation import RevenueComponent
from src.repositories.base import BaseRepository


class StakerRewardsDetailRepository(BaseRepository[CanonicalStakerRewardsDetail]):
    """Repository for staker rewards detail CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(CanonicalStakerRewardsDetail, session)

    async def get_by_staker_and_period(
        self,
        chain_id: str,
        period_id: UUID,
        staker_address: str,
        validator_key: Optional[str] = None,
        revenue_component: Optional[RevenueComponent] = None,
    ) -> list[CanonicalStakerRewardsDetail]:
        """Get rewards for a staker in a specific period."""
        query = select(CanonicalStakerRewardsDetail).where(
            and_(
                CanonicalStakerRewardsDetail.chain_id == chain_id,
                CanonicalStakerRewardsDetail.period_id == period_id,
                CanonicalStakerRewardsDetail.staker_address == staker_address,
            )
        )

        if validator_key is not None:
            query = query.where(CanonicalStakerRewardsDetail.validator_key == validator_key)

        if revenue_component is not None:
            query = query.where(CanonicalStakerRewardsDetail.revenue_component == revenue_component)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def sum_rewards_for_wallets(
        self,
        chain_id: str,
        period_id: UUID,
        wallet_addresses: list[str],
        validator_key: Optional[str] = None,
        revenue_component: Optional[RevenueComponent] = None,
    ) -> float:
        """Sum rewards for a list of wallet addresses in a period."""
        query = select(func.sum(CanonicalStakerRewardsDetail.reward_amount_native)).where(
            and_(
                CanonicalStakerRewardsDetail.chain_id == chain_id,
                CanonicalStakerRewardsDetail.period_id == period_id,
                CanonicalStakerRewardsDetail.staker_address.in_(wallet_addresses),
            )
        )

        if validator_key is not None:
            query = query.where(CanonicalStakerRewardsDetail.validator_key == validator_key)

        if revenue_component is not None:
            query = query.where(CanonicalStakerRewardsDetail.revenue_component == revenue_component)

        result = await self.session.execute(query)
        total = result.scalar_one_or_none()

        return float(total) if total is not None else 0.0
```

**Also Update**: `src/repositories/__init__.py` to export new repositories

---

### Services (src/core/services/)

**Estimated Time**: 2 hours

#### 1. partner_wallets.py

**Location**: Create `src/core/services/partner_wallets.py`

**Key Methods**:
- `create_wallet()` - Add single wallet with validation
- `bulk_upload_csv()` - Parse CSV, validate, bulk insert wallets
- `get_partner_wallets()` - List with pagination and filters
- `update_wallet()` - Modify wallet details
- `soft_delete_wallet()` - Deactivate wallet
- `validate_wallet_address()` - Format validation (base58 for Solana)
- `check_wallet_uniqueness()` - Verify wallet not already claimed

#### 2. Enhance commissions.py

**Location**: Update `src/core/services/commissions.py`

**New Methods**:
- `calculate_wallet_attributed_commission()` - Main attribution logic
- `is_wallet_staked_in_period()` - Validate wallet was staking
- `get_wallet_rewards_for_period()` - Sum rewards for wallets
- `create_wallet_commission_lines()` - Generate commission records with wallet_address

**Key Logic for Wallet Attribution**:
```python
async def calculate_wallet_attributed_commission(
    partner_id: UUID,
    period_ids: list[UUID],
    validator_key: Optional[str] = None,
) -> CommissionBreakdown:
    """Calculate commissions using wallet attribution method."""

    # 1. Get partner wallets
    wallets = await wallet_repo.get_by_partner(partner_id, is_active=True)

    # 2. For each period
    for period_id in period_ids:
        period = await period_repo.get_by_id(period_id)

        # 3. Filter wallets by introduced_date (retroactive support)
        eligible_wallets = [
            w for w in wallets
            if w.introduced_date <= period.start_time.date()
        ]

        # 4. Check staking status (lifecycle validation)
        for wallet in eligible_wallets:
            is_staked = await is_wallet_staked_in_period(
                wallet.wallet_address,
                wallet.chain_id,
                period_id,
                validator_key
            )

            if not is_staked:
                continue  # Skip if wallet not staking in this period

            # 5. Get staker rewards for this wallet
            rewards = await staker_rewards_repo.get_by_staker_and_period(
                chain_id=wallet.chain_id,
                period_id=period_id,
                validator_key=validator_key,
                staker_address=wallet.wallet_address
            )

            # 6. Calculate commission per component
            for reward in rewards:
                # Get applicable rule for this component
                rule = await get_active_rule_for_component(
                    agreement_id, reward.revenue_component
                )

                commission = reward.reward_amount_native * rule.commission_rate_bps / 10000

                # Create commission line with wallet_address
                await create_commission_line(
                    agreement_id=agreement_id,
                    partner_id=partner_id,
                    period_id=period_id,
                    validator_key=validator_key,
                    revenue_component=reward.revenue_component,
                    base_amount=reward.reward_amount_native,
                    commission_rate=rule.commission_rate_bps,
                    commission_amount=commission,
                    wallet_address=wallet.wallet_address,  # NEW: Track wallet
                )
```

---

### API Endpoints (src/api/routers/)

**Estimated Time**: 1.5 hours

Create new router: `src/api/routers/partner_wallets.py`

**Endpoints**:

1. `POST /api/v1/partners/{partner_id}/wallets` - Create single wallet
2. `POST /api/v1/partners/{partner_id}/wallets/bulk` - CSV bulk upload
3. `GET /api/v1/partners/{partner_id}/wallets` - List with pagination
4. `DELETE /api/v1/partners/{partner_id}/wallets/{wallet_id}` - Soft delete
5. `GET /api/v1/partners/{partner_id}/wallets/export` - Export CSV

**Also Enhance**:
- `src/api/routers/periods.py` - Add `GET /periods/by-date-range`
- `src/api/routers/commissions.py` - Update breakdown endpoint for wallet attribution

---

### Seed Data (scripts/seed_mvp_data.py)

**Estimated Time**: 30 minutes

**Add to Seed Script**:
- 50 partner wallets (25 per partner)
- 300 staker reward records (per staker-component detail)
- 150 stake event records (STAKE/UNSTAKE lifecycle)
- Set `wallet_attribution_enabled = true` for one agreement

---

## 🔑 Key Technical Learnings from Session

### PostgreSQL ENUM Handling in Alembic

**Problem**: Creating enum types can cause "duplicate object" errors if enum already exists from previous migrations or manual creation.

**Solution**: Use `postgresql.ENUM(..., create_type=False)` in column definition, then create enum explicitly with idempotent SQL:

```python
# In upgrade():
op.execute(
    "DO $$ BEGIN "
    "CREATE TYPE stake_event_type AS ENUM ('STAKE', 'UNSTAKE', 'RESTAKE'); "
    "EXCEPTION WHEN duplicate_object THEN NULL; "
    "END $$;"
)

# In column definition:
sa.Column(
    "event_type",
    postgresql.ENUM("STAKE", "UNSTAKE", "RESTAKE", name="stake_event_type", create_type=False),
    nullable=False,
)
```

This prevents SQLAlchemy from trying to create the enum type again during table creation.

---

## 📝 Next Session Checklist

### Before Starting
- [ ] Review this document completely
- [ ] Check database migration status: `./scripts/migrate.sh current`
- [ ] Verify migrations 1-2 are applied: `af2383dc7482`, `8ea71cd7ef5d`

### Session Tasks (Sequential Order)

**Phase 1: Complete Migrations (1 hour)**
- [ ] Create migration 3: canonical_staker_rewards_detail table
- [ ] Create migration 4: enhance agreements and commission_lines
- [ ] Run all migrations: `./scripts/migrate.sh upgrade`
- [ ] Verify schema: `./scripts/migrate.sh current`

**Phase 2: ORM Models (1.5 hours)**
- [ ] Add PartnerWallet model to computation.py
- [ ] Add CanonicalStakeEvent model to chains.py (with StakeEventType enum)
- [ ] Add CanonicalStakerRewardsDetail model to chains.py
- [ ] Update Partners, Chain, CanonicalPeriod relationships
- [ ] Enhance Agreements and PartnerCommissionLines models
- [ ] Update src/core/models/__init__.py exports
- [ ] Run: `poetry run mypy src/` to validate types

**Phase 3: Repositories (1 hour)**
- [ ] Create partner_wallets.py repository
- [ ] Create stake_events.py repository
- [ ] Create staker_rewards.py repository
- [ ] Update src/repositories/__init__.py exports
- [ ] Run: `poetry run mypy src/` to validate

**Phase 4: Services (2 hours)**
- [ ] Create partner_wallets.py service
- [ ] Enhance commissions.py service with wallet attribution
- [ ] Update src/core/services/__init__.py exports
- [ ] Run: `poetry run mypy src/` to validate

**Phase 5: API Endpoints (1.5 hours)**
- [ ] Create partner_wallets.py router
- [ ] Enhance periods.py router (date range endpoint)
- [ ] Enhance commissions.py router (wallet breakdown)
- [ ] Register routers in src/main.py
- [ ] Run: `poetry run mypy src/` to validate

**Phase 6: Seed Data (30 minutes)**
- [ ] Update scripts/seed_mvp_data.py with wallet test data
- [ ] Run: `poetry run python scripts/seed_mvp_data.py`
- [ ] Verify data: Check partner_wallets, stake_events, staker_rewards tables

**Phase 7: Quality Checks (30 minutes)**
- [ ] Run: `poetry run ruff check src/`
- [ ] Run: `poetry run black src/`
- [ ] Run: `poetry run pytest` (if tests exist)
- [ ] Manual API testing via http://localhost:8001/docs

**Phase 8: Documentation (30 minutes)**
- [ ] Update docs/ai-context/project-structure.md (add new files)
- [ ] Update docs/ai-context/HANDOFF.md (mark Issue #29 complete)
- [ ] Commit all changes with descriptive message
- [ ] Push to repository

### Total Estimated Time
**7-8 hours** to complete Issue #29 (Database & Backend Foundation)

---

## 🎯 Success Criteria

Issue #29 is complete when:
- ✅ All 4 database migrations applied successfully
- ✅ All ORM models created with proper relationships
- ✅ All repositories implement CRUD operations
- ✅ Wallet attribution logic implemented in commissions service
- ✅ Partner wallets API endpoints functional
- ✅ Seed data includes wallet test data
- ✅ All quality checks passing (mypy, ruff, black)
- ✅ Documentation updated

---

## 📚 Reference Documentation

**Business Requirements**: See HANDOFF.md section "Upcoming Work: Wallet Attribution System"

**Key Concepts**:
- Wallet exclusivity: One wallet → one partner (UNIQUE constraint)
- Retroactive support: introduced_date allows historical attribution
- Lifecycle validation: Only count rewards when wallet was actively staking
- Component granularity: Attribution works per revenue component (EXEC_FEES, MEV, REWARDS)

**Database Design Patterns**:
- NUMERIC(38,18) for all amounts
- UUID primary keys with uuid4 default
- Timestamp tracking: created_at, updated_at
- Data lineage: source_provider_id + source_payload_id
- Soft deletes: is_active flag where needed

---

**Document Version**: 1.0
**Last Updated**: 2025-11-03
**Next Review**: After Issue #29 completion
