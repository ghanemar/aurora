"""Script to create an admin user for testing.

This script creates an admin user with default credentials:
- Username: admin
- Password: admin123
- Email: admin@aurora.local
"""

import asyncio
import sys
import uuid
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from src.config.settings import get_settings
from src.core.models import User
from src.core.models.users import UserRole
from src.core.security import hash_password
from src.db.session import async_session_factory


async def create_admin_user() -> None:
    """Create an admin user in the database."""
    async with async_session_factory() as session:
        # Check if admin user already exists
        stmt = select(User).where(User.username == "admin")
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("Admin user already exists!")
            print(f"  Username: {existing_user.username}")
            print(f"  Email: {existing_user.email}")
            print(f"  Role: {existing_user.role.value}")
            return

        # Create new admin user
        admin_user = User(
            id=uuid.uuid4(),
            username="admin",
            email="admin@aurora.local",
            hashed_password=hash_password("admin123"),
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True,
            partner_id=None,
        )

        session.add(admin_user)
        await session.commit()

        print("Admin user created successfully!")
        print(f"  Username: {admin_user.username}")
        print(f"  Email: {admin_user.email}")
        print(f"  Password: admin123")
        print(f"  Role: {admin_user.role.value}")


if __name__ == "__main__":
    asyncio.run(create_admin_user())
