"""Unit tests for chain registry and configuration models.

Tests cover:
- Chain model creation and validation
- Provider model creation and validation
- ChainProviderMapping model and relationships
- CanonicalPeriod model and finalization tracking
- CanonicalValidatorIdentity model and chain-specific fields
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import (
    CanonicalPeriod,
    CanonicalValidatorIdentity,
    Chain,
    ChainProviderMapping,
    Provider,
)


class TestChainModel:
    """Tests for Chain model."""

    async def test_create_chain(self, db_session: AsyncSession) -> None:
        """Test creating a valid chain."""
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True
        )
        db_session.add(chain)
        await db_session.commit()

        # Verify chain was created
        result = await db_session.execute(
            select(Chain).where(Chain.chain_id == "solana-mainnet")
        )
        saved_chain = result.scalar_one()

        assert saved_chain.chain_id == "solana-mainnet"
        assert saved_chain.name == "Solana Mainnet"
        assert saved_chain.period_type == "EPOCH"
        assert saved_chain.native_unit == "lamports"
        assert saved_chain.native_decimals == 9
        assert saved_chain.finality_lag == 2
        assert saved_chain.is_active is True
        assert saved_chain.created_at is not None
        assert saved_chain.updated_at is not None

    async def test_chain_period_type_constraint(self, db_session: AsyncSession) -> None:
        """Test chain period_type check constraint."""
        chain = Chain(
            chain_id="invalid-chain",
            name="Invalid Chain",
            period_type="INVALID_TYPE",  # Invalid period type
            native_unit="wei",
            native_decimals=18,
            finality_lag=1,
            is_active=True
        )
        db_session.add(chain)

        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()

        assert "ck_chains_period_type" in str(exc_info.value)
        await db_session.rollback()

    async def test_chain_native_decimals_positive(self, db_session: AsyncSession) -> None:
        """Test chain native_decimals must be non-negative."""
        chain = Chain(
            chain_id="invalid-chain",
            name="Invalid Chain",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=-1,  # Invalid negative decimals
            finality_lag=1,
            is_active=True
        )
        db_session.add(chain)

        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()

        assert "ck_chains_native_decimals_positive" in str(exc_info.value)
        await db_session.rollback()

    async def test_chain_finality_lag_positive(self, db_session: AsyncSession) -> None:
        """Test chain finality_lag must be non-negative."""
        chain = Chain(
            chain_id="invalid-chain",
            name="Invalid Chain",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=-1,  # Invalid negative lag
            is_active=True
        )
        db_session.add(chain)

        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()

        assert "ck_chains_finality_lag_positive" in str(exc_info.value)
        await db_session.rollback()

    async def test_chain_to_dict(self, db_session: AsyncSession) -> None:
        """Test chain to_dict method."""
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True
        )

        chain_dict = chain.to_dict()

        assert chain_dict["chain_id"] == "solana-mainnet"
        assert chain_dict["name"] == "Solana Mainnet"
        assert chain_dict["period_type"] == "EPOCH"
        assert "created_at" in chain_dict
        assert "updated_at" in chain_dict

    async def test_chain_repr(self, db_session: AsyncSession) -> None:
        """Test chain __repr__ method."""
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True
        )

        repr_str = repr(chain)
        assert "Chain" in repr_str
        assert "solana-mainnet" in repr_str


class TestProviderModel:
    """Tests for Provider model."""

    async def test_create_provider(self, db_session: AsyncSession) -> None:
        """Test creating a valid provider."""
        provider = Provider(
            provider_name="solanabeach",
            provider_type="FEES",
            base_url="https://api.solanabeach.io",
            api_version="v1",
            is_enabled=True,
            rate_limit_per_minute=60,
            timeout_seconds=30
        )
        db_session.add(provider)
        await db_session.commit()

        # Verify provider was created
        result = await db_session.execute(
            select(Provider).where(Provider.provider_name == "solanabeach")
        )
        saved_provider = result.scalar_one()

        assert saved_provider.provider_name == "solanabeach"
        assert saved_provider.provider_type == "FEES"
        assert saved_provider.base_url == "https://api.solanabeach.io"
        assert saved_provider.api_version == "v1"
        assert saved_provider.is_enabled is True
        assert saved_provider.rate_limit_per_minute == 60
        assert saved_provider.timeout_seconds == 30
        assert saved_provider.created_at is not None
        assert saved_provider.updated_at is not None

    async def test_provider_type_constraint(self, db_session: AsyncSession) -> None:
        """Test provider provider_type check constraint."""
        provider = Provider(
            provider_name="invalid-provider",
            provider_type="INVALID_TYPE",  # Invalid provider type
            is_enabled=True
        )
        db_session.add(provider)

        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()

        assert "ck_providers_type" in str(exc_info.value)
        await db_session.rollback()

    async def test_provider_unique_name(self, db_session: AsyncSession) -> None:
        """Test provider name must be unique."""
        provider1 = Provider(
            provider_name="solanabeach",
            provider_type="FEES",
            is_enabled=True
        )
        db_session.add(provider1)
        await db_session.commit()

        # Try to create another provider with same name
        provider2 = Provider(
            provider_name="solanabeach",  # Duplicate name
            provider_type="MEV",
            is_enabled=True
        )
        db_session.add(provider2)

        with pytest.raises(IntegrityError):
            await db_session.commit()

        await db_session.rollback()

    async def test_provider_optional_fields(self, db_session: AsyncSession) -> None:
        """Test provider with optional fields as None."""
        provider = Provider(
            provider_name="minimal-provider",
            provider_type="RPC",
            base_url=None,
            api_version=None,
            is_enabled=True,
            rate_limit_per_minute=None
        )
        db_session.add(provider)
        await db_session.commit()

        result = await db_session.execute(
            select(Provider).where(Provider.provider_name == "minimal-provider")
        )
        saved_provider = result.scalar_one()

        assert saved_provider.base_url is None
        assert saved_provider.api_version is None
        assert saved_provider.rate_limit_per_minute is None


class TestChainProviderMapping:
    """Tests for ChainProviderMapping model."""

    async def test_create_mapping(self, db_session: AsyncSession) -> None:
        """Test creating a valid chain-provider mapping."""
        # Create chain
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True
        )
        db_session.add(chain)

        # Create provider
        provider = Provider(
            provider_name="solanabeach",
            provider_type="FEES",
            is_enabled=True
        )
        db_session.add(provider)
        await db_session.commit()

        # Create mapping
        mapping = ChainProviderMapping(
            chain_id=chain.chain_id,
            provider_id=provider.provider_id,
            provider_role="FEES",
            priority=1,
            is_active=True
        )
        db_session.add(mapping)
        await db_session.commit()

        # Verify mapping was created
        result = await db_session.execute(
            select(ChainProviderMapping).where(
                ChainProviderMapping.chain_id == "solana-mainnet"
            )
        )
        saved_mapping = result.scalar_one()

        assert saved_mapping.chain_id == "solana-mainnet"
        assert saved_mapping.provider_id == provider.provider_id
        assert saved_mapping.provider_role == "FEES"
        assert saved_mapping.priority == 1
        assert saved_mapping.is_active is True

    async def test_mapping_relationships(self, db_session: AsyncSession) -> None:
        """Test chain-provider mapping relationships."""
        # Create chain
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True
        )
        db_session.add(chain)

        # Create provider
        provider = Provider(
            provider_name="solanabeach",
            provider_type="FEES",
            is_enabled=True
        )
        db_session.add(provider)
        await db_session.commit()

        # Create mapping
        mapping = ChainProviderMapping(
            chain_id=chain.chain_id,
            provider_id=provider.provider_id,
            provider_role="FEES",
            priority=1,
            is_active=True
        )
        db_session.add(mapping)
        await db_session.commit()

        # Verify relationships
        result = await db_session.execute(
            select(ChainProviderMapping).where(
                ChainProviderMapping.chain_id == "solana-mainnet"
            )
        )
        saved_mapping = result.scalar_one()

        assert saved_mapping.chain.name == "Solana Mainnet"
        assert saved_mapping.provider.provider_name == "solanabeach"

    async def test_mapping_unique_constraint(self, db_session: AsyncSession) -> None:
        """Test chain-provider mapping unique constraint on (chain_id, provider_role, priority)."""
        # Create chain and provider
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True
        )
        provider = Provider(
            provider_name="solanabeach",
            provider_type="FEES",
            is_enabled=True
        )
        db_session.add_all([chain, provider])
        await db_session.commit()

        # Create first mapping
        mapping1 = ChainProviderMapping(
            chain_id=chain.chain_id,
            provider_id=provider.provider_id,
            provider_role="FEES",
            priority=1,
            is_active=True
        )
        db_session.add(mapping1)
        await db_session.commit()

        # Try to create duplicate mapping
        mapping2 = ChainProviderMapping(
            chain_id=chain.chain_id,
            provider_id=provider.provider_id,
            provider_role="FEES",  # Same role
            priority=1,  # Same priority
            is_active=True
        )
        db_session.add(mapping2)

        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()

        assert "uq_chain_provider_role_priority" in str(exc_info.value)
        await db_session.rollback()

    async def test_mapping_cascade_delete(self, db_session: AsyncSession) -> None:
        """Test cascade delete when chain is deleted."""
        # Create chain and provider
        chain = Chain(
            chain_id="test-chain",
            name="Test Chain",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=1,
            is_active=True
        )
        provider = Provider(
            provider_name="test-provider",
            provider_type="FEES",
            is_enabled=True
        )
        db_session.add_all([chain, provider])
        await db_session.commit()

        # Create mapping
        mapping = ChainProviderMapping(
            chain_id=chain.chain_id,
            provider_id=provider.provider_id,
            provider_role="FEES",
            priority=1,
            is_active=True
        )
        db_session.add(mapping)
        await db_session.commit()

        # Delete chain
        await db_session.delete(chain)
        await db_session.commit()

        # Verify mapping was also deleted
        result = await db_session.execute(
            select(ChainProviderMapping).where(
                ChainProviderMapping.chain_id == "test-chain"
            )
        )
        assert result.scalar_one_or_none() is None


class TestCanonicalPeriod:
    """Tests for CanonicalPeriod model."""

    async def test_create_period(self, db_session: AsyncSession) -> None:
        """Test creating a valid period."""
        # Create chain
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True
        )
        db_session.add(chain)
        await db_session.commit()

        # Create period
        period = CanonicalPeriod(
            chain_id=chain.chain_id,
            period_identifier="850",
            period_start=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            period_end=datetime(2024, 1, 3, 0, 0, 0, tzinfo=timezone.utc),
            is_finalized=False
        )
        db_session.add(period)
        await db_session.commit()

        # Verify period was created
        result = await db_session.execute(
            select(CanonicalPeriod).where(
                CanonicalPeriod.period_identifier == "850"
            )
        )
        saved_period = result.scalar_one()

        assert saved_period.chain_id == "solana-mainnet"
        assert saved_period.period_identifier == "850"
        assert saved_period.is_finalized is False
        assert saved_period.finalized_at is None

    async def test_period_finalization(self, db_session: AsyncSession) -> None:
        """Test period finalization tracking."""
        # Create chain
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True
        )
        db_session.add(chain)
        await db_session.commit()

        # Create period
        period = CanonicalPeriod(
            chain_id=chain.chain_id,
            period_identifier="850",
            period_start=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            period_end=datetime(2024, 1, 3, 0, 0, 0, tzinfo=timezone.utc),
            is_finalized=False
        )
        db_session.add(period)
        await db_session.commit()

        # Finalize period
        period.is_finalized = True
        period.finalized_at = datetime.now(timezone.utc)
        await db_session.commit()

        # Verify finalization
        result = await db_session.execute(
            select(CanonicalPeriod).where(
                CanonicalPeriod.period_identifier == "850"
            )
        )
        saved_period = result.scalar_one()

        assert saved_period.is_finalized is True
        assert saved_period.finalized_at is not None

    async def test_period_unique_constraint(self, db_session: AsyncSession) -> None:
        """Test period unique constraint on (chain_id, period_identifier)."""
        # Create chain
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True
        )
        db_session.add(chain)
        await db_session.commit()

        # Create first period
        period1 = CanonicalPeriod(
            chain_id=chain.chain_id,
            period_identifier="850",
            period_start=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            period_end=datetime(2024, 1, 3, 0, 0, 0, tzinfo=timezone.utc),
            is_finalized=False
        )
        db_session.add(period1)
        await db_session.commit()

        # Try to create duplicate period
        period2 = CanonicalPeriod(
            chain_id=chain.chain_id,
            period_identifier="850",  # Duplicate identifier
            period_start=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            period_end=datetime(2024, 1, 3, 0, 0, 0, tzinfo=timezone.utc),
            is_finalized=False
        )
        db_session.add(period2)

        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()

        assert "uq_canonical_periods_chain_period" in str(exc_info.value)
        await db_session.rollback()


class TestCanonicalValidatorIdentity:
    """Tests for CanonicalValidatorIdentity model."""

    async def test_create_solana_validator_identity(self, db_session: AsyncSession) -> None:
        """Test creating a Solana validator identity."""
        # Create chain
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True
        )
        db_session.add(chain)
        await db_session.commit()

        # Create validator identity
        identity = CanonicalValidatorIdentity(
            chain_id=chain.chain_id,
            validator_key="vote_pubkey_123",
            vote_pubkey="vote_pubkey_123",
            node_pubkey="node_pubkey_456",
            identity_pubkey="identity_pubkey_789",
            display_name="Test Validator",
            is_active=True
        )
        db_session.add(identity)
        await db_session.commit()

        # Verify identity was created
        result = await db_session.execute(
            select(CanonicalValidatorIdentity).where(
                CanonicalValidatorIdentity.validator_key == "vote_pubkey_123"
            )
        )
        saved_identity = result.scalar_one()

        assert saved_identity.chain_id == "solana-mainnet"
        assert saved_identity.validator_key == "vote_pubkey_123"
        assert saved_identity.vote_pubkey == "vote_pubkey_123"
        assert saved_identity.node_pubkey == "node_pubkey_456"
        assert saved_identity.identity_pubkey == "identity_pubkey_789"
        assert saved_identity.display_name == "Test Validator"
        assert saved_identity.fee_recipient is None  # Solana doesn't use fee_recipient
        assert saved_identity.is_active is True

    async def test_create_ethereum_validator_identity(self, db_session: AsyncSession) -> None:
        """Test creating an Ethereum validator identity."""
        # Create chain
        chain = Chain(
            chain_id="ethereum-mainnet",
            name="Ethereum Mainnet",
            period_type="BLOCK_WINDOW",
            native_unit="wei",
            native_decimals=18,
            finality_lag=1,
            is_active=True
        )
        db_session.add(chain)
        await db_session.commit()

        # Create validator identity
        identity = CanonicalValidatorIdentity(
            chain_id=chain.chain_id,
            validator_key="0x123...abc",
            fee_recipient="0x123...abc",
            display_name="Ethereum Validator",
            is_active=True
        )
        db_session.add(identity)
        await db_session.commit()

        # Verify identity was created
        result = await db_session.execute(
            select(CanonicalValidatorIdentity).where(
                CanonicalValidatorIdentity.validator_key == "0x123...abc"
            )
        )
        saved_identity = result.scalar_one()

        assert saved_identity.chain_id == "ethereum-mainnet"
        assert saved_identity.validator_key == "0x123...abc"
        assert saved_identity.fee_recipient == "0x123...abc"
        assert saved_identity.vote_pubkey is None  # Ethereum doesn't use Solana keys
        assert saved_identity.is_active is True

    async def test_validator_identity_unique_constraint(self, db_session: AsyncSession) -> None:
        """Test validator identity unique constraint on (chain_id, validator_key)."""
        # Create chain
        chain = Chain(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True
        )
        db_session.add(chain)
        await db_session.commit()

        # Create first identity
        identity1 = CanonicalValidatorIdentity(
            chain_id=chain.chain_id,
            validator_key="vote_pubkey_123",
            vote_pubkey="vote_pubkey_123",
            is_active=True
        )
        db_session.add(identity1)
        await db_session.commit()

        # Try to create duplicate identity
        identity2 = CanonicalValidatorIdentity(
            chain_id=chain.chain_id,
            validator_key="vote_pubkey_123",  # Duplicate key
            vote_pubkey="vote_pubkey_123",
            is_active=True
        )
        db_session.add(identity2)

        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()

        assert "uq_canonical_validator_identities_chain_key" in str(exc_info.value)
        await db_session.rollback()
