#!/usr/bin/env python3
"""Sync validators from ValidatorPnL to validators registry.

This utility script ensures that all validators present in the ValidatorPnL
table (computation data) are also registered in the validators table (registry).
This is useful when P&L data is imported but validators aren't yet registered.

Usage:
    poetry run python scripts/sync_validators_from_pnl.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select

from src.core.models.chains import Validator
from src.core.models.computation import ValidatorPnL
from src.db.session import async_session_factory


async def sync_validators() -> tuple[int, int]:
    """Sync validators from ValidatorPnL to validators registry.

    Returns:
        Tuple of (total_found, added_count)
    """
    async with async_session_factory() as session:
        # Get distinct validators from ValidatorPnL
        stmt = select(ValidatorPnL.validator_key, ValidatorPnL.chain_id).distinct()
        result = await session.execute(stmt)
        pnl_validators = result.fetchall()

        print(f"Found {len(pnl_validators)} validators in ValidatorPnL table")

        added_count = 0
        for row in pnl_validators:
            validator_key = row.validator_key
            chain_id = row.chain_id

            # Check if already exists in registry
            stmt = select(Validator).where(
                Validator.validator_key == validator_key,
                Validator.chain_id == chain_id,
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                # Add to registry
                validator = Validator(
                    validator_key=validator_key,
                    chain_id=chain_id,
                    description="Auto-imported from P&L data",
                    is_active=True,
                )
                session.add(validator)
                added_count += 1
                print(f"  + Added: {validator_key[:30]}... on {chain_id}")
            else:
                print(f"  - Exists: {validator_key[:30]}... on {chain_id}")

        await session.commit()
        return len(pnl_validators), added_count


async def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        total, added = await sync_validators()
        print(f"\n✅ Sync complete: {added}/{total} validators added to registry")
        return 0
    except Exception as e:
        print(f"\n❌ Sync failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
