"""Unit tests for staging layer models.

Tests cover:
- IngestionRun model creation and validation
- StagingPayload model creation and validation
- Relationships between staging models and chain registry
- Constraint validation and cascade deletes
"""

from datetime import UTC, datetime

import pytest
from core.models import (
    CanonicalPeriod,
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


class TestIngestionRunModel:
    """Tests for IngestionRun model."""

    async def test_create_ingestion_run(self, db_session: AsyncSession) -> None:
        """Test creating a valid ingestion run."""
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

        # Create ingestion run
        run = IngestionRun(
            chain_id="solana-mainnet",
            status=IngestionStatus.PENDING,
            records_fetched=100,
            records_staged=95,
            job_metadata={"provider_version": "1.0.0"},
        )
        db_session.add(run)
        await db_session.commit()

        # Verify ingestion run was created
        result = await db_session.execute(
            select(IngestionRun).where(IngestionRun.run_id == run.run_id)
        )
        saved_run = result.scalar_one()

        assert saved_run.chain_id == "solana-mainnet"
        assert saved_run.status == IngestionStatus.PENDING
        assert saved_run.records_fetched == 100
        assert saved_run.records_staged == 95
        assert saved_run.job_metadata == {"provider_version": "1.0.0"}
        assert saved_run.started_at is not None
        assert saved_run.completed_at is None
        assert saved_run.error_message is None
        assert saved_run.created_at is not None
        assert saved_run.updated_at is not None

    async def test_ingestion_run_with_period(self, db_session: AsyncSession) -> None:
        """Test ingestion run with canonical period reference."""
        # Create chain
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

        # Create period
        period = CanonicalPeriod(
            chain_id="solana-mainnet",
            period_identifier="123",
            period_start=datetime.now(UTC),
            period_end=datetime.now(UTC),
            is_finalized=False,
        )
        db_session.add(period)
        await db_session.flush()

        # Create ingestion run with period
        run = IngestionRun(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            status=IngestionStatus.RUNNING,
        )
        db_session.add(run)
        await db_session.commit()

        # Verify relationship
        result = await db_session.execute(
            select(IngestionRun).where(IngestionRun.run_id == run.run_id)
        )
        saved_run = result.scalar_one()
        assert saved_run.period_id == period.period_id
        assert saved_run.period.period_identifier == "123"

    async def test_ingestion_run_records_fetched_positive(self, db_session: AsyncSession) -> None:
        """Test ingestion run records_fetched must be non-negative."""
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

        run = IngestionRun(
            chain_id="solana-mainnet",
            status=IngestionStatus.PENDING,
            records_fetched=-1,  # Invalid negative value
        )
        db_session.add(run)

        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()

        assert "ck_ingestion_runs_records_fetched_positive" in str(exc_info.value)
        await db_session.rollback()

    async def test_ingestion_run_records_staged_positive(self, db_session: AsyncSession) -> None:
        """Test ingestion run records_staged must be non-negative."""
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

        run = IngestionRun(
            chain_id="solana-mainnet",
            status=IngestionStatus.PENDING,
            records_staged=-1,  # Invalid negative value
        )
        db_session.add(run)

        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()

        assert "ck_ingestion_runs_records_staged_positive" in str(exc_info.value)
        await db_session.rollback()

    async def test_ingestion_run_cascade_delete_with_chain(self, db_session: AsyncSession) -> None:
        """Test cascade delete when chain is deleted."""
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

        run = IngestionRun(
            chain_id="solana-mainnet",
            status=IngestionStatus.SUCCESS,
        )
        db_session.add(run)
        await db_session.commit()

        run_id = run.run_id

        # Delete chain should cascade delete ingestion run
        await db_session.delete(chain)
        await db_session.commit()

        # Verify ingestion run was deleted
        result = await db_session.execute(select(IngestionRun).where(IngestionRun.run_id == run_id))
        assert result.scalar_one_or_none() is None

    async def test_ingestion_run_status_values(self, db_session: AsyncSession) -> None:
        """Test all valid ingestion status values."""
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

        statuses = [
            IngestionStatus.PENDING,
            IngestionStatus.RUNNING,
            IngestionStatus.SUCCESS,
            IngestionStatus.FAILED,
            IngestionStatus.PARTIAL,
        ]

        for status in statuses:
            run = IngestionRun(
                chain_id="solana-mainnet",
                status=status,
            )
            db_session.add(run)
            await db_session.flush()

            result = await db_session.execute(
                select(IngestionRun).where(IngestionRun.run_id == run.run_id)
            )
            saved_run = result.scalar_one()
            assert saved_run.status == status

            await db_session.delete(saved_run)
            await db_session.flush()


class TestStagingPayloadModel:
    """Tests for StagingPayload model."""

    async def test_create_staging_payload(self, db_session: AsyncSession) -> None:
        """Test creating a valid staging payload."""
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

        # Create period
        period = CanonicalPeriod(
            chain_id="solana-mainnet",
            period_identifier="123",
            period_start=datetime.now(UTC),
            period_end=datetime.now(UTC),
            is_finalized=False,
        )
        db_session.add(period)
        await db_session.flush()

        # Create provider
        provider = Provider(
            provider_name="Solana RPC",
            provider_type="RPC",
            base_url="https://api.mainnet-beta.solana.com",
            is_enabled=True,
        )
        db_session.add(provider)
        await db_session.flush()

        # Create ingestion run
        run = IngestionRun(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            status=IngestionStatus.RUNNING,
        )
        db_session.add(run)
        await db_session.flush()

        # Create staging payload
        payload = StagingPayload(
            run_id=run.run_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            provider_id=provider.provider_id,
            data_type=DataType.FEES,
            response_hash="abc123",
            raw_payload={"fee": 5000, "transaction_count": 100},
        )
        db_session.add(payload)
        await db_session.commit()

        # Verify staging payload was created
        result = await db_session.execute(
            select(StagingPayload).where(StagingPayload.payload_id == payload.payload_id)
        )
        saved_payload = result.scalar_one()

        assert saved_payload.run_id == run.run_id
        assert saved_payload.chain_id == "solana-mainnet"
        assert saved_payload.period_id == period.period_id
        assert saved_payload.validator_key == "validator123"
        assert saved_payload.provider_id == provider.provider_id
        assert saved_payload.data_type == DataType.FEES
        assert saved_payload.response_hash == "abc123"
        assert saved_payload.raw_payload == {"fee": 5000, "transaction_count": 100}
        assert saved_payload.fetch_timestamp is not None
        assert saved_payload.created_at is not None

    async def test_staging_payload_relationships(self, db_session: AsyncSession) -> None:
        """Test staging payload relationships with chain, period, provider, and run."""
        # Create chain
        chain = Chain(
            chain_id="ethereum-mainnet",
            name="Ethereum Mainnet",
            period_type="BLOCK_WINDOW",
            native_unit="wei",
            native_decimals=18,
            finality_lag=32,
            is_active=True,
        )
        db_session.add(chain)
        await db_session.flush()

        # Create period
        period = CanonicalPeriod(
            chain_id="ethereum-mainnet",
            period_identifier="1000",
            period_start=datetime.now(UTC),
            period_end=datetime.now(UTC),
            is_finalized=False,
        )
        db_session.add(period)
        await db_session.flush()

        # Create provider
        provider = Provider(
            provider_name="Etherscan",
            provider_type="FEES",
            base_url="https://api.etherscan.io",
            is_enabled=True,
        )
        db_session.add(provider)
        await db_session.flush()

        # Create ingestion run
        run = IngestionRun(
            chain_id="ethereum-mainnet",
            period_id=period.period_id,
            status=IngestionStatus.RUNNING,
        )
        db_session.add(run)
        await db_session.flush()

        # Create staging payload
        payload = StagingPayload(
            run_id=run.run_id,
            chain_id="ethereum-mainnet",
            period_id=period.period_id,
            validator_key="0x123validator",
            provider_id=provider.provider_id,
            data_type=DataType.MEV,
            response_hash="xyz789",
            raw_payload={"mev_tips": 1000000000000000000},
        )
        db_session.add(payload)
        await db_session.commit()

        # Verify relationships
        result = await db_session.execute(
            select(StagingPayload).where(StagingPayload.payload_id == payload.payload_id)
        )
        saved_payload = result.scalar_one()

        assert saved_payload.chain.chain_id == "ethereum-mainnet"
        assert saved_payload.chain.name == "Ethereum Mainnet"
        assert saved_payload.period.period_identifier == "1000"
        assert saved_payload.provider.provider_name == "Etherscan"
        assert saved_payload.ingestion_run.status == IngestionStatus.RUNNING

    async def test_staging_payload_data_types(self, db_session: AsyncSession) -> None:
        """Test all valid data types for staging payload."""
        # Create chain
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

        # Create period
        period = CanonicalPeriod(
            chain_id="solana-mainnet",
            period_identifier="123",
            period_start=datetime.now(UTC),
            period_end=datetime.now(UTC),
            is_finalized=False,
        )
        db_session.add(period)
        await db_session.flush()

        # Create provider
        provider = Provider(
            provider_name="Solana RPC",
            provider_type="RPC",
            base_url="https://api.mainnet-beta.solana.com",
            is_enabled=True,
        )
        db_session.add(provider)
        await db_session.flush()

        # Create ingestion run
        run = IngestionRun(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            status=IngestionStatus.RUNNING,
        )
        db_session.add(run)
        await db_session.flush()

        data_types = [DataType.FEES, DataType.MEV, DataType.REWARDS, DataType.META]

        for data_type in data_types:
            payload = StagingPayload(
                run_id=run.run_id,
                chain_id="solana-mainnet",
                period_id=period.period_id,
                validator_key=f"validator_{data_type.value}",
                provider_id=provider.provider_id,
                data_type=data_type,
                response_hash=f"hash_{data_type.value}",
                raw_payload={"type": data_type.value},
            )
            db_session.add(payload)
            await db_session.flush()

            result = await db_session.execute(
                select(StagingPayload).where(StagingPayload.payload_id == payload.payload_id)
            )
            saved_payload = result.scalar_one()
            assert saved_payload.data_type == data_type

            await db_session.delete(saved_payload)
            await db_session.flush()

    async def test_staging_payload_cascade_delete_with_run(self, db_session: AsyncSession) -> None:
        """Test cascade delete when ingestion run is deleted."""
        # Create chain
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

        # Create period
        period = CanonicalPeriod(
            chain_id="solana-mainnet",
            period_identifier="123",
            period_start=datetime.now(UTC),
            period_end=datetime.now(UTC),
            is_finalized=False,
        )
        db_session.add(period)
        await db_session.flush()

        # Create provider
        provider = Provider(
            provider_name="Solana RPC",
            provider_type="RPC",
            base_url="https://api.mainnet-beta.solana.com",
            is_enabled=True,
        )
        db_session.add(provider)
        await db_session.flush()

        # Create ingestion run
        run = IngestionRun(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            status=IngestionStatus.SUCCESS,
        )
        db_session.add(run)
        await db_session.flush()

        # Create staging payload
        payload = StagingPayload(
            run_id=run.run_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            provider_id=provider.provider_id,
            data_type=DataType.REWARDS,
            response_hash="hash123",
            raw_payload={"rewards": 5000},
        )
        db_session.add(payload)
        await db_session.commit()

        payload_id = payload.payload_id

        # Delete ingestion run should cascade delete staging payload
        await db_session.delete(run)
        await db_session.commit()

        # Verify staging payload was deleted
        result = await db_session.execute(
            select(StagingPayload).where(StagingPayload.payload_id == payload_id)
        )
        assert result.scalar_one_or_none() is None

    async def test_staging_payload_cascade_delete_with_chain(
        self, db_session: AsyncSession
    ) -> None:
        """Test cascade delete when chain is deleted."""
        # Create chain
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

        # Create period
        period = CanonicalPeriod(
            chain_id="solana-mainnet",
            period_identifier="123",
            period_start=datetime.now(UTC),
            period_end=datetime.now(UTC),
            is_finalized=False,
        )
        db_session.add(period)
        await db_session.flush()

        # Create provider
        provider = Provider(
            provider_name="Solana RPC",
            provider_type="RPC",
            base_url="https://api.mainnet-beta.solana.com",
            is_enabled=True,
        )
        db_session.add(provider)
        await db_session.flush()

        # Create ingestion run
        run = IngestionRun(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            status=IngestionStatus.SUCCESS,
        )
        db_session.add(run)
        await db_session.flush()

        # Create staging payload
        payload = StagingPayload(
            run_id=run.run_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            provider_id=provider.provider_id,
            data_type=DataType.FEES,
            response_hash="hash456",
            raw_payload={"fees": 10000},
        )
        db_session.add(payload)
        await db_session.commit()

        payload_id = payload.payload_id

        # Delete chain should cascade delete everything
        await db_session.delete(chain)
        await db_session.commit()

        # Verify staging payload was deleted
        result = await db_session.execute(
            select(StagingPayload).where(StagingPayload.payload_id == payload_id)
        )
        assert result.scalar_one_or_none() is None
