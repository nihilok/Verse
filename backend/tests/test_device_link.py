"""Tests for device linking functionality."""

from datetime import UTC, datetime, timedelta

import pytest

from app.models.models import DeviceLinkCode, StandaloneChat, User
from app.services.device_link_service import DeviceLinkService
from app.services.insight_service import InsightService
from app.services.user_service import UserService


def test_generate_link_code(db, test_user):
    """Test generating a device link code."""
    service = DeviceLinkService()

    result = service.generate_link_code(db, test_user.id)

    assert "display_code" in result
    assert "expires_at" in result
    assert "qr_data" in result

    # Check display code format (XXXX-XXXX-XXXX)
    display_code = result["display_code"]
    assert len(display_code) == 14  # 12 chars + 2 dashes
    assert display_code.count("-") == 2
    parts = display_code.split("-")
    assert all(len(part) == 4 for part in parts)

    # Verify code was saved to database
    link_code = db.query(DeviceLinkCode).filter(DeviceLinkCode.display_code == display_code).first()

    assert link_code is not None
    assert link_code.source_user_id == test_user.id
    assert link_code.status == "pending"


def test_generate_link_code_rate_limiting(db, test_user):
    """Test rate limiting on link code generation."""
    service = DeviceLinkService()

    # Generate maximum allowed codes
    for _ in range(service.MAX_ACTIVE_CODES_PER_USER):
        service.generate_link_code(db, test_user.id)

    # Attempt to generate one more should fail
    with pytest.raises(ValueError, match="Too many active link codes"):
        service.generate_link_code(db, test_user.id)


def test_validate_and_use_code_success(db):
    """Test successfully validating and using a link code."""
    user_service = UserService()
    device_service = DeviceLinkService()

    # Create two users
    user1 = user_service.get_or_create_user(db)
    user2 = user_service.get_or_create_user(db)

    # User 1 generates a code
    result = device_service.generate_link_code(db, user1.id)
    display_code = result["display_code"]

    # User 2 uses the code
    link_result = device_service.validate_and_use_code(db, display_code, user2.id)

    assert link_result["success"] is True
    assert "new_anonymous_id" in link_result
    assert "message" in link_result

    # Verify code status was updated
    link_code = db.query(DeviceLinkCode).filter(DeviceLinkCode.display_code == display_code).first()

    assert link_code.status == "used"
    assert link_code.used_at is not None
    assert link_code.target_user_id is not None


def test_validate_code_expired(db, test_user):
    """Test that expired codes are rejected."""
    service = DeviceLinkService()

    # Generate a code
    result = service.generate_link_code(db, test_user.id)
    display_code = result["display_code"]

    # Manually expire the code
    link_code = db.query(DeviceLinkCode).filter(DeviceLinkCode.display_code == display_code).first()

    link_code.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db.commit()

    # Create second user
    user_service = UserService()
    user2 = user_service.get_or_create_user(db)

    # Attempt to use expired code
    with pytest.raises(ValueError, match="expired"):
        service.validate_and_use_code(db, display_code, user2.id)

    # Verify code status was updated to expired
    db.refresh(link_code)
    assert link_code.status == "expired"


def test_validate_code_already_used(db):
    """Test that already used codes are rejected."""
    user_service = UserService()
    device_service = DeviceLinkService()

    # Create three users
    user1 = user_service.get_or_create_user(db)
    user2 = user_service.get_or_create_user(db)
    user3 = user_service.get_or_create_user(db)

    # User 1 generates a code
    result = device_service.generate_link_code(db, user1.id)
    display_code = result["display_code"]

    # User 2 uses the code
    device_service.validate_and_use_code(db, display_code, user2.id)

    # User 3 attempts to use the same code
    with pytest.raises(ValueError, match="already been used"):
        device_service.validate_and_use_code(db, display_code, user3.id)


def test_validate_code_same_user(db, test_user):
    """Test that users cannot link to themselves."""
    service = DeviceLinkService()

    # Generate a code
    result = service.generate_link_code(db, test_user.id)
    display_code = result["display_code"]

    # Attempt to use own code
    with pytest.raises(ValueError, match="Cannot link device to itself"):
        service.validate_and_use_code(db, display_code, test_user.id)


def test_validate_code_invalid(db, test_user):
    """Test that invalid codes are rejected."""
    service = DeviceLinkService()

    # Attempt to use invalid code
    with pytest.raises(ValueError, match="Invalid link code"):
        service.validate_and_use_code(db, "INVALID-CODE-1234", test_user.id)


@pytest.mark.asyncio
async def test_merge_users_data_transfer(async_db):
    """Test that user data is correctly merged."""
    user_service = UserService()
    device_service = DeviceLinkService()
    insight_service = InsightService()

    # Create two users
    user1 = await user_service.get_or_create_user(async_db)
    user2 = await user_service.get_or_create_user(async_db)

    # Create a mock insight response
    class MockInsight:
        historical_context = "Historical context"
        theological_significance = "Theological significance"
        practical_application = "Practical application"

    # User 1 has some insights
    await insight_service.save_insight(
        async_db,
        passage_reference="John 3:16",
        passage_text="For God so loved the world",
        insights=MockInsight(),
        user_id=user1.id,
    )

    # User 2 has different insights
    await insight_service.save_insight(
        async_db,
        passage_reference="Romans 8:28",
        passage_text="And we know that in all things",
        insights=MockInsight(),
        user_id=user2.id,
    )

    # User 1 has a standalone chat
    chat1 = StandaloneChat(user_id=user1.id, title="User 1 Chat")
    async_db.add(chat1)
    await async_db.flush()

    # Merge users
    kept_user_id = await device_service.merge_users(async_db, user1.id, user2.id)

    # Get the kept user
    from sqlalchemy import select

    result = await async_db.execute(select(User).where(User.id == kept_user_id))
    kept_user = result.scalar_one_or_none()

    # Verify insights were merged
    kept_user_insights = await insight_service.get_user_insights(async_db, kept_user_id)
    assert len(kept_user_insights) == 2

    insight_refs = [i.passage_reference for i in kept_user_insights]
    assert "John 3:16" in insight_refs
    assert "Romans 8:28" in insight_refs

    # Verify standalone chats were transferred
    result = await async_db.execute(select(StandaloneChat).where(StandaloneChat.user_id == kept_user_id))
    chats = list(result.scalars().all())
    assert len(chats) == 1

    # Verify device count was updated
    assert kept_user.device_count == 2  # Sum of both users


def test_merge_users_keeps_higher_device_count(db):
    """Test that user with higher device_count is kept."""
    user_service = UserService()
    device_service = DeviceLinkService()

    # Create two users
    user1 = user_service.get_or_create_user(db)
    user2 = user_service.get_or_create_user(db)

    # Set different device counts
    user1.device_count = 3
    user2.device_count = 1
    db.commit()

    # Merge users
    kept_user_id = device_service.merge_users(db, user1.id, user2.id)

    # User 1 should be kept (higher device count)
    assert kept_user_id == user1.id

    # Verify device count is sum
    kept_user = db.query(User).filter(User.id == kept_user_id).first()
    assert kept_user.device_count == 4


@pytest.mark.asyncio
async def test_merge_users_no_duplicate_insights(async_db):
    """Test that shared insights are not duplicated during merge."""
    user_service = UserService()
    device_service = DeviceLinkService()
    insight_service = InsightService()

    # Create two users
    user1 = await user_service.get_or_create_user(async_db)
    user2 = await user_service.get_or_create_user(async_db)

    # Create a mock insight response
    class MockInsight:
        historical_context = "Historical context"
        theological_significance = "Theological significance"
        practical_application = "Practical application"

    # Both users have the same insight
    insight = await insight_service.save_insight(
        async_db,
        passage_reference="John 3:16",
        passage_text="For God so loved the world",
        insights=MockInsight(),
        user_id=user1.id,
    )

    # Link the same insight to user2
    await insight_service.link_insight_to_user(async_db, insight.id, user2.id)

    # Merge users
    kept_user_id = await device_service.merge_users(async_db, user1.id, user2.id)

    # Verify insight appears only once
    kept_user_insights = await insight_service.get_user_insights(async_db, kept_user_id)
    assert len(kept_user_insights) == 1
    assert kept_user_insights[0].id == insight.id


def test_create_or_update_device(db, test_user):
    """Test creating and updating device records."""
    service = DeviceLinkService()

    # Create a device
    device1 = service.create_or_update_device(
        db,
        user_id=test_user.id,
        device_name="My Phone",
        device_type="mobile",
        user_agent="Mozilla/5.0 (iPhone)",
    )

    assert device1.id is not None
    assert device1.device_name == "My Phone"
    assert device1.device_type == "mobile"

    # Update the same device (same user_agent)
    device2 = service.create_or_update_device(
        db,
        user_id=test_user.id,
        device_name="My iPhone",
        device_type="mobile",
        user_agent="Mozilla/5.0 (iPhone)",
    )

    # Should be the same device
    assert device1.id == device2.id
    assert device2.device_name == "My iPhone"


def test_get_user_devices(db, test_user):
    """Test retrieving user devices."""
    service = DeviceLinkService()

    # Create multiple devices
    service.create_or_update_device(db, test_user.id, "Phone", "mobile", "agent1")
    service.create_or_update_device(db, test_user.id, "Laptop", "desktop", "agent2")

    # Get devices
    devices = service.get_user_devices(db, test_user.id)

    assert len(devices) == 2
    assert any(d["device_name"] == "Phone" for d in devices)
    assert any(d["device_name"] == "Laptop" for d in devices)


def test_unlink_device(db, test_user):
    """Test unlinking a device."""
    service = DeviceLinkService()

    # Set device count to 2
    test_user.device_count = 2
    db.commit()

    # Create a device
    device = service.create_or_update_device(db, test_user.id, "Phone", "mobile", "agent1")

    # Unlink the device
    result = service.unlink_device(db, device.id, test_user.id)

    assert result["device_count"] == 1
    assert result["data_deleted"] is False
    assert result["should_clear_cookie"] is False

    # Verify device was deleted
    devices = service.get_user_devices(db, test_user.id)
    assert len(devices) == 0


def test_unlink_last_device_deletes_data(db, test_user):
    """Test that unlinking the last device deletes all user data."""
    service = DeviceLinkService()
    insight_service = InsightService()

    # Create a mock insight response
    class MockInsight:
        historical_context = "Historical context"
        theological_significance = "Theological significance"
        practical_application = "Practical application"

    # Add some insights
    insight_service.save_insight(
        db,
        passage_reference="John 3:16",
        passage_text="For God so loved the world",
        insights=MockInsight(),
        user_id=test_user.id,
    )

    # Create a device
    device = service.create_or_update_device(db, test_user.id, "Phone", "mobile", "agent1")

    # Unlink the last device
    result = service.unlink_device(db, device.id, test_user.id)

    assert result["device_count"] == 0
    assert result["data_deleted"] is True
    assert result["should_clear_cookie"] is True

    # Verify user was deleted
    deleted_user = db.query(User).filter(User.id == test_user.id).first()
    assert deleted_user is None


def test_unlink_device_wrong_user(db):
    """Test that users cannot unlink devices belonging to other users."""
    user_service = UserService()
    device_service = DeviceLinkService()

    # Create two users
    user1 = user_service.get_or_create_user(db)
    user2 = user_service.get_or_create_user(db)

    # Create a device for user1
    device = device_service.create_or_update_device(db, user1.id, "Phone", "mobile", "agent1")

    # User2 attempts to unlink user1's device
    with pytest.raises(ValueError, match="doesn't belong to user"):
        device_service.unlink_device(db, device.id, user2.id)


def test_cleanup_expired_codes(db, test_user):
    """Test cleanup of expired link codes."""
    service = DeviceLinkService()

    # Generate a code
    result = service.generate_link_code(db, test_user.id)
    display_code = result["display_code"]

    # Manually expire the code
    link_code = db.query(DeviceLinkCode).filter(DeviceLinkCode.display_code == display_code).first()

    link_code.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db.commit()

    # Run cleanup
    count = service.cleanup_expired_codes(db)

    assert count == 1

    # Verify code status
    db.refresh(link_code)
    assert link_code.status == "expired"


def test_revoke_user_codes(db, test_user):
    """Test revoking all pending codes for a user."""
    service = DeviceLinkService()

    # Generate multiple codes
    service.generate_link_code(db, test_user.id)
    service.generate_link_code(db, test_user.id)

    # Revoke all codes
    count = service.revoke_user_codes(db, test_user.id)

    assert count == 2

    # Verify codes were revoked
    codes = db.query(DeviceLinkCode).filter(DeviceLinkCode.source_user_id == test_user.id).all()

    assert all(code.status == "revoked" for code in codes)


@pytest.mark.asyncio
async def test_full_device_linking_workflow(async_db):
    """Test complete device linking workflow."""
    user_service = UserService()
    device_service = DeviceLinkService()
    insight_service = InsightService()

    # Create two users (representing two devices)
    user1 = await user_service.get_or_create_user(async_db)
    user2 = await user_service.get_or_create_user(async_db)

    # Create a mock insight response
    class MockInsight:
        historical_context = "Historical context"
        theological_significance = "Theological significance"
        practical_application = "Practical application"

    # User 1 has some data
    await insight_service.save_insight(
        async_db,
        passage_reference="John 3:16",
        passage_text="For God so loved the world",
        insights=MockInsight(),
        user_id=user1.id,
    )

    # User 2 has different data
    await insight_service.save_insight(
        async_db,
        passage_reference="Romans 8:28",
        passage_text="And we know that in all things",
        insights=MockInsight(),
        user_id=user2.id,
    )

    # User 1 generates a link code
    code_result = await device_service.generate_link_code(async_db, user1.id)
    display_code = code_result["display_code"]

    # User 2 uses the code to link devices
    link_result = await device_service.validate_and_use_code(async_db, display_code, user2.id)

    assert link_result["success"] is True

    # Get the merged user's anonymous_id
    merged_anonymous_id = link_result["new_anonymous_id"]

    # Verify both users' data is accessible under merged account
    merged_user = await user_service.get_user_by_anonymous_id(async_db, merged_anonymous_id)
    merged_insights = await insight_service.get_user_insights(async_db, merged_user.id)

    assert len(merged_insights) == 2
    insight_refs = [i.passage_reference for i in merged_insights]
    assert "John 3:16" in insight_refs
    assert "Romans 8:28" in insight_refs

    # Verify device count
    assert merged_user.device_count == 2
