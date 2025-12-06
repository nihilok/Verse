"""Tests for usage tracking functionality."""

import pytest
from datetime import UTC, datetime, timedelta

from app.models.models import User, UsageTracking
from app.services.usage_service import UsageService, FREE_USER_DAILY_LIMIT


@pytest.mark.asyncio
async def test_can_make_llm_call_new_user(async_db, async_test_user):
    """Test that a new user can make LLM calls."""
    usage_service = UsageService()
    can_call, current_usage, limit = await usage_service.can_make_llm_call(async_db, async_test_user.id)

    assert can_call is True
    assert current_usage == 0
    assert limit == FREE_USER_DAILY_LIMIT


@pytest.mark.asyncio
async def test_can_make_llm_call_pro_user(async_db, async_test_user):
    """Test that a pro user can always make LLM calls."""
    # Make user pro
    async_test_user.pro_subscription = True
    await async_db.commit()

    usage_service = UsageService()
    can_call, current_usage, limit = await usage_service.can_make_llm_call(async_db, async_test_user.id)

    assert can_call is True
    assert current_usage == 0
    assert limit == 0  # 0 means unlimited


@pytest.mark.asyncio
async def test_track_llm_call(async_db, async_test_user):
    """Test tracking LLM calls."""
    usage_service = UsageService()

    # Track first call
    await usage_service.track_llm_call(async_db, async_test_user.id)
    await async_db.commit()

    # Check that usage was tracked
    can_call, current_usage, limit = await usage_service.can_make_llm_call(async_db, async_test_user.id)
    assert current_usage == 1
    assert can_call is True

    # Track more calls
    for _ in range(5):
        await usage_service.track_llm_call(async_db, async_test_user.id)
        await async_db.commit()

    # Check usage
    can_call, current_usage, limit = await usage_service.can_make_llm_call(async_db, async_test_user.id)
    assert current_usage == 6
    assert can_call is True


@pytest.mark.asyncio
async def test_usage_limit_reached(async_db, async_test_user):
    """Test that users are blocked when they reach the daily limit."""
    usage_service = UsageService()

    # Track calls up to the limit
    for _ in range(FREE_USER_DAILY_LIMIT):
        await usage_service.track_llm_call(async_db, async_test_user.id)
        await async_db.commit()

    # Check that user has reached limit
    can_call, current_usage, limit = await usage_service.can_make_llm_call(async_db, async_test_user.id)
    assert current_usage == FREE_USER_DAILY_LIMIT
    assert can_call is False


@pytest.mark.asyncio
async def test_pro_user_unlimited_calls(async_db, async_test_user):
    """Test that pro users can make unlimited calls."""
    # Make user pro
    async_test_user.pro_subscription = True
    await async_db.commit()

    usage_service = UsageService()

    # Track many calls
    for _ in range(100):
        can_call, _, _ = await usage_service.can_make_llm_call(async_db, async_test_user.id)
        assert can_call is True
        await usage_service.track_llm_call(async_db, async_test_user.id)


@pytest.mark.asyncio
async def test_get_user_usage(async_db, async_test_user):
    """Test getting user usage information."""
    usage_service = UsageService()

    # Get usage for new user
    usage_info = await usage_service.get_user_usage(async_db, async_test_user.id)
    assert usage_info["is_pro"] is False
    assert usage_info["daily_limit"] == FREE_USER_DAILY_LIMIT
    assert usage_info["calls_today"] == 0
    assert usage_info["remaining"] == FREE_USER_DAILY_LIMIT

    # Track some calls
    for _ in range(3):
        await usage_service.track_llm_call(async_db, async_test_user.id)
        await async_db.commit()

    # Get usage again
    usage_info = await usage_service.get_user_usage(async_db, async_test_user.id)
    assert usage_info["calls_today"] == 3
    assert usage_info["remaining"] == FREE_USER_DAILY_LIMIT - 3


@pytest.mark.asyncio
async def test_get_user_usage_pro(async_db, async_test_user):
    """Test getting usage info for pro users."""
    # Make user pro
    async_test_user.pro_subscription = True
    await async_db.commit()

    usage_service = UsageService()
    usage_info = await usage_service.get_user_usage(async_db, async_test_user.id)

    assert usage_info["is_pro"] is True
    assert usage_info["daily_limit"] == 0  # 0 means unlimited
    assert usage_info["remaining"] == -1  # -1 means unlimited


@pytest.mark.asyncio
async def test_set_pro_subscription(async_db, async_test_user):
    """Test setting pro subscription status."""
    usage_service = UsageService()

    # Enable pro
    success = await usage_service.set_pro_subscription(async_db, async_test_user.id, True)
    assert success is True
    await async_db.commit()

    # Verify user is pro
    await async_db.refresh(async_test_user)
    assert async_test_user.pro_subscription is True

    # Disable pro
    success = await usage_service.set_pro_subscription(async_db, async_test_user.id, False)
    assert success is True
    await async_db.commit()

    # Verify user is not pro
    await async_db.refresh(async_test_user)
    assert async_test_user.pro_subscription is False


@pytest.mark.asyncio
async def test_set_pro_subscription_invalid_user(async_db):
    """Test setting pro subscription for non-existent user."""
    usage_service = UsageService()
    success = await usage_service.set_pro_subscription(async_db, 99999, True)
    assert success is False


@pytest.mark.asyncio
async def test_cleanup_old_usage_records(async_db, async_test_user):
    """Test cleaning up old usage records."""
    usage_service = UsageService()

    # Create old usage record (35 days ago)
    old_date = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=35)
    old_usage = UsageTracking(user_id=async_test_user.id, date=old_date, llm_calls=5)
    async_db.add(old_usage)

    # Create recent usage record (today)
    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    recent_usage = UsageTracking(user_id=async_test_user.id, date=today, llm_calls=3)
    async_db.add(recent_usage)

    await async_db.commit()

    # Clean up records older than 30 days
    deleted_count = await usage_service.cleanup_old_usage_records(async_db, days_to_keep=30)
    await async_db.commit()

    # Should have deleted 1 record
    assert deleted_count == 1

    # Verify recent record still exists
    from sqlalchemy import select

    result = await async_db.execute(
        select(UsageTracking).where(
            UsageTracking.user_id == async_test_user.id, UsageTracking.date == today
        )
    )
    remaining_usage = result.scalar_one_or_none()
    assert remaining_usage is not None
    assert remaining_usage.llm_calls == 3


@pytest.mark.asyncio
async def test_usage_tracking_unique_constraint(async_db, async_test_user):
    """Test that only one usage record exists per user per day."""
    usage_service = UsageService()
    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    # Track multiple calls on the same day
    for _ in range(5):
        await usage_service.track_llm_call(async_db, async_test_user.id)
        await async_db.commit()

    # Verify only one record exists for today
    from sqlalchemy import select, func

    result = await async_db.execute(
        select(func.count(UsageTracking.id)).where(
            UsageTracking.user_id == async_test_user.id, UsageTracking.date == today
        )
    )
    count = result.scalar()
    assert count == 1

    # Verify the count is correct
    result = await async_db.execute(
        select(UsageTracking).where(
            UsageTracking.user_id == async_test_user.id, UsageTracking.date == today
        )
    )
    usage = result.scalar_one()
    assert usage.llm_calls == 5
