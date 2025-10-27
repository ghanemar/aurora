"""Unit tests for computation layer models.

Tests cover:
- ValidatorPnL model creation and validation
- Partners model creation and validation
- Agreements model creation and validation
- AgreementVersions model creation and validation
- AgreementRules model creation and validation
- PartnerCommissionLines model creation and validation
- PartnerCommissionStatements model creation and validation
- All enum types (AgreementStatus, RevenueComponent, AttributionMethod, StatementStatus)
- NUMERIC(38,18) decimal precision for amounts
- Unique constraints and data integrity
- Check constraints (positive amounts, valid rates, etc.)
- Relationships with chain, period, and other models
- Constraint validation and cascade deletes
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from core.models import (
    AgreementRules,
    Agreements,
    AgreementStatus,
    AgreementVersions,
    AttributionMethod,
    CanonicalPeriod,
    Chain,
    PartnerCommissionLines,
    PartnerCommissionStatements,
    Partners,
    RevenueComponent,
    StatementStatus,
    ValidatorPnL,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class TestValidatorPnLModel:
    """Tests for ValidatorPnL model."""

    async def test_create_validator_pnl(self, db_session: AsyncSession) -> None:
        """Test creating a valid validator P&L record."""
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

        # Create validator P&L
        pnl = ValidatorPnL(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            exec_fees_native=Decimal("1500000.500000000000000000"),
            mev_tips_native=Decimal("750000.250000000000000000"),
            vote_rewards_native=Decimal("500000.000000000000000000"),
            commission_native=Decimal("250000.125000000000000000"),
            total_revenue_native=Decimal("3000000.875000000000000000"),
        )
        db_session.add(pnl)
        await db_session.commit()

        # Verify P&L was created
        result = await db_session.execute(
            select(ValidatorPnL).where(ValidatorPnL.pnl_id == pnl.pnl_id)
        )
        saved_pnl = result.scalar_one()

        assert saved_pnl.chain_id == "solana-mainnet"
        assert saved_pnl.period_id == period.period_id
        assert saved_pnl.validator_key == "validator123"
        assert Decimal(str(saved_pnl.exec_fees_native)) == Decimal("1500000.500000000000000000")
        assert Decimal(str(saved_pnl.mev_tips_native)) == Decimal("750000.250000000000000000")
        assert Decimal(str(saved_pnl.vote_rewards_native)) == Decimal("500000.000000000000000000")
        assert Decimal(str(saved_pnl.commission_native)) == Decimal("250000.125000000000000000")
        assert Decimal(str(saved_pnl.total_revenue_native)) == Decimal("3000000.875000000000000000")
        assert saved_pnl.computed_at is not None
        assert saved_pnl.created_at is not None
        assert saved_pnl.updated_at is not None

    async def test_validator_pnl_unique_constraint(self, db_session: AsyncSession) -> None:
        """Test unique constraint on (chain_id, period_id, validator_key)."""
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

        # Create first P&L record
        pnl1 = ValidatorPnL(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            exec_fees_native=Decimal("1000.0"),
            total_revenue_native=Decimal("1000.0"),
        )
        db_session.add(pnl1)
        await db_session.commit()

        # Attempt to create duplicate
        pnl2 = ValidatorPnL(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            exec_fees_native=Decimal("2000.0"),
            total_revenue_native=Decimal("2000.0"),
        )
        db_session.add(pnl2)

        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()
        assert "uq_validator_pnl_chain_period_validator" in str(exc_info.value)

    async def test_validator_pnl_check_constraints(self, db_session: AsyncSession) -> None:
        """Test check constraints for positive amounts."""
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

        # Test negative exec_fees_native
        pnl = ValidatorPnL(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            exec_fees_native=Decimal("-1000.0"),
            total_revenue_native=Decimal("1000.0"),
        )
        db_session.add(pnl)

        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()
        assert "ck_validator_pnl_exec_fees_positive" in str(exc_info.value)

    async def test_validator_pnl_cascade_delete(self, db_session: AsyncSession) -> None:
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

        period = CanonicalPeriod(
            chain_id="solana-mainnet",
            period_identifier="850",
            period_start=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            period_end=datetime(2024, 1, 3, 0, 0, 0, tzinfo=UTC),
            is_finalized=True,
        )
        db_session.add(period)
        await db_session.flush()

        pnl = ValidatorPnL(
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            exec_fees_native=Decimal("1000.0"),
            total_revenue_native=Decimal("1000.0"),
        )
        db_session.add(pnl)
        await db_session.commit()

        pnl_id = pnl.pnl_id

        # Delete chain should cascade to P&L
        await db_session.delete(chain)
        await db_session.commit()

        result = await db_session.execute(select(ValidatorPnL).where(ValidatorPnL.pnl_id == pnl_id))
        assert result.scalar_one_or_none() is None


class TestPartnersModel:
    """Tests for Partners model."""

    async def test_create_partner(self, db_session: AsyncSession) -> None:
        """Test creating a valid partner record."""
        partner = Partners(
            partner_name="Global Stake",
            legal_entity_name="Global Stake LLC",
            contact_email="contact@globalstake.io",
            contact_name="John Doe",
            is_active=True,
        )
        db_session.add(partner)
        await db_session.commit()

        # Verify partner was created
        result = await db_session.execute(
            select(Partners).where(Partners.partner_id == partner.partner_id)
        )
        saved_partner = result.scalar_one()

        assert saved_partner.partner_name == "Global Stake"
        assert saved_partner.legal_entity_name == "Global Stake LLC"
        assert saved_partner.contact_email == "contact@globalstake.io"
        assert saved_partner.contact_name == "John Doe"
        assert saved_partner.is_active is True
        assert saved_partner.created_at is not None
        assert saved_partner.updated_at is not None

    async def test_partner_nullable_fields(self, db_session: AsyncSession) -> None:
        """Test creating partner with nullable fields."""
        partner = Partners(
            partner_name="Minimal Partner",
            contact_email="minimal@example.com",
            is_active=True,
        )
        db_session.add(partner)
        await db_session.commit()

        result = await db_session.execute(
            select(Partners).where(Partners.partner_id == partner.partner_id)
        )
        saved_partner = result.scalar_one()

        assert saved_partner.legal_entity_name is None
        assert saved_partner.contact_name is None


class TestAgreementsModel:
    """Tests for Agreements model."""

    async def test_create_agreement(self, db_session: AsyncSession) -> None:
        """Test creating a valid agreement record."""
        partner = Partners(
            partner_name="Global Stake",
            contact_email="contact@globalstake.io",
            is_active=True,
        )
        db_session.add(partner)
        await db_session.flush()

        agreement = Agreements(
            partner_id=partner.partner_id,
            agreement_name="2024 Commission Agreement",
            current_version=1,
            status=AgreementStatus.ACTIVE,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            effective_until=datetime(2024, 12, 31, 23, 59, 59, tzinfo=UTC),
        )
        db_session.add(agreement)
        await db_session.commit()

        # Verify agreement was created
        result = await db_session.execute(
            select(Agreements).where(Agreements.agreement_id == agreement.agreement_id)
        )
        saved_agreement = result.scalar_one()

        assert saved_agreement.partner_id == partner.partner_id
        assert saved_agreement.agreement_name == "2024 Commission Agreement"
        assert saved_agreement.current_version == 1
        assert saved_agreement.status == AgreementStatus.ACTIVE
        assert saved_agreement.effective_from == datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        assert saved_agreement.effective_until == datetime(2024, 12, 31, 23, 59, 59, tzinfo=UTC)
        assert saved_agreement.created_at is not None
        assert saved_agreement.updated_at is not None

    async def test_agreement_status_enum(self, db_session: AsyncSession) -> None:
        """Test AgreementStatus enum values."""
        partner = Partners(
            partner_name="Global Stake",
            contact_email="contact@globalstake.io",
            is_active=True,
        )
        db_session.add(partner)
        await db_session.flush()

        # Test each status
        for status in [
            AgreementStatus.DRAFT,
            AgreementStatus.ACTIVE,
            AgreementStatus.SUSPENDED,
            AgreementStatus.TERMINATED,
        ]:
            agreement = Agreements(
                partner_id=partner.partner_id,
                agreement_name=f"Agreement {status.value}",
                current_version=1,
                status=status,
                effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            )
            db_session.add(agreement)
            await db_session.flush()

            result = await db_session.execute(
                select(Agreements).where(Agreements.agreement_id == agreement.agreement_id)
            )
            saved_agreement = result.scalar_one()
            assert saved_agreement.status == status

        await db_session.commit()

    async def test_agreement_restrict_delete_partner(self, db_session: AsyncSession) -> None:
        """Test RESTRICT on partner delete when agreement exists."""
        partner = Partners(
            partner_name="Global Stake",
            contact_email="contact@globalstake.io",
            is_active=True,
        )
        db_session.add(partner)
        await db_session.flush()

        agreement = Agreements(
            partner_id=partner.partner_id,
            agreement_name="2024 Agreement",
            current_version=1,
            status=AgreementStatus.ACTIVE,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        )
        db_session.add(agreement)
        await db_session.commit()

        # Attempt to delete partner with existing agreement
        await db_session.delete(partner)

        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestAgreementVersionsModel:
    """Tests for AgreementVersions model."""

    async def test_create_agreement_version(self, db_session: AsyncSession) -> None:
        """Test creating a valid agreement version record."""
        partner = Partners(
            partner_name="Global Stake",
            contact_email="contact@globalstake.io",
            is_active=True,
        )
        db_session.add(partner)
        await db_session.flush()

        agreement = Agreements(
            partner_id=partner.partner_id,
            agreement_name="2024 Agreement",
            current_version=1,
            status=AgreementStatus.ACTIVE,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        )
        db_session.add(agreement)
        await db_session.flush()

        version = AgreementVersions(
            agreement_id=agreement.agreement_id,
            version_number=1,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            effective_until=datetime(2024, 6, 30, 23, 59, 59, tzinfo=UTC),
            terms_snapshot={"rate": 10, "components": ["EXEC_FEES", "MEV_TIPS"]},
            created_by=None,  # User model not yet implemented
        )
        db_session.add(version)
        await db_session.commit()

        # Verify version was created
        result = await db_session.execute(
            select(AgreementVersions).where(AgreementVersions.version_id == version.version_id)
        )
        saved_version = result.scalar_one()

        assert saved_version.agreement_id == agreement.agreement_id
        assert saved_version.version_number == 1
        assert saved_version.effective_from == datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        assert saved_version.effective_until == datetime(2024, 6, 30, 23, 59, 59, tzinfo=UTC)
        assert saved_version.terms_snapshot == {"rate": 10, "components": ["EXEC_FEES", "MEV_TIPS"]}
        assert saved_version.created_at is not None

    async def test_agreement_version_unique_constraint(self, db_session: AsyncSession) -> None:
        """Test unique constraint on (agreement_id, version_number)."""
        partner = Partners(
            partner_name="Global Stake",
            contact_email="contact@globalstake.io",
            is_active=True,
        )
        db_session.add(partner)
        await db_session.flush()

        agreement = Agreements(
            partner_id=partner.partner_id,
            agreement_name="2024 Agreement",
            current_version=1,
            status=AgreementStatus.ACTIVE,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        )
        db_session.add(agreement)
        await db_session.flush()

        # Create first version
        version1 = AgreementVersions(
            agreement_id=agreement.agreement_id,
            version_number=1,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            terms_snapshot={"rate": 10},
        )
        db_session.add(version1)
        await db_session.commit()

        # Attempt to create duplicate version
        version2 = AgreementVersions(
            agreement_id=agreement.agreement_id,
            version_number=1,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            terms_snapshot={"rate": 15},
        )
        db_session.add(version2)

        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()
        assert "uq_agreement_versions_agreement_version" in str(exc_info.value)

    async def test_agreement_version_cascade_delete(self, db_session: AsyncSession) -> None:
        """Test cascade delete when agreement is deleted."""
        # First delete partner (which will delete agreement via RESTRICT, so we need to delete agreement first)
        partner = Partners(
            partner_name="Global Stake",
            contact_email="contact@globalstake.io",
            is_active=True,
        )
        db_session.add(partner)
        await db_session.flush()

        agreement = Agreements(
            partner_id=partner.partner_id,
            agreement_name="2024 Agreement",
            current_version=1,
            status=AgreementStatus.ACTIVE,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        )
        db_session.add(agreement)
        await db_session.flush()

        version = AgreementVersions(
            agreement_id=agreement.agreement_id,
            version_number=1,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            terms_snapshot={"rate": 10},
        )
        db_session.add(version)
        await db_session.commit()

        version_id = version.version_id

        # Refresh the agreement to ensure it's bound to the session
        await db_session.refresh(agreement)

        # Delete agreement should cascade to version
        await db_session.delete(agreement)
        await db_session.commit()

        # Verify version was cascade deleted
        result = await db_session.execute(
            select(AgreementVersions).where(AgreementVersions.version_id == version_id)
        )
        assert result.scalar_one_or_none() is None


class TestAgreementRulesModel:
    """Tests for AgreementRules model."""

    async def test_create_agreement_rule(self, db_session: AsyncSession) -> None:
        """Test creating a valid agreement rule record."""
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

        # Create partner and agreement
        partner = Partners(
            partner_name="Global Stake",
            contact_email="contact@globalstake.io",
            is_active=True,
        )
        db_session.add(partner)
        await db_session.flush()

        agreement = Agreements(
            partner_id=partner.partner_id,
            agreement_name="2024 Agreement",
            current_version=1,
            status=AgreementStatus.ACTIVE,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        )
        db_session.add(agreement)
        await db_session.flush()

        # Create agreement version
        version = AgreementVersions(
            agreement_id=agreement.agreement_id,
            version_number=1,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            terms_snapshot={"rate": 10},
        )
        db_session.add(version)
        await db_session.flush()

        # Create agreement rule
        rule = AgreementRules(
            agreement_id=agreement.agreement_id,
            version_number=1,
            rule_order=1,
            chain_id="solana-mainnet",
            validator_key="validator123",
            revenue_component=RevenueComponent.EXEC_FEES,
            attribution_method=AttributionMethod.CLIENT_REVENUE,
            commission_rate_bps=1000,  # 10%
            floor_amount_native=Decimal("100.0"),
            cap_amount_native=Decimal("10000.0"),
            tier_config={"tiers": [{"threshold": 1000, "rate": 1000}]},
            is_active=True,
        )
        db_session.add(rule)
        await db_session.commit()

        # Verify rule was created
        result = await db_session.execute(
            select(AgreementRules).where(AgreementRules.rule_id == rule.rule_id)
        )
        saved_rule = result.scalar_one()

        assert saved_rule.agreement_id == agreement.agreement_id
        assert saved_rule.version_number == 1
        assert saved_rule.rule_order == 1
        assert saved_rule.chain_id == "solana-mainnet"
        assert saved_rule.validator_key == "validator123"
        assert saved_rule.revenue_component == RevenueComponent.EXEC_FEES
        assert saved_rule.attribution_method == AttributionMethod.CLIENT_REVENUE
        assert saved_rule.commission_rate_bps == 1000
        assert Decimal(str(saved_rule.floor_amount_native)) == Decimal("100.0")
        assert Decimal(str(saved_rule.cap_amount_native)) == Decimal("10000.0")
        assert saved_rule.tier_config == {"tiers": [{"threshold": 1000, "rate": 1000}]}
        assert saved_rule.is_active is True
        assert saved_rule.created_at is not None
        assert saved_rule.updated_at is not None

    async def test_agreement_rule_commission_rate_constraint(
        self, db_session: AsyncSession
    ) -> None:
        """Test commission_rate_bps check constraint (0-10000)."""
        partner = Partners(
            partner_name="Global Stake",
            contact_email="contact@globalstake.io",
            is_active=True,
        )
        db_session.add(partner)
        await db_session.flush()

        agreement = Agreements(
            partner_id=partner.partner_id,
            agreement_name="2024 Agreement",
            current_version=1,
            status=AgreementStatus.ACTIVE,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        )
        db_session.add(agreement)
        await db_session.flush()

        version = AgreementVersions(
            agreement_id=agreement.agreement_id,
            version_number=1,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            terms_snapshot={"rate": 10},
        )
        db_session.add(version)
        await db_session.flush()

        # Test invalid rate > 10000
        rule = AgreementRules(
            agreement_id=agreement.agreement_id,
            version_number=1,
            rule_order=1,
            revenue_component=RevenueComponent.EXEC_FEES,
            attribution_method=AttributionMethod.CLIENT_REVENUE,
            commission_rate_bps=15000,  # Invalid: > 10000
            is_active=True,
        )
        db_session.add(rule)

        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()
        assert "ck_agreement_rules_commission_rate_valid" in str(exc_info.value)

    async def test_agreement_rule_enums(self, db_session: AsyncSession) -> None:
        """Test RevenueComponent and AttributionMethod enum values."""
        partner = Partners(
            partner_name="Global Stake",
            contact_email="contact@globalstake.io",
            is_active=True,
        )
        db_session.add(partner)
        await db_session.flush()

        agreement = Agreements(
            partner_id=partner.partner_id,
            agreement_name="2024 Agreement",
            current_version=1,
            status=AgreementStatus.ACTIVE,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        )
        db_session.add(agreement)
        await db_session.flush()

        version = AgreementVersions(
            agreement_id=agreement.agreement_id,
            version_number=1,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            terms_snapshot={"rate": 10},
        )
        db_session.add(version)
        await db_session.flush()

        # Test each revenue component
        for i, component in enumerate(
            [
                RevenueComponent.EXEC_FEES,
                RevenueComponent.MEV_TIPS,
                RevenueComponent.VOTE_REWARDS,
                RevenueComponent.COMMISSION,
            ]
        ):
            rule = AgreementRules(
                agreement_id=agreement.agreement_id,
                version_number=1,
                rule_order=i + 1,
                revenue_component=component,
                attribution_method=AttributionMethod.CLIENT_REVENUE,
                commission_rate_bps=1000,
                is_active=True,
            )
            db_session.add(rule)
            await db_session.flush()

            result = await db_session.execute(
                select(AgreementRules).where(AgreementRules.rule_id == rule.rule_id)
            )
            saved_rule = result.scalar_one()
            assert saved_rule.revenue_component == component

        # Test each attribution method
        for i, method in enumerate(
            [
                AttributionMethod.CLIENT_REVENUE,
                AttributionMethod.STAKE_WEIGHT,
                AttributionMethod.FIXED_SHARE,
            ]
        ):
            rule = AgreementRules(
                agreement_id=agreement.agreement_id,
                version_number=1,
                rule_order=i + 10,
                revenue_component=RevenueComponent.EXEC_FEES,
                attribution_method=method,
                commission_rate_bps=1000,
                is_active=True,
            )
            db_session.add(rule)
            await db_session.flush()

            result = await db_session.execute(
                select(AgreementRules).where(AgreementRules.rule_id == rule.rule_id)
            )
            saved_rule = result.scalar_one()
            assert saved_rule.attribution_method == method

        await db_session.commit()


class TestPartnerCommissionLinesModel:
    """Tests for PartnerCommissionLines model."""

    async def test_create_commission_line(self, db_session: AsyncSession) -> None:
        """Test creating a valid commission line record."""
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
            period_identifier="850",
            period_start=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            period_end=datetime(2024, 1, 3, 0, 0, 0, tzinfo=UTC),
            is_finalized=True,
        )
        db_session.add(period)
        await db_session.flush()

        # Create partner, agreement, version, rule
        partner = Partners(
            partner_name="Global Stake",
            contact_email="contact@globalstake.io",
            is_active=True,
        )
        db_session.add(partner)
        await db_session.flush()

        agreement = Agreements(
            partner_id=partner.partner_id,
            agreement_name="2024 Agreement",
            current_version=1,
            status=AgreementStatus.ACTIVE,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        )
        db_session.add(agreement)
        await db_session.flush()

        version = AgreementVersions(
            agreement_id=agreement.agreement_id,
            version_number=1,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            terms_snapshot={"rate": 10},
        )
        db_session.add(version)
        await db_session.flush()

        rule = AgreementRules(
            agreement_id=agreement.agreement_id,
            version_number=1,
            rule_order=1,
            revenue_component=RevenueComponent.EXEC_FEES,
            attribution_method=AttributionMethod.CLIENT_REVENUE,
            commission_rate_bps=1000,
            is_active=True,
        )
        db_session.add(rule)
        await db_session.flush()

        # Create commission line
        line = PartnerCommissionLines(
            agreement_id=agreement.agreement_id,
            agreement_version=1,
            rule_id=rule.rule_id,
            partner_id=partner.partner_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            revenue_component=RevenueComponent.EXEC_FEES,
            attribution_method=AttributionMethod.CLIENT_REVENUE,
            base_amount_native=Decimal("100000.0"),
            commission_rate_bps=1000,
            pre_override_amount_native=Decimal("10000.0"),
            override_amount_native=None,
            override_reason=None,
            override_user_id=None,
            override_timestamp=None,
            final_amount_native=Decimal("10000.0"),
        )
        db_session.add(line)
        await db_session.commit()

        # Verify line was created
        result = await db_session.execute(
            select(PartnerCommissionLines).where(PartnerCommissionLines.line_id == line.line_id)
        )
        saved_line = result.scalar_one()

        assert saved_line.agreement_id == agreement.agreement_id
        assert saved_line.agreement_version == 1
        assert saved_line.rule_id == rule.rule_id
        assert saved_line.partner_id == partner.partner_id
        assert saved_line.chain_id == "solana-mainnet"
        assert saved_line.period_id == period.period_id
        assert saved_line.validator_key == "validator123"
        assert saved_line.revenue_component == RevenueComponent.EXEC_FEES
        assert saved_line.attribution_method == AttributionMethod.CLIENT_REVENUE
        assert Decimal(str(saved_line.base_amount_native)) == Decimal("100000.0")
        assert saved_line.commission_rate_bps == 1000
        assert Decimal(str(saved_line.pre_override_amount_native)) == Decimal("10000.0")
        assert saved_line.override_amount_native is None
        assert Decimal(str(saved_line.final_amount_native)) == Decimal("10000.0")
        assert saved_line.computed_at is not None
        assert saved_line.created_at is not None
        assert saved_line.updated_at is not None

    async def test_commission_line_with_override(self, db_session: AsyncSession) -> None:
        """Test commission line with manual override."""
        # Create dependencies
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

        partner = Partners(
            partner_name="Global Stake",
            contact_email="contact@globalstake.io",
            is_active=True,
        )
        db_session.add(partner)
        await db_session.flush()

        agreement = Agreements(
            partner_id=partner.partner_id,
            agreement_name="2024 Agreement",
            current_version=1,
            status=AgreementStatus.ACTIVE,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        )
        db_session.add(agreement)
        await db_session.flush()

        version = AgreementVersions(
            agreement_id=agreement.agreement_id,
            version_number=1,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            terms_snapshot={"rate": 10},
        )
        db_session.add(version)
        await db_session.flush()

        rule = AgreementRules(
            agreement_id=agreement.agreement_id,
            version_number=1,
            rule_order=1,
            revenue_component=RevenueComponent.EXEC_FEES,
            attribution_method=AttributionMethod.CLIENT_REVENUE,
            commission_rate_bps=1000,
            is_active=True,
        )
        db_session.add(rule)
        await db_session.flush()

        # Create line with override
        line = PartnerCommissionLines(
            agreement_id=agreement.agreement_id,
            agreement_version=1,
            rule_id=rule.rule_id,
            partner_id=partner.partner_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            validator_key="validator123",
            revenue_component=RevenueComponent.EXEC_FEES,
            attribution_method=AttributionMethod.CLIENT_REVENUE,
            base_amount_native=Decimal("100000.0"),
            commission_rate_bps=1000,
            pre_override_amount_native=Decimal("10000.0"),
            override_amount_native=Decimal("12000.0"),
            override_reason="Bonus for exceeding target",
            override_user_id=None,  # User model not yet implemented
            override_timestamp=datetime(2024, 1, 10, 12, 0, 0, tzinfo=UTC),
            final_amount_native=Decimal("12000.0"),
        )
        db_session.add(line)
        await db_session.commit()

        result = await db_session.execute(
            select(PartnerCommissionLines).where(PartnerCommissionLines.line_id == line.line_id)
        )
        saved_line = result.scalar_one()

        assert Decimal(str(saved_line.override_amount_native)) == Decimal("12000.0")
        assert saved_line.override_reason == "Bonus for exceeding target"
        assert saved_line.override_timestamp is not None

    async def test_commission_line_check_constraints(self, db_session: AsyncSession) -> None:
        """Test check constraints for commission line amounts."""
        # Create minimal dependencies
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

        partner = Partners(
            partner_name="Global Stake",
            contact_email="contact@globalstake.io",
            is_active=True,
        )
        db_session.add(partner)
        await db_session.flush()

        agreement = Agreements(
            partner_id=partner.partner_id,
            agreement_name="2024 Agreement",
            current_version=1,
            status=AgreementStatus.ACTIVE,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        )
        db_session.add(agreement)
        await db_session.flush()

        version = AgreementVersions(
            agreement_id=agreement.agreement_id,
            version_number=1,
            effective_from=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            terms_snapshot={"rate": 10},
        )
        db_session.add(version)
        await db_session.flush()

        rule = AgreementRules(
            agreement_id=agreement.agreement_id,
            version_number=1,
            rule_order=1,
            revenue_component=RevenueComponent.EXEC_FEES,
            attribution_method=AttributionMethod.CLIENT_REVENUE,
            commission_rate_bps=1000,
            is_active=True,
        )
        db_session.add(rule)
        await db_session.flush()

        # Test negative final_amount_native
        line = PartnerCommissionLines(
            agreement_id=agreement.agreement_id,
            agreement_version=1,
            rule_id=rule.rule_id,
            partner_id=partner.partner_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            revenue_component=RevenueComponent.EXEC_FEES,
            attribution_method=AttributionMethod.CLIENT_REVENUE,
            base_amount_native=Decimal("100000.0"),
            commission_rate_bps=1000,
            pre_override_amount_native=Decimal("10000.0"),
            final_amount_native=Decimal("-1000.0"),  # Invalid: negative
        )
        db_session.add(line)

        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()
        assert "ck_commission_lines_final_positive" in str(exc_info.value)


class TestPartnerCommissionStatementsModel:
    """Tests for PartnerCommissionStatements model."""

    async def test_create_commission_statement(self, db_session: AsyncSession) -> None:
        """Test creating a valid commission statement record."""
        # Create dependencies
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

        partner = Partners(
            partner_name="Global Stake",
            contact_email="contact@globalstake.io",
            is_active=True,
        )
        db_session.add(partner)
        await db_session.flush()

        # Create statement
        statement = PartnerCommissionStatements(
            partner_id=partner.partner_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            total_commission_native=Decimal("50000.0"),
            line_count=10,
            status=StatementStatus.DRAFT,
            approved_by=None,
            approved_at=None,
            released_by=None,
            released_at=None,
            paid_at=None,
            statement_metadata={"notes": "Monthly statement"},
        )
        db_session.add(statement)
        await db_session.commit()

        # Verify statement was created
        result = await db_session.execute(
            select(PartnerCommissionStatements).where(
                PartnerCommissionStatements.statement_id == statement.statement_id
            )
        )
        saved_statement = result.scalar_one()

        assert saved_statement.partner_id == partner.partner_id
        assert saved_statement.chain_id == "solana-mainnet"
        assert saved_statement.period_id == period.period_id
        assert Decimal(str(saved_statement.total_commission_native)) == Decimal("50000.0")
        assert saved_statement.line_count == 10
        assert saved_statement.status == StatementStatus.DRAFT
        assert saved_statement.statement_metadata == {"notes": "Monthly statement"}
        assert saved_statement.created_at is not None
        assert saved_statement.updated_at is not None

    async def test_statement_status_enum(self, db_session: AsyncSession) -> None:
        """Test StatementStatus enum values."""
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

        partner = Partners(
            partner_name="Global Stake",
            contact_email="contact@globalstake.io",
            is_active=True,
        )
        db_session.add(partner)
        await db_session.flush()

        # Test each status with different periods to avoid unique constraint
        for i, status in enumerate(
            [
                StatementStatus.DRAFT,
                StatementStatus.PENDING_APPROVAL,
                StatementStatus.APPROVED,
                StatementStatus.RELEASED,
                StatementStatus.PAID,
            ]
        ):
            # Create unique period for each statement
            period = CanonicalPeriod(
                chain_id="solana-mainnet",
                period_identifier=str(850 + i),
                period_start=datetime(2024, i + 1, 1, 0, 0, 0, tzinfo=UTC),
                period_end=datetime(2024, i + 1, 3, 0, 0, 0, tzinfo=UTC),
                is_finalized=True,
            )
            db_session.add(period)
            await db_session.flush()

            statement = PartnerCommissionStatements(
                partner_id=partner.partner_id,
                chain_id="solana-mainnet",
                period_id=period.period_id,
                total_commission_native=Decimal("50000.0"),
                line_count=i + 1,
                status=status,
            )
            db_session.add(statement)
            await db_session.flush()

            result = await db_session.execute(
                select(PartnerCommissionStatements).where(
                    PartnerCommissionStatements.statement_id == statement.statement_id
                )
            )
            saved_statement = result.scalar_one()
            assert saved_statement.status == status

        await db_session.commit()

    async def test_statement_unique_constraint(self, db_session: AsyncSession) -> None:
        """Test unique constraint on (partner_id, chain_id, period_id)."""
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

        partner = Partners(
            partner_name="Global Stake",
            contact_email="contact@globalstake.io",
            is_active=True,
        )
        db_session.add(partner)
        await db_session.flush()

        # Create first statement
        statement1 = PartnerCommissionStatements(
            partner_id=partner.partner_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            total_commission_native=Decimal("50000.0"),
            line_count=10,
            status=StatementStatus.DRAFT,
        )
        db_session.add(statement1)
        await db_session.commit()

        # Attempt to create duplicate
        statement2 = PartnerCommissionStatements(
            partner_id=partner.partner_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            total_commission_native=Decimal("60000.0"),
            line_count=12,
            status=StatementStatus.DRAFT,
        )
        db_session.add(statement2)

        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()
        assert "uq_statements_partner_chain_period" in str(exc_info.value)

    async def test_statement_check_constraints(self, db_session: AsyncSession) -> None:
        """Test check constraints for statement amounts and counts."""
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

        partner = Partners(
            partner_name="Global Stake",
            contact_email="contact@globalstake.io",
            is_active=True,
        )
        db_session.add(partner)
        await db_session.flush()

        # Test negative total_commission_native
        statement = PartnerCommissionStatements(
            partner_id=partner.partner_id,
            chain_id="solana-mainnet",
            period_id=period.period_id,
            total_commission_native=Decimal("-1000.0"),  # Invalid: negative
            line_count=10,
            status=StatementStatus.DRAFT,
        )
        db_session.add(statement)

        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()
        assert "ck_statements_total_positive" in str(exc_info.value)
