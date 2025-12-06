"""Service for managing user LLM usage limits."""
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User, UsageTracking

# Daily limit for free users
FREE_USER_DAILY_LIMIT = 10


class UsageService:
    """Service for tracking and enforcing LLM usage limits."""

    @staticmethod
    async def can_make_llm_call(db: AsyncSession, user_id: int) -> tuple[bool, int, int]:
        """
        Check if a user can make an LLM call.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Tuple of (can_call, current_usage, limit)
            - can_call: True if user can make a call
            - current_usage: Number of calls made today
            - limit: Daily limit (0 means unlimited for pro users)
        """
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return False, 0, FREE_USER_DAILY_LIMIT

        # Pro users have unlimited access
        if user.pro_subscription:
            return True, 0, 0

        # Get today's date (start of day in UTC)
        today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        # Get or create usage tracking for today
        result = await db.execute(
            select(UsageTracking).where(
                UsageTracking.user_id == user_id,
                UsageTracking.date == today,
            )
        )
        usage = result.scalar_one_or_none()

        if not usage:
            # No usage record for today, user can make a call
            return True, 0, FREE_USER_DAILY_LIMIT

        # Check if under limit
        can_call = usage.llm_calls < FREE_USER_DAILY_LIMIT
        return can_call, usage.llm_calls, FREE_USER_DAILY_LIMIT

    @staticmethod
    async def track_llm_call(db: AsyncSession, user_id: int) -> None:
        """
        Track an LLM call for a user.

        Args:
            db: Database session
            user_id: User ID
        """
        # Get today's date (start of day in UTC)
        today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        # Get or create usage tracking for today
        result = await db.execute(
            select(UsageTracking).where(
                UsageTracking.user_id == user_id,
                UsageTracking.date == today,
            )
        )
        usage = result.scalar_one_or_none()

        if not usage:
            # Create new usage record
            usage = UsageTracking(user_id=user_id, date=today, llm_calls=1)
            db.add(usage)
        else:
            # Increment existing usage
            usage.llm_calls += 1

        await db.flush()

    @staticmethod
    async def get_user_usage(db: AsyncSession, user_id: int) -> dict:
        """
        Get current usage information for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Dictionary with usage information
        """
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return {
                "is_pro": False,
                "daily_limit": FREE_USER_DAILY_LIMIT,
                "calls_today": 0,
                "remaining": FREE_USER_DAILY_LIMIT,
            }

        # Pro users have unlimited access
        if user.pro_subscription:
            return {
                "is_pro": True,
                "daily_limit": 0,  # 0 means unlimited
                "calls_today": 0,
                "remaining": -1,  # -1 means unlimited
            }

        # Get today's date (start of day in UTC)
        today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        # Get usage tracking for today
        result = await db.execute(
            select(UsageTracking).where(
                UsageTracking.user_id == user_id,
                UsageTracking.date == today,
            )
        )
        usage = result.scalar_one_or_none()

        calls_today = usage.llm_calls if usage else 0
        remaining = max(0, FREE_USER_DAILY_LIMIT - calls_today)

        return {
            "is_pro": False,
            "daily_limit": FREE_USER_DAILY_LIMIT,
            "calls_today": calls_today,
            "remaining": remaining,
        }

    @staticmethod
    async def set_pro_subscription(db: AsyncSession, user_id: int, is_pro: bool) -> bool:
        """
        Set the pro subscription status for a user.

        Args:
            db: Database session
            user_id: User ID
            is_pro: True to enable pro, False to disable

        Returns:
            True if successful, False if user not found
        """
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return False

        user.pro_subscription = is_pro
        await db.flush()
        return True

    @staticmethod
    async def cleanup_old_usage_records(db: AsyncSession, days_to_keep: int = 30) -> int:
        """
        Clean up old usage tracking records.

        Args:
            db: Database session
            days_to_keep: Number of days of records to keep

        Returns:
            Number of records deleted
        """
        cutoff_date = datetime.now(UTC) - timedelta(days=days_to_keep)

        result = await db.execute(
            UsageTracking.__table__.delete().where(UsageTracking.date < cutoff_date)
        )

        return result.rowcount
