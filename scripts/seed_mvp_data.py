#!/usr/bin/env python3
"""MVP Data Seeding Script.

This script seeds the database with realistic test data for MVP demo.
The script is idempotent - it can be run multiple times safely without
duplicating data.

Usage:
    python scripts/seed_mvp_data.py

Requirements:
    - Database must be running (via docker-compose up)
    - All migrations must be applied
    - Environment variables must be configured (.env file)

Seeded Data:
    - 1 Chain (solana-mainnet)
    - 1 Provider (Jito for MEV/fees data)
    - 1 Admin User (admin/admin123)
    - 3 Solana Validators with CanonicalValidatorIdentity
    - 2 Partners with contact information
    - 3 Canonical Periods (last 3 epochs)
    - 2 Active Agreements (one per partner)
    - Agreement Rules for commission calculation
    - ValidatorPnL data for last 3 epochs
    - CanonicalValidatorMEV records
    - CanonicalValidatorFees records
"""

import asyncio
import hashlib
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from src.core.models.canonical import CanonicalValidatorFees, CanonicalValidatorMEV
from src.core.models.chains import (
    CanonicalPeriod,
    CanonicalStakeEvent,
    CanonicalStakerRewardsDetail,
    CanonicalValidatorIdentity,
    Chain,
    Provider,
    StakeEventType,
)
from src.core.models.computation import (
    AgreementRules,
    Agreements,
    AgreementStatus,
    AgreementVersions,
    AttributionMethod,
    Partners,
    PartnerWallet,
    RevenueComponent,
    ValidatorPnL,
)
from src.core.models.staging import DataType, IngestionRun, IngestionStatus, StagingPayload
from src.core.models.users import User, UserRole
from src.core.security import hash_password
from src.db.session import async_session_factory

# ============================================================================
# Configuration & Constants
# ============================================================================

# Validator vote pubkeys (to be provided by user)
# These should be real Solana mainnet validator vote pubkeys
VALIDATOR_VOTE_PUBKEYS = [
    "7Np41oeYqPefeNQEHSv1UDhYrehxin3NStELsSKCT4K2",  # Example validator 1
    "J2nUHEAgZFRyuJbFjdqPrAa9gyWDuc7hErtDQHPhsYRp",  # Example validator 2
    "CertusDeBmqN8ZawdkxK5kFGMwBXdudvWHYwtNgNhvLu",  # Example validator 3
]

# Epoch configuration (recent Solana epochs)
BASE_EPOCH = 850  # Starting epoch number
NUM_EPOCHS = 3  # Last 3 epochs

# Partner configuration
PARTNERS_DATA = [
    {
        "partner_name": "Global Stake Partners",
        "legal_entity_name": "Global Stake Partners LLC",
        "contact_email": "partnerships@globalstake.io",
        "contact_name": "John Partnership",
        "is_active": True,
    },
    {
        "partner_name": "Decentralized Validators Group",
        "legal_entity_name": "DVG Holdings Inc",
        "contact_email": "admin@dvgroup.network",
        "contact_name": "Sarah Validator",
        "is_active": True,
    },
]

# Realistic P&L amounts (in lamports)
# These are approximate values for demonstration
LAMPORTS_PER_SOL = 1_000_000_000
BASE_FEES_PER_EPOCH = 50 * LAMPORTS_PER_SOL  # ~50 SOL in fees per epoch
BASE_MEV_PER_EPOCH = 30 * LAMPORTS_PER_SOL  # ~30 SOL in MEV per epoch
BASE_REWARDS_PER_EPOCH = 100 * LAMPORTS_PER_SOL  # ~100 SOL in rewards per epoch

# ============================================================================
# Helper Functions
# ============================================================================


def compute_sha256(data: str) -> str:
    """Compute SHA-256 hash of data.

    Args:
        data: String data to hash

    Returns:
        Hex-encoded SHA-256 hash
    """
    return hashlib.sha256(data.encode()).hexdigest()


def get_epoch_timestamps(epoch_number: int) -> tuple[datetime, datetime]:
    """Get estimated start and end timestamps for Solana epoch.

    Solana epochs are approximately 2-3 days. This is an approximation
    for demo purposes.

    Args:
        epoch_number: Epoch number

    Returns:
        Tuple of (start_timestamp, end_timestamp)
    """
    # Approximate epoch start (each epoch ~2.5 days)
    days_since_base = (epoch_number - BASE_EPOCH) * 2.5
    start = datetime.now(UTC) - timedelta(days=days_since_base + 2.5)
    end = datetime.now(UTC) - timedelta(days=days_since_base)

    return start, end


# ============================================================================
# Seeding Functions
# ============================================================================


async def seed_chain() -> str:
    """Seed Solana mainnet chain configuration.

    Returns:
        Chain ID
    """
    print("Seeding Chain (solana-mainnet)...")

    async with async_session_factory() as session:
        stmt = insert(Chain).values(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type="EPOCH",
            native_unit="lamports",
            native_decimals=9,
            finality_lag=2,
            is_active=True,
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["chain_id"])

        await session.execute(stmt)
        await session.commit()

    print("✓ Chain seeded")
    return "solana-mainnet"


async def seed_provider() -> uuid.UUID:
    """Seed Jito provider for MEV/fees data.

    Returns:
        Provider ID
    """
    print("Seeding Provider (Jito)...")

    provider_id = uuid.uuid4()

    async with async_session_factory() as session:
        # Check if provider already exists
        result = await session.execute(
            select(Provider).where(Provider.provider_name == "Jito")
        )
        existing = result.scalar_one_or_none()

        if existing:
            print("✓ Provider already exists")
            return existing.provider_id

        stmt = insert(Provider).values(
            provider_id=provider_id,
            provider_name="Jito",
            provider_type="MEV",
            base_url="https://mainnet.block-engine.jito.wtf",
            api_version="v1",
            is_enabled=True,
            rate_limit_per_minute=60,
            timeout_seconds=30,
        )

        await session.execute(stmt)
        await session.commit()

    print("✓ Provider seeded")
    return provider_id


async def seed_admin_user() -> uuid.UUID:
    """Seed admin user with credentials admin/admin123.

    Returns:
        User ID
    """
    print("Seeding Admin User (admin/admin123)...")

    user_id = uuid.uuid4()

    async with async_session_factory() as session:
        # Check if admin user already exists (query ID only to avoid enum issues)
        result = await session.execute(
            select(User.id).where(User.username == "admin")
        )
        existing_id = result.scalar_one_or_none()

        if existing_id:
            print("✓ Admin user already exists")
            return existing_id

        hashed_pwd = hash_password("admin123")

        stmt = insert(User).values(
            id=user_id,
            username="admin",
            email="admin@aurora.local",
            hashed_password=hashed_pwd,
            full_name="System Administrator",
            role=UserRole.ADMIN.value,  # Use .value to get string value
            is_active=True,
            partner_id=None,
        )

        await session.execute(stmt)
        await session.commit()

    print("✓ Admin user seeded (username: admin, password: admin123)")
    return user_id


async def seed_validators(chain_id: str) -> list[str]:
    """Seed 3 Solana validators with CanonicalValidatorIdentity.

    Args:
        chain_id: Chain ID

    Returns:
        List of validator keys
    """
    print("Seeding Validators...")

    validator_keys = []

    async with async_session_factory() as session:
        for i, vote_pubkey in enumerate(VALIDATOR_VOTE_PUBKEYS, 1):
            validator_key = vote_pubkey  # Use vote pubkey as canonical validator key

            stmt = insert(CanonicalValidatorIdentity).values(
                identity_id=uuid.uuid4(),
                chain_id=chain_id,
                validator_key=validator_key,
                vote_pubkey=vote_pubkey,
                node_pubkey=None,  # Not required for MVP
                identity_pubkey=None,  # Not required for MVP
                fee_recipient=None,  # Solana-specific, not Ethereum
                display_name=f"Validator {i}",
                is_active=True,
            )
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["chain_id", "validator_key"]
            )

            await session.execute(stmt)
            validator_keys.append(validator_key)

        await session.commit()

    print(f"✓ {len(validator_keys)} validators seeded")
    return validator_keys


async def seed_partners() -> list[uuid.UUID]:
    """Seed 2 partners with contact information.

    Returns:
        List of partner IDs
    """
    print("Seeding Partners...")

    partner_ids = []

    async with async_session_factory() as session:
        for partner_data in PARTNERS_DATA:
            # Check if partner already exists
            result = await session.execute(
                select(Partners).where(
                    Partners.partner_name == partner_data["partner_name"]
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                partner_ids.append(existing.partner_id)
                continue

            partner_id = uuid.uuid4()

            stmt = insert(Partners).values(
                partner_id=partner_id,
                **partner_data,
            )

            await session.execute(stmt)
            partner_ids.append(partner_id)

        await session.commit()

    print(f"✓ {len(partner_ids)} partners seeded")
    return partner_ids


async def seed_canonical_periods(chain_id: str) -> list[uuid.UUID]:
    """Seed 3 canonical periods (last 3 epochs).

    Args:
        chain_id: Chain ID

    Returns:
        List of period IDs
    """
    print("Seeding Canonical Periods (last 3 epochs)...")

    period_ids = []

    async with async_session_factory() as session:
        for i in range(NUM_EPOCHS):
            epoch_number = BASE_EPOCH + i
            start_ts, end_ts = get_epoch_timestamps(epoch_number)

            period_id = uuid.uuid4()

            stmt = insert(CanonicalPeriod).values(
                period_id=period_id,
                chain_id=chain_id,
                period_identifier=str(epoch_number),
                period_start=start_ts,
                period_end=end_ts,
                is_finalized=True,
                finalized_at=end_ts,
            )
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["chain_id", "period_identifier"]
            )

            result = await session.execute(stmt)

            # If conflict (already exists), fetch the existing period_id
            if result.rowcount == 0:
                result = await session.execute(
                    select(CanonicalPeriod.period_id).where(
                        CanonicalPeriod.chain_id == chain_id,
                        CanonicalPeriod.period_identifier == str(epoch_number),
                    )
                )
                period_id = result.scalar_one()

            period_ids.append(period_id)

        await session.commit()

    print(f"✓ {len(period_ids)} canonical periods seeded")
    return period_ids


async def seed_agreements(partner_ids: list[uuid.UUID]) -> list[uuid.UUID]:
    """Seed 2 active agreements (one per partner).

    Args:
        partner_ids: List of partner IDs

    Returns:
        List of agreement IDs
    """
    print("Seeding Agreements...")

    agreement_ids = []
    effective_from = datetime.now(UTC) - timedelta(days=30)

    async with async_session_factory() as session:
        for i, partner_id in enumerate(partner_ids, 1):
            # Check if agreement already exists
            result = await session.execute(
                select(Agreements).where(Agreements.partner_id == partner_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                agreement_ids.append(existing.agreement_id)
                continue

            agreement_id = uuid.uuid4()

            stmt = insert(Agreements).values(
                agreement_id=agreement_id,
                partner_id=partner_id,
                agreement_name=f"Partner Agreement {i}",
                current_version=1,
                status=AgreementStatus.ACTIVE,
                effective_from=effective_from,
                effective_until=None,  # Ongoing
            )

            await session.execute(stmt)
            agreement_ids.append(agreement_id)

        await session.commit()

    print(f"✓ {len(agreement_ids)} agreements seeded")
    return agreement_ids


async def seed_agreement_versions(
    agreement_ids: list[uuid.UUID], partner_ids: list[uuid.UUID]
) -> None:
    """Seed agreement versions for historical tracking.

    Args:
        agreement_ids: List of agreement IDs
        partner_ids: List of partner IDs
    """
    print("Seeding Agreement Versions...")

    effective_from = datetime.now(UTC) - timedelta(days=30)

    async with async_session_factory() as session:
        for agreement_id, partner_id in zip(agreement_ids, partner_ids, strict=True):
            # Check if version already exists
            result = await session.execute(
                select(AgreementVersions).where(
                    AgreementVersions.agreement_id == agreement_id,
                    AgreementVersions.version_number == 1,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                continue

            stmt = insert(AgreementVersions).values(
                version_id=uuid.uuid4(),
                agreement_id=agreement_id,
                version_number=1,
                effective_from=effective_from,
                effective_until=None,
                terms_snapshot={
                    "version": 1,
                    "created_at": effective_from.isoformat(),
                    "notes": "Initial agreement version",
                },
                created_by=None,  # System created
            )

            await session.execute(stmt)

        await session.commit()

    print("✓ Agreement versions seeded")


async def seed_agreement_rules(
    agreement_ids: list[uuid.UUID],
    validator_keys: list[str],
    chain_id: str,
) -> None:
    """Seed agreement rules for commission calculation.

    Args:
        agreement_ids: List of agreement IDs
        validator_keys: List of validator keys
        chain_id: Chain ID
    """
    print("Seeding Agreement Rules...")

    async with async_session_factory() as session:
        # Agreement 1: Partner 1, 10% on CLIENT_REVENUE, validators 1-2
        agreement1_validators = validator_keys[:2]
        for validator_key in agreement1_validators:
            # Check if rule already exists
            result = await session.execute(
                select(AgreementRules).where(
                    AgreementRules.agreement_id == agreement_ids[0],
                    AgreementRules.validator_key == validator_key,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                continue

            stmt = insert(AgreementRules).values(
                rule_id=uuid.uuid4(),
                agreement_id=agreement_ids[0],
                version_number=1,
                rule_order=1,
                chain_id=chain_id,
                validator_key=validator_key,
                revenue_component=RevenueComponent.MEV_TIPS,
                attribution_method=AttributionMethod.CLIENT_REVENUE,
                commission_rate_bps=1000,  # 10%
                floor_amount_native=None,
                cap_amount_native=None,
                tier_config=None,
                is_active=True,
            )

            await session.execute(stmt)

        # Agreement 2: Partner 2, 15% on CLIENT_REVENUE, validator 3
        agreement2_validator = validator_keys[2]

        # Check if rule already exists
        result = await session.execute(
            select(AgreementRules).where(
                AgreementRules.agreement_id == agreement_ids[1],
                AgreementRules.validator_key == agreement2_validator,
            )
        )
        existing = result.scalar_one_or_none()

        if not existing:
            stmt = insert(AgreementRules).values(
                rule_id=uuid.uuid4(),
                agreement_id=agreement_ids[1],
                version_number=1,
                rule_order=1,
                chain_id=chain_id,
                validator_key=agreement2_validator,
                revenue_component=RevenueComponent.MEV_TIPS,
                attribution_method=AttributionMethod.CLIENT_REVENUE,
                commission_rate_bps=1500,  # 15%
                floor_amount_native=None,
                cap_amount_native=None,
                tier_config=None,
                is_active=True,
            )

            await session.execute(stmt)

        await session.commit()

    print("✓ Agreement rules seeded")


async def seed_ingestion_run_and_payloads(
    chain_id: str,
    period_ids: list[uuid.UUID],
    validator_keys: list[str],
    provider_id: uuid.UUID,
) -> tuple[uuid.UUID, list[uuid.UUID]]:
    """Seed ingestion run and staging payloads for traceability.

    Args:
        chain_id: Chain ID
        period_ids: List of period IDs
        validator_keys: List of validator keys
        provider_id: Provider ID

    Returns:
        Tuple of (ingestion_run_id, list of staging_payload_ids)
    """
    print("Seeding Ingestion Run and Staging Payloads...")

    async with async_session_factory() as session:
        # Create single ingestion run for all data
        run_id = uuid.uuid4()

        stmt = insert(IngestionRun).values(
            run_id=run_id,
            chain_id=chain_id,
            period_id=period_ids[0],  # Reference first period
            started_at=datetime.now(UTC) - timedelta(hours=1),
            completed_at=datetime.now(UTC),
            status=IngestionStatus.SUCCESS,
            error_message=None,
            records_fetched=len(period_ids) * len(validator_keys) * 2,  # Fees + MEV
            records_staged=len(period_ids) * len(validator_keys) * 2,
            job_metadata={"source": "seed_script", "version": "1.0"},
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["run_id"])

        result = await session.execute(stmt)

        # If conflict, fetch existing run_id
        if result.rowcount == 0:
            result = await session.execute(
                select(IngestionRun.run_id)
                .where(IngestionRun.chain_id == chain_id)
                .limit(1)
            )
            existing = result.scalar_one_or_none()
            if existing:
                run_id = existing

        # Create staging payloads for each period/validator/data_type combination
        payload_ids = []
        for period_id in period_ids:
            for validator_key in validator_keys:
                # MEV payload
                mev_payload_id = uuid.uuid4()
                raw_mev = {"validator": validator_key, "mev_tips": BASE_MEV_PER_EPOCH}
                mev_hash = compute_sha256(str(raw_mev))

                mev_stmt = insert(StagingPayload).values(
                    payload_id=mev_payload_id,
                    run_id=run_id,
                    chain_id=chain_id,
                    period_id=period_id,
                    validator_key=validator_key,
                    provider_id=provider_id,
                    data_type=DataType.MEV,
                    fetch_timestamp=datetime.now(UTC),
                    response_hash=mev_hash,
                    raw_payload=raw_mev,
                )
                mev_stmt = mev_stmt.on_conflict_do_nothing(index_elements=["payload_id"])

                await session.execute(mev_stmt)
                payload_ids.append(mev_payload_id)

                # Fees payload
                fees_payload_id = uuid.uuid4()
                raw_fees = {"validator": validator_key, "fees": BASE_FEES_PER_EPOCH}
                fees_hash = compute_sha256(str(raw_fees))

                fees_stmt = insert(StagingPayload).values(
                    payload_id=fees_payload_id,
                    run_id=run_id,
                    chain_id=chain_id,
                    period_id=period_id,
                    validator_key=validator_key,
                    provider_id=provider_id,
                    data_type=DataType.FEES,
                    fetch_timestamp=datetime.now(UTC),
                    response_hash=fees_hash,
                    raw_payload=raw_fees,
                )
                fees_stmt = fees_stmt.on_conflict_do_nothing(
                    index_elements=["payload_id"]
                )

                await session.execute(fees_stmt)
                payload_ids.append(fees_payload_id)

        await session.commit()

    print(f"✓ Ingestion run and {len(payload_ids)} staging payloads seeded")
    return run_id, payload_ids


async def seed_canonical_data(
    chain_id: str,
    period_ids: list[uuid.UUID],
    validator_keys: list[str],
    provider_id: uuid.UUID,
) -> None:
    """Seed canonical validator fees and MEV records.

    Args:
        chain_id: Chain ID
        period_ids: List of period IDs
        validator_keys: List of validator keys
        provider_id: Provider ID
    """
    print("Seeding Canonical Validator Fees and MEV...")

    # First create ingestion run and payloads
    _, payload_ids = await seed_ingestion_run_and_payloads(
        chain_id, period_ids, validator_keys, provider_id
    )

    # Group payload IDs by data type
    mev_payload_ids = payload_ids[::2]  # Every even index is MEV
    fees_payload_ids = payload_ids[1::2]  # Every odd index is FEES

    async with async_session_factory() as session:
        mev_idx = 0
        fees_idx = 0

        for period_id in period_ids:
            for validator_key in validator_keys:
                # Seed CanonicalValidatorMEV
                mev_stmt = insert(CanonicalValidatorMEV).values(
                    mev_id=uuid.uuid4(),
                    chain_id=chain_id,
                    period_id=period_id,
                    validator_key=validator_key,
                    total_mev_native=float(BASE_MEV_PER_EPOCH),
                    tip_count=100,  # Example: 100 MEV tips per epoch
                    source_provider_id=provider_id,
                    source_payload_id=mev_payload_ids[mev_idx],
                    normalized_at=datetime.now(UTC),
                )
                mev_stmt = mev_stmt.on_conflict_do_nothing(
                    index_elements=["chain_id", "period_id", "validator_key"]
                )

                await session.execute(mev_stmt)
                mev_idx += 1

                # Seed CanonicalValidatorFees
                fees_stmt = insert(CanonicalValidatorFees).values(
                    fee_id=uuid.uuid4(),
                    chain_id=chain_id,
                    period_id=period_id,
                    validator_key=validator_key,
                    total_fees_native=float(BASE_FEES_PER_EPOCH),
                    fee_count=1000,  # Example: 1000 fee-paying transactions per epoch
                    source_provider_id=provider_id,
                    source_payload_id=fees_payload_ids[fees_idx],
                    normalized_at=datetime.now(UTC),
                )
                fees_stmt = fees_stmt.on_conflict_do_nothing(
                    index_elements=["chain_id", "period_id", "validator_key"]
                )

                await session.execute(fees_stmt)
                fees_idx += 1

        await session.commit()

    print("✓ Canonical validator fees and MEV seeded")


async def seed_validator_pnl(
    chain_id: str,
    period_ids: list[uuid.UUID],
    validator_keys: list[str],
) -> None:
    """Seed ValidatorPnL data for last 3 epochs.

    Args:
        chain_id: Chain ID
        period_ids: List of period IDs
        validator_keys: List of validator keys
    """
    print("Seeding ValidatorPnL...")

    async with async_session_factory() as session:
        for period_id in period_ids:
            for validator_key in validator_keys:
                exec_fees = float(BASE_FEES_PER_EPOCH)
                mev_tips = float(BASE_MEV_PER_EPOCH)
                vote_rewards = float(BASE_REWARDS_PER_EPOCH)
                commission = 0.0  # No commission from delegators in this example
                total_revenue = exec_fees + mev_tips + vote_rewards + commission

                stmt = insert(ValidatorPnL).values(
                    pnl_id=uuid.uuid4(),
                    chain_id=chain_id,
                    period_id=period_id,
                    validator_key=validator_key,
                    exec_fees_native=exec_fees,
                    mev_tips_native=mev_tips,
                    vote_rewards_native=vote_rewards,
                    commission_native=commission,
                    total_revenue_native=total_revenue,
                    computed_at=datetime.now(UTC),
                )
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=["chain_id", "period_id", "validator_key"]
                )

                await session.execute(stmt)

        await session.commit()

    print("✓ ValidatorPnL seeded")


# ============================================================================
# Partner Wallets Seeding
# ============================================================================


async def seed_partner_wallets(partner_ids: list[uuid.UUID], chain_id: str) -> None:
    """Seed partner wallets for testing wallet attribution.

    Args:
        partner_ids: List of partner UUIDs
        chain_id: Chain identifier
    """
    print("\n10. Seeding Partner Wallets...")

    # Example wallet addresses for testing
    # In production, these would be actual staker wallet addresses
    wallet_data = [
        # Partner 1 wallets
        {
            "partner_id": partner_ids[0],
            "chain_id": chain_id,
            "wallet_address": "Stake11111111111111111111111111111111111111",
            "introduced_date": datetime.now(UTC).date() - timedelta(days=90),
            "notes": "Test wallet 1 for Global Stake Partners",
        },
        {
            "partner_id": partner_ids[0],
            "chain_id": chain_id,
            "wallet_address": "Stake22222222222222222222222222222222222222",
            "introduced_date": datetime.now(UTC).date() - timedelta(days=60),
            "notes": "Test wallet 2 for Global Stake Partners",
        },
        # Partner 2 wallets
        {
            "partner_id": partner_ids[1],
            "chain_id": chain_id,
            "wallet_address": "Stake33333333333333333333333333333333333333",
            "introduced_date": datetime.now(UTC).date() - timedelta(days=45),
            "notes": "Test wallet for DVG",
        },
    ]

    async with async_session_factory() as session:
        for wallet_info in wallet_data:
            # Check if wallet already exists
            result = await session.execute(
                select(PartnerWallet).where(
                    PartnerWallet.partner_id == wallet_info["partner_id"],
                    PartnerWallet.chain_id == wallet_info["chain_id"],
                    PartnerWallet.wallet_address == wallet_info["wallet_address"],
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(
                    f"  → Wallet {wallet_info['wallet_address'][:20]}... already exists"
                )
            else:
                wallet = PartnerWallet(
                    wallet_id=uuid.uuid4(),
                    **wallet_info,
                    is_active=True,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
                session.add(wallet)
                print(
                    f"  ✓ Added wallet {wallet_info['wallet_address'][:20]}... for partner"
                )

        await session.commit()
        print("  ✓ Partner wallets seeded")


async def seed_stake_events(
    chain_id: str,
    period_ids: list[uuid.UUID],
    validator_keys: list[str],
    provider_id: uuid.UUID,
) -> None:
    """Seed stake events for wallet lifecycle tracking.

    Args:
        chain_id: Chain identifier
        period_ids: List of period UUIDs
        validator_keys: List of validator keys
        provider_id: Provider UUID
    """
    print("\n11. Seeding Stake Events...")

    # Example stake events
    stake_events = []
    wallet_addresses = [
        "Stake11111111111111111111111111111111111111",
        "Stake22222222222222222222222222222222222222",
        "Stake33333333333333333333333333333333333333",
    ]

    async with async_session_factory() as session:
        for period_id in period_ids:
            for i, wallet_address in enumerate(wallet_addresses):
                validator_key = validator_keys[i % len(validator_keys)]

                # STAKE event at beginning of period
                stake_event_id = uuid.uuid4()
                event_timestamp = datetime.now(UTC) - timedelta(days=len(period_ids) - period_ids.index(period_id))

                stake_event = CanonicalStakeEvent(
                    stake_event_id=stake_event_id,
                    chain_id=chain_id,
                    period_id=period_id,
                    validator_key=validator_key,
                    staker_address=wallet_address,
                    event_type=StakeEventType.STAKE,
                    stake_amount_native=5000000000,  # 5 SOL in lamports
                    event_timestamp=event_timestamp,
                    source_provider_id=provider_id,
                    source_payload_id=None,
                    normalized_at=datetime.now(UTC),
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )

                # Check if event exists
                result = await session.execute(
                    select(CanonicalStakeEvent).where(
                        CanonicalStakeEvent.chain_id == chain_id,
                        CanonicalStakeEvent.period_id == period_id,
                        CanonicalStakeEvent.staker_address == wallet_address,
                        CanonicalStakeEvent.validator_key == validator_key,
                    )
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    session.add(stake_event)
                    stake_events.append(stake_event)

        await session.commit()
        print(f"  ✓ Seeded {len(stake_events)} stake events")


async def seed_staker_rewards(
    chain_id: str,
    period_ids: list[uuid.UUID],
    validator_keys: list[str],
    provider_id: uuid.UUID,
) -> None:
    """Seed per-staker rewards detail for wallet attribution.

    Args:
        chain_id: Chain identifier
        period_ids: List of period UUIDs
        validator_keys: List of validator keys
        provider_id: Provider UUID
    """
    print("\n12. Seeding Staker Rewards Detail...")

    wallet_addresses = [
        "Stake11111111111111111111111111111111111111",
        "Stake22222222222222222222222222222222222222",
        "Stake33333333333333333333333333333333333333",
    ]

    async with async_session_factory() as session:
        rewards_count = 0

        for period_id in period_ids:
            for i, wallet_address in enumerate(wallet_addresses):
                validator_key = validator_keys[i % len(validator_keys)]

                # Create rewards for different components
                components = [
                    ("MEV", 100000000),  # 0.1 SOL
                    ("BLOCK_REWARDS", 250000000),  # 0.25 SOL
                    ("CONSENSUS_REWARDS", 150000000),  # 0.15 SOL
                ]

                for component, reward_amount in components:
                    detail_id = uuid.uuid4()

                    reward_detail = CanonicalStakerRewardsDetail(
                        detail_id=detail_id,
                        chain_id=chain_id,
                        period_id=period_id,
                        validator_key=validator_key,
                        staker_address=wallet_address,
                        revenue_component=component,
                        reward_amount_native=reward_amount,
                        stake_amount_native=5000000000,  # 5 SOL stake
                        source_provider_id=provider_id,
                        source_payload_id=None,
                        normalized_at=datetime.now(UTC),
                        created_at=datetime.now(UTC),
                        updated_at=datetime.now(UTC),
                    )

                    # Check if reward detail exists
                    result = await session.execute(
                        select(CanonicalStakerRewardsDetail).where(
                            CanonicalStakerRewardsDetail.chain_id == chain_id,
                            CanonicalStakerRewardsDetail.period_id == period_id,
                            CanonicalStakerRewardsDetail.staker_address == wallet_address,
                            CanonicalStakerRewardsDetail.validator_key == validator_key,
                            CanonicalStakerRewardsDetail.revenue_component == component,
                        )
                    )
                    existing = result.scalar_one_or_none()

                    if not existing:
                        session.add(reward_detail)
                        rewards_count += 1

        await session.commit()
        print(f"  ✓ Seeded {rewards_count} staker reward details")


# ============================================================================
# Main Execution
# ============================================================================


async def main() -> None:
    """Main execution function."""
    print("\n" + "=" * 80)
    print("MVP Data Seeding Script")
    print("=" * 80 + "\n")

    try:
        # 1. Seed Chain
        chain_id = await seed_chain()

        # 2. Seed Provider
        provider_id = await seed_provider()

        # 3. Seed Admin User
        await seed_admin_user()

        # 4. Seed Validators
        validator_keys = await seed_validators(chain_id)

        # 5. Seed Partners
        partner_ids = await seed_partners()

        # 6. Seed Canonical Periods
        period_ids = await seed_canonical_periods(chain_id)

        # 7. Seed Agreements
        agreement_ids = await seed_agreements(partner_ids)

        # 8. Seed Agreement Versions
        await seed_agreement_versions(agreement_ids, partner_ids)

        # 9. Seed Agreement Rules
        await seed_agreement_rules(agreement_ids, validator_keys, chain_id)

        # 10. Seed Canonical Data (MEV + Fees)
        await seed_canonical_data(chain_id, period_ids, validator_keys, provider_id)

        # 11. Seed ValidatorPnL
        await seed_validator_pnl(chain_id, period_ids, validator_keys)

        # 12. Seed Partner Wallets
        await seed_partner_wallets(partner_ids, chain_id)

        # 13. Seed Stake Events
        await seed_stake_events(chain_id, period_ids, validator_keys, provider_id)

        # 14. Seed Staker Rewards Detail
        await seed_staker_rewards(chain_id, period_ids, validator_keys, provider_id)

        print("\n" + "=" * 80)
        print("✓ All data seeded successfully!")
        print("=" * 80)
        print("\nYou can now:")
        print("  - Login with username: admin, password: admin123")
        print("  - View validators, partners, agreements, and P&L data")
        print("  - Test commission calculations")
        print("  - Test wallet attribution with partner wallets")
        print("\nNote: This script is idempotent and can be run multiple times safely.")

    except Exception as e:
        print(f"\n❌ Error seeding data: {e!s}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
