"""Unit tests for canonical layer models.

Tests cover:
- CanonicalValidatorFees model creation and validation
- CanonicalValidatorMEV model creation and validation
- CanonicalStakeRewards model creation and validation
- CanonicalValidatorMeta model creation and validation
- NUMERIC(38,18) decimal precision
- Unique constraints and data integrity
- Relationships with chain, period, provider, and staging models
- Constraint validation and cascade deletes
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from core.models import (
    CanonicalPeriod,
    CanonicalStakeRewards,
    CanonicalValidatorFees,
    CanonicalValidatorMeta,
    CanonicalValidatorMEV,
    Chain,
    DataType,
    IngestionRun,
    IngestionStatus,
    Provider,
    StagingPayload,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class TestCanonicalValidatorFeesModel:
    """Tests for CanonicalValidatorFees model."""

    async def test_create_canonical_fees(self, db_session: AsyncSession) -> None:
        """Test creating a valid canonical fees record."""
        # Create required chain
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True,
        )
        db_session.add(chain)
        await db_session.flush()

        # Create canonical period
        period = CanonicalPeriod(
            chain_id="solana-mainnet",
            period_identifier="850",
            period_start=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            period_end=datetime(2024, 1, 3, 0, 0, 0, tzinfo=UTC),
            is_finalized=True,
        )
        db_session.add(period)
        await db_session.flush()

        # Create provider
        provider = Provider(
            provider_name="solanabeach",
            provider_type="FEES",
            is_enabled=True,
        )
        db_session.add(provider)
        await db_session.flush()

        # Create staging payload
        run = IngestionRun(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            status=IngestionStatus.SUCCESS,
        )
        db_session.add(run)
        await db_session.flush()

        staging = StagingPayload(
            run_id=run.run_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            provider_id=provider.provider_id,
            data_type=DataType.FEES,
            response_hash="abc123",
            raw_payload={"fees": 1000000},
        )
        db_session.add(staging)
        await db_session.flush()

        # Create canonical fees
        fees = CanonicalValidatorFees(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            total_fees_native=Decimal("1500000.500000000000000000"),
            fee_count=42,
            source_provider_id=provider.provider_id,
            source_payload_id=staging.payload_id,
        )
        db_session.add(fees)
        await db_session.commit()

        # Verify canonical fees was created
        result = await db_session.execute(
            select(CanonicalValidatorFees).where(CanonicalValidatorFees.fee_id == fees.fee_id)
        )
        saved_fees = result.scalar_one()

        assert saved_fees.chain_id == "solana-mainnet"
        assert saved_fees.period_id == period.period_id
        assert saved_fees.validator_key == "validator123"
        assert Decimal(str(saved_fees.total_fees_native)) == Decimal("1500000.500000000000000000")
        assert saved_fees.fee_count == 42
        assert saved_fees.source_provider_id == provider.provider_id
        assert saved_fees.source_payload_id == staging.payload_id
        assert saved_fees.normalized_at is not None
        assert saved_fees.created_at is not None
        assert saved_fees.updated_at is not None

    async def test_canonical_fees_unique_constraint(self, db_session: AsyncSession) -> None:
        """Test unique constraint on (chain_id, period_id, validator_key)."""
        # Create required dependencies
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True,
        )
        db_session.add(chain)
        await db_session.flush()

        period = CanonicalPeriod(
            chain_id="solana-mainnet",
            period_identifier="850",
            period_start=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            period_end=datetime(2024, 1, 3, 0, 0, 0, tzinfo=UTC),
            is_finalized=True,
        )
        db_session.add(period)
        await db_session.flush()

        provider = Provider(
            provider_name="solanabeach",
            provider_type="FEES",
            is_enabled=True,
        )
        db_session.add(provider)
        await db_session.flush()

        run = IngestionRun(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            status=IngestionStatus.SUCCESS,
        )
        db_session.add(run)
        await db_session.flush()

        staging1 = StagingPayload(
            run_id=run.run_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            provider_id=provider.provider_id,
            data_type=DataType.FEES,
            response_hash="abc123",
            raw_payload={"fees": 1000000},
        )
        db_session.add(staging1)
        await db_session.flush()

        staging2 = StagingPayload(
            run_id=run.run_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            provider_id=provider.provider_id,
            data_type=DataType.FEES,
            response_hash="def456",
            raw_payload={"fees": 2000000},
        )
        db_session.add(staging2)
        await db_session.flush()

        # Create first canonical fees record
        fees1 = CanonicalValidatorFees(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            total_fees_native=Decimal("1500000.0"),
            fee_count=42,
            source_provider_id=provider.provider_id,
            source_payload_id=staging1.payload_id,
        )
        db_session.add(fees1)
        await db_session.commit()

        # Try to create duplicate - should fail
        fees2 = CanonicalValidatorFees(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            total_fees_native=Decimal("2500000.0"),
            fee_count=50,
            source_provider_id=provider.provider_id,
            source_payload_id=staging2.payload_id,
        )
        db_session.add(fees2)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_canonical_fees_check_constraints(self, db_session: AsyncSession) -> None:
        """Test check constraints for positive values."""
        # Create required dependencies
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True,
        )
        db_session.add(chain)
        await db_session.flush()

        period = CanonicalPeriod(
            chain_id="solana-mainnet",
            period_identifier="850",
            period_start=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            period_end=datetime(2024, 1, 3, 0, 0, 0, tzinfo=UTC),
            is_finalized=True,
        )
        db_session.add(period)
        await db_session.flush()

        provider = Provider(
            provider_name="solanabeach",
            provider_type="FEES",
            is_enabled=True,
        )
        db_session.add(provider)
        await db_session.flush()

        run = IngestionRun(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            status=IngestionStatus.SUCCESS,
        )
        db_session.add(run)
        await db_session.flush()

        staging = StagingPayload(
            run_id=run.run_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            provider_id=provider.provider_id,
            data_type=DataType.FEES,
            response_hash="abc123",
            raw_payload={"fees": 1000000},
        )
        db_session.add(staging)
        await db_session.flush()

        # Try to create with negative total_fees_native
        fees = CanonicalValidatorFees(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            total_fees_native=Decimal("-1000.0"),
            fee_count=42,
            source_provider_id=provider.provider_id,
            source_payload_id=staging.payload_id,
        )
        db_session.add(fees)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_canonical_fees_relationships(self, db_session: AsyncSession) -> None:
        """Test relationships with chain, period, provider, and staging."""
        # Create full dependency chain
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True,
        )
        db_session.add(chain)
        await db_session.flush()

        period = CanonicalPeriod(
            chain_id="solana-mainnet",
            period_identifier="850",
            period_start=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            period_end=datetime(2024, 1, 3, 0, 0, 0, tzinfo=UTC),
            is_finalized=True,
        )
        db_session.add(period)
        await db_session.flush()

        provider = Provider(
            provider_name="solanabeach",
            provider_type="FEES",
            is_enabled=True,
        )
        db_session.add(provider)
        await db_session.flush()

        run = IngestionRun(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            status=IngestionStatus.SUCCESS,
        )
        db_session.add(run)
        await db_session.flush()

        staging = StagingPayload(
            run_id=run.run_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            provider_id=provider.provider_id,
            data_type=DataType.FEES,
            response_hash="abc123",
            raw_payload={"fees": 1000000},
        )
        db_session.add(staging)
        await db_session.flush()

        fees = CanonicalValidatorFees(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            total_fees_native=Decimal("1500000.0"),
            fee_count=42,
            source_provider_id=provider.provider_id,
            source_payload_id=staging.payload_id,
        )
        db_session.add(fees)
        await db_session.commit()

        # Verify relationships
        result = await db_session.execute(
            select(CanonicalValidatorFees).where(CanonicalValidatorFees.fee_id == fees.fee_id)
        )
        saved_fees = result.scalar_one()

        assert saved_fees.chain.chain_id == "solana-mainnet"
        assert saved_fees.period.period_id == period.period_id
        assert saved_fees.source_provider.provider_id == provider.provider_id
        assert saved_fees.source_payload.payload_id == staging.payload_id


class TestCanonicalValidatorMEVModel:
    """Tests for CanonicalValidatorMEV model."""

    async def test_create_canonical_mev(self, db_session: AsyncSession) -> None:
        """Test creating a valid canonical MEV record."""
        # Create required dependencies
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True,
        )
        db_session.add(chain)
        await db_session.flush()

        period = CanonicalPeriod(
            chain_id="solana-mainnet",
            period_identifier="850",
            period_start=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            period_end=datetime(2024, 1, 3, 0, 0, 0, tzinfo=UTC),
            is_finalized=True,
        )
        db_session.add(period)
        await db_session.flush()

        provider = Provider(
            provider_name="jito",
            provider_type="MEV",
            is_enabled=True,
        )
        db_session.add(provider)
        await db_session.flush()

        run = IngestionRun(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            status=IngestionStatus.SUCCESS,
        )
        db_session.add(run)
        await db_session.flush()

        staging = StagingPayload(
            run_id=run.run_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            provider_id=provider.provider_id,
            data_type=DataType.MEV,
            response_hash="xyz789",
            raw_payload={"mev_tips": 500000},
        )
        db_session.add(staging)
        await db_session.flush()

        # Create canonical MEV
        mev = CanonicalValidatorMEV(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            total_mev_native=Decimal("750000.250000000000000000"),
            tip_count=15,
            source_provider_id=provider.provider_id,
            source_payload_id=staging.payload_id,
        )
        db_session.add(mev)
        await db_session.commit()

        # Verify canonical MEV was created
        result = await db_session.execute(
            select(CanonicalValidatorMEV).where(CanonicalValidatorMEV.mev_id == mev.mev_id)
        )
        saved_mev = result.scalar_one()

        assert saved_mev.chain_id == "solana-mainnet"
        assert saved_mev.period_id == period.period_id
        assert saved_mev.validator_key == "validator123"
        assert Decimal(str(saved_mev.total_mev_native)) == Decimal("750000.250000000000000000")
        assert saved_mev.tip_count == 15
        assert saved_mev.source_provider_id == provider.provider_id
        assert saved_mev.source_payload_id == staging.payload_id

    async def test_canonical_mev_unique_constraint(self, db_session: AsyncSession) -> None:
        """Test unique constraint on (chain_id, period_id, validator_key)."""
        # Create required dependencies
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True,
        )
        db_session.add(chain)
        await db_session.flush()

        period = CanonicalPeriod(
            chain_id="solana-mainnet",
            period_identifier="850",
            period_start=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            period_end=datetime(2024, 1, 3, 0, 0, 0, tzinfo=UTC),
            is_finalized=True,
        )
        db_session.add(period)
        await db_session.flush()

        provider = Provider(
            provider_name="jito",
            provider_type="MEV",
            is_enabled=True,
        )
        db_session.add(provider)
        await db_session.flush()

        run = IngestionRun(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            status=IngestionStatus.SUCCESS,
        )
        db_session.add(run)
        await db_session.flush()

        staging1 = StagingPayload(
            run_id=run.run_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            provider_id=provider.provider_id,
            data_type=DataType.MEV,
            response_hash="xyz789",
            raw_payload={"mev_tips": 500000},
        )
        db_session.add(staging1)
        await db_session.flush()

        staging2 = StagingPayload(
            run_id=run.run_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            provider_id=provider.provider_id,
            data_type=DataType.MEV,
            response_hash="uvw456",
            raw_payload={"mev_tips": 600000},
        )
        db_session.add(staging2)
        await db_session.flush()

        # Create first canonical MEV record
        mev1 = CanonicalValidatorMEV(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            total_mev_native=Decimal("750000.0"),
            tip_count=15,
            source_provider_id=provider.provider_id,
            source_payload_id=staging1.payload_id,
        )
        db_session.add(mev1)
        await db_session.commit()

        # Try to create duplicate - should fail
        mev2 = CanonicalValidatorMEV(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            total_mev_native=Decimal("850000.0"),
            tip_count=20,
            source_provider_id=provider.provider_id,
            source_payload_id=staging2.payload_id,
        )
        db_session.add(mev2)

        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestCanonicalStakeRewardsModel:
    """Tests for CanonicalStakeRewards model."""

    async def test_create_canonical_rewards_aggregated(self, db_session: AsyncSession) -> None:
        """Test creating aggregated canonical rewards (no staker_address)."""
        # Create required dependencies
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True,
        )
        db_session.add(chain)
        await db_session.flush()

        period = CanonicalPeriod(
            chain_id="solana-mainnet",
            period_identifier="850",
            period_start=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            period_end=datetime(2024, 1, 3, 0, 0, 0, tzinfo=UTC),
            is_finalized=True,
        )
        db_session.add(period)
        await db_session.flush()

        provider = Provider(
            provider_name="solanabeach",
            provider_type="REWARDS",
            is_enabled=True,
        )
        db_session.add(provider)
        await db_session.flush()

        run = IngestionRun(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            status=IngestionStatus.SUCCESS,
        )
        db_session.add(run)
        await db_session.flush()

        staging = StagingPayload(
            run_id=run.run_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            provider_id=provider.provider_id,
            data_type=DataType.REWARDS,
            response_hash="reward123",
            raw_payload={"rewards": 2000000},
        )
        db_session.add(staging)
        await db_session.flush()

        # Create canonical rewards (aggregated)
        rewards = CanonicalStakeRewards(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            staker_address=None,  # Aggregated
            rewards_native=Decimal("2500000.123456789012345678"),
            commission_native=Decimal("125000.012345678901234567"),
            source_provider_id=provider.provider_id,
            source_payload_id=staging.payload_id,
        )
        db_session.add(rewards)
        await db_session.commit()

        # Verify canonical rewards was created
        result = await db_session.execute(
            select(CanonicalStakeRewards).where(
                CanonicalStakeRewards.reward_id == rewards.reward_id
            )
        )
        saved_rewards = result.scalar_one()

        assert saved_rewards.chain_id == "solana-mainnet"
        assert saved_rewards.period_id == period.period_id
        assert saved_rewards.validator_key == "validator123"
        assert saved_rewards.staker_address is None
        assert Decimal(str(saved_rewards.rewards_native)) == Decimal("2500000.123456789012345678")
        assert Decimal(str(saved_rewards.commission_native)) == Decimal("125000.012345678901234567")

    async def test_create_canonical_rewards_per_staker(self, db_session: AsyncSession) -> None:
        """Test creating per-staker canonical rewards."""
        # Create required dependencies
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True,
        )
        db_session.add(chain)
        await db_session.flush()

        period = CanonicalPeriod(
            chain_id="solana-mainnet",
            period_identifier="850",
            period_start=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            period_end=datetime(2024, 1, 3, 0, 0, 0, tzinfo=UTC),
            is_finalized=True,
        )
        db_session.add(period)
        await db_session.flush()

        provider = Provider(
            provider_name="solanabeach",
            provider_type="REWARDS",
            is_enabled=True,
        )
        db_session.add(provider)
        await db_session.flush()

        run = IngestionRun(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            status=IngestionStatus.SUCCESS,
        )
        db_session.add(run)
        await db_session.flush()

        staging = StagingPayload(
            run_id=run.run_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            provider_id=provider.provider_id,
            data_type=DataType.REWARDS,
            response_hash="reward123",
            raw_payload={"rewards": 2000000},
        )
        db_session.add(staging)
        await db_session.flush()

        # Create canonical rewards (per-staker)
        rewards = CanonicalStakeRewards(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            staker_address="staker_address_xyz",
            rewards_native=Decimal("50000.0"),
            commission_native=Decimal("2500.0"),
            source_provider_id=provider.provider_id,
            source_payload_id=staging.payload_id,
        )
        db_session.add(rewards)
        await db_session.commit()

        # Verify canonical rewards was created
        result = await db_session.execute(
            select(CanonicalStakeRewards).where(
                CanonicalStakeRewards.reward_id == rewards.reward_id
            )
        )
        saved_rewards = result.scalar_one()

        assert saved_rewards.staker_address == "staker_address_xyz"
        assert Decimal(str(saved_rewards.rewards_native)) == Decimal("50000.0")
        assert Decimal(str(saved_rewards.commission_native)) == Decimal("2500.0")


class TestCanonicalValidatorMetaModel:
    """Tests for CanonicalValidatorMeta model."""

    async def test_create_canonical_meta(self, db_session: AsyncSession) -> None:
        """Test creating a valid canonical meta record."""
        # Create required dependencies
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True,
        )
        db_session.add(chain)
        await db_session.flush()

        period = CanonicalPeriod(
            chain_id="solana-mainnet",
            period_identifier="850",
            period_start=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            period_end=datetime(2024, 1, 3, 0, 0, 0, tzinfo=UTC),
            is_finalized=True,
        )
        db_session.add(period)
        await db_session.flush()

        provider = Provider(
            provider_name="solanabeach",
            provider_type="META",
            is_enabled=True,
        )
        db_session.add(provider)
        await db_session.flush()

        run = IngestionRun(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            status=IngestionStatus.SUCCESS,
        )
        db_session.add(run)
        await db_session.flush()

        staging = StagingPayload(
            run_id=run.run_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            provider_id=provider.provider_id,
            data_type=DataType.META,
            response_hash="meta123",
            raw_payload={"commission": 500, "mev_enabled": True},
        )
        db_session.add(staging)
        await db_session.flush()

        # Create canonical meta
        meta = CanonicalValidatorMeta(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            commission_rate_bps=500,  # 5%
            is_mev_enabled=True,
            total_stake_native=Decimal("10000000.500000000000000000"),
            active_stake_native=Decimal("9500000.250000000000000000"),
            delegator_count=150,
            uptime_percentage=Decimal("99.95"),
            source_provider_id=provider.provider_id,
            source_payload_id=staging.payload_id,
        )
        db_session.add(meta)
        await db_session.commit()

        # Verify canonical meta was created
        result = await db_session.execute(
            select(CanonicalValidatorMeta).where(CanonicalValidatorMeta.meta_id == meta.meta_id)
        )
        saved_meta = result.scalar_one()

        assert saved_meta.chain_id == "solana-mainnet"
        assert saved_meta.period_id == period.period_id
        assert saved_meta.validator_key == "validator123"
        assert saved_meta.commission_rate_bps == 500
        assert saved_meta.is_mev_enabled is True
        assert Decimal(str(saved_meta.total_stake_native)) == Decimal("10000000.500000000000000000")
        assert Decimal(str(saved_meta.active_stake_native)) == Decimal("9500000.250000000000000000")
        assert saved_meta.delegator_count == 150
        assert Decimal(str(saved_meta.uptime_percentage)) == Decimal("99.95")

    async def test_canonical_meta_check_constraints(self, db_session: AsyncSession) -> None:
        """Test check constraints for valid ranges."""
        # Create required dependencies
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True,
        )
        db_session.add(chain)
        await db_session.flush()

        period = CanonicalPeriod(
            chain_id="solana-mainnet",
            period_identifier="850",
            period_start=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            period_end=datetime(2024, 1, 3, 0, 0, 0, tzinfo=UTC),
            is_finalized=True,
        )
        db_session.add(period)
        await db_session.flush()

        provider = Provider(
            provider_name="solanabeach",
            provider_type="META",
            is_enabled=True,
        )
        db_session.add(provider)
        await db_session.flush()

        run = IngestionRun(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            status=IngestionStatus.SUCCESS,
        )
        db_session.add(run)
        await db_session.flush()

        staging = StagingPayload(
            run_id=run.run_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            provider_id=provider.provider_id,
            data_type=DataType.META,
            response_hash="meta123",
            raw_payload={"commission": 500},
        )
        db_session.add(staging)
        await db_session.flush()

        # Try to create with invalid commission_rate_bps (>10000)
        meta = CanonicalValidatorMeta(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            commission_rate_bps=15000,  # Invalid: > 10000 (100%)
            is_mev_enabled=False,
            total_stake_native=Decimal("10000000.0"),
            source_provider_id=provider.provider_id,
            source_payload_id=staging.payload_id,
        )
        db_session.add(meta)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_canonical_meta_unique_constraint(self, db_session: AsyncSession) -> None:
        """Test unique constraint on (chain_id, period_id, validator_key)."""
        # Create required dependencies
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True,
        )
        db_session.add(chain)
        await db_session.flush()

        period = CanonicalPeriod(
            chain_id="solana-mainnet",
            period_identifier="850",
            period_start=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            period_end=datetime(2024, 1, 3, 0, 0, 0, tzinfo=UTC),
            is_finalized=True,
        )
        db_session.add(period)
        await db_session.flush()

        provider = Provider(
            provider_name="solanabeach",
            provider_type="META",
            is_enabled=True,
        )
        db_session.add(provider)
        await db_session.flush()

        run = IngestionRun(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            status=IngestionStatus.SUCCESS,
        )
        db_session.add(run)
        await db_session.flush()

        staging1 = StagingPayload(
            run_id=run.run_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            provider_id=provider.provider_id,
            data_type=DataType.META,
            response_hash="meta123",
            raw_payload={"commission": 500},
        )
        db_session.add(staging1)
        await db_session.flush()

        staging2 = StagingPayload(
            run_id=run.run_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            provider_id=provider.provider_id,
            data_type=DataType.META,
            response_hash="meta456",
            raw_payload={"commission": 600},
        )
        db_session.add(staging2)
        await db_session.flush()

        # Create first canonical meta record
        meta1 = CanonicalValidatorMeta(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            commission_rate_bps=500,
            is_mev_enabled=True,
            total_stake_native=Decimal("10000000.0"),
            source_provider_id=provider.provider_id,
            source_payload_id=staging1.payload_id,
        )
        db_session.add(meta1)
        await db_session.commit()

        # Try to create duplicate - should fail
        meta2 = CanonicalValidatorMeta(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            commission_rate_bps=600,
            is_mev_enabled=False,
            total_stake_native=Decimal("12000000.0"),
            source_provider_id=provider.provider_id,
            source_payload_id=staging2.payload_id,
        )
        db_session.add(meta2)

        with pytest.raises(IntegrityError):
            await db_session.commit()
