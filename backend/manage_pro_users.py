#!/usr/bin/env python3
"""
Admin script to manage pro subscriptions for users.

Usage:
    python manage_pro_users.py add <anonymous_id>     # Add user to pro
    python manage_pro_users.py remove <anonymous_id>  # Remove user from pro
    python manage_pro_users.py list                   # List all pro users
    python manage_pro_users.py status <anonymous_id>  # Check user status
"""

import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.models import User, UserDevice


async def get_async_session():
    """Create an async database session."""
    settings = get_settings()
    # Convert psycopg2 URL to asyncpg URL
    db_url = settings.database_url
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("sqlite://"):
        db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    return async_session()


async def add_pro(anonymous_id: str):
    """Add a user and their linked devices to pro subscription."""
    async with await get_async_session() as db:
        # Find user by anonymous_id
        result = await db.execute(select(User).where(User.anonymous_id == anonymous_id))
        user = result.scalar_one_or_none()

        if not user:
            print(f"Error: User with anonymous_id '{anonymous_id}' not found")
            return False

        if user.pro_subscription:
            print(f"User '{anonymous_id}' is already a pro user")
            return True

        # Update user to pro
        user.pro_subscription = True
        await db.commit()

        # Get linked devices
        result = await db.execute(select(UserDevice).where(UserDevice.user_id == user.id))
        devices = result.scalars().all()

        print(f"Successfully added user '{anonymous_id}' to pro subscription")
        print(f"User ID: {user.id}")
        print(f"Linked devices: {len(devices)}")
        if devices:
            for device in devices:
                device_name = device.device_name or "Unnamed"
                device_type = device.device_type or "unknown"
                print(f"  - Device {device.id}: {device_name} ({device_type})")

        return True


async def remove_pro(anonymous_id: str):
    """Remove a user from pro subscription."""
    async with await get_async_session() as db:
        # Find user by anonymous_id
        result = await db.execute(select(User).where(User.anonymous_id == anonymous_id))
        user = result.scalar_one_or_none()

        if not user:
            print(f"Error: User with anonymous_id '{anonymous_id}' not found")
            return False

        if not user.pro_subscription:
            print(f"User '{anonymous_id}' is not a pro user")
            return True

        # Update user to free
        user.pro_subscription = False
        await db.commit()

        print(f"Successfully removed user '{anonymous_id}' from pro subscription")
        print(f"User ID: {user.id}")

        return True


async def list_pro_users():
    """List all pro users."""
    async with await get_async_session() as db:
        result = await db.execute(select(User).where(User.pro_subscription.is_(True)))
        users = result.scalars().all()

        if not users:
            print("No pro users found")
            return

        print(f"Found {len(users)} pro user(s):")
        print()

        for user in users:
            # Get linked devices
            result = await db.execute(select(UserDevice).where(UserDevice.user_id == user.id))
            devices = result.scalars().all()

            print(f"Anonymous ID: {user.anonymous_id}")
            print(f"  User ID: {user.id}")
            print(f"  Created: {user.created_at}")
            print(f"  Devices: {len(devices)}")
            if devices:
                for device in devices:
                    device_name = device.device_name or "Unnamed"
                    device_type = device.device_type or "unknown"
                    print(f"    - Device {device.id}: {device_name} ({device_type})")
            print()


async def check_status(anonymous_id: str):
    """Check user status and usage."""
    async with await get_async_session() as db:
        # Find user by anonymous_id
        result = await db.execute(select(User).where(User.anonymous_id == anonymous_id))
        user = result.scalar_one_or_none()

        if not user:
            print(f"Error: User with anonymous_id '{anonymous_id}' not found")
            return False

        # Get linked devices
        result = await db.execute(select(UserDevice).where(UserDevice.user_id == user.id))
        devices = result.scalars().all()

        print(f"User: {anonymous_id}")
        print(f"  User ID: {user.id}")
        print(f"  Created: {user.created_at}")
        print(f"  Pro Subscription: {'Yes' if user.pro_subscription else 'No'}")
        print(f"  Linked Devices: {len(devices)}")
        if devices:
            for device in devices:
                device_name = device.device_name or "Unnamed"
                device_type = device.device_type or "unknown"
                print(f"    - Device {device.id}: {device_name} ({device_type})")
                print(f"      Last Active: {device.last_active}")

        # Get usage information
        from datetime import UTC, datetime

        from app.models.models import UsageTracking

        today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await db.execute(
            select(UsageTracking).where(
                UsageTracking.user_id == user.id,
                UsageTracking.date == today,
            )
        )
        usage = result.scalar_one_or_none()

        if usage:
            print("\n  Today's Usage:")
            print(f"    LLM Calls: {usage.llm_calls}")
            if not user.pro_subscription:
                from app.services.usage_service import FREE_USER_DAILY_LIMIT

                print(f"    Remaining: {max(0, FREE_USER_DAILY_LIMIT - usage.llm_calls)}")
        else:
            print("\n  Today's Usage: 0 LLM calls")
            if not user.pro_subscription:
                from app.services.usage_service import FREE_USER_DAILY_LIMIT

                print(f"    Remaining: {FREE_USER_DAILY_LIMIT}")

        return True


def print_usage():
    """Print usage information."""
    print("Usage:")
    print("  python manage_pro_users.py add <anonymous_id>     # Add user to pro")
    print("  python manage_pro_users.py remove <anonymous_id>  # Remove user from pro")
    print("  python manage_pro_users.py list                   # List all pro users")
    print("  python manage_pro_users.py status <anonymous_id>  # Check user status")


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "add":
        if len(sys.argv) != 3:
            print("Error: Missing anonymous_id")
            print_usage()
            sys.exit(1)
        anonymous_id = sys.argv[2]
        success = await add_pro(anonymous_id)
        sys.exit(0 if success else 1)

    elif command == "remove":
        if len(sys.argv) != 3:
            print("Error: Missing anonymous_id")
            print_usage()
            sys.exit(1)
        anonymous_id = sys.argv[2]
        success = await remove_pro(anonymous_id)
        sys.exit(0 if success else 1)

    elif command == "list":
        await list_pro_users()
        sys.exit(0)

    elif command == "status":
        if len(sys.argv) != 3:
            print("Error: Missing anonymous_id")
            print_usage()
            sys.exit(1)
        anonymous_id = sys.argv[2]
        success = await check_status(anonymous_id)
        sys.exit(0 if success else 1)

    else:
        print(f"Error: Unknown command '{command}'")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
