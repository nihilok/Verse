import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select

from app.models.models import ChatMessage, DeviceLinkCode, StandaloneChat, User, UserDevice, user_insights
from app.services.user_service import UserService


class DeviceLinkService:
    """Service for managing device linking and user account merging."""

    LINK_CODE_EXPIRY_MINUTES = 5
    MAX_ACTIVE_CODES_PER_USER = 3
    DISPLAY_CODE_LENGTH = 12

    # Characters for display code (excluding ambiguous characters: 0, O, I, 1, l)
    DISPLAY_CODE_CHARS = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"

    def __init__(self):
        self.user_service = UserService()

    def _generate_display_code(self) -> str:
        """Generate a user-friendly 12-character display code in format XXXX-XXXX-XXXX"""
        code_chars = "".join(secrets.choice(self.DISPLAY_CODE_CHARS) for _ in range(self.DISPLAY_CODE_LENGTH))
        # Format as XXXX-XXXX-XXXX
        return f"{code_chars[0:4]}-{code_chars[4:8]}-{code_chars[8:12]}"

    def _hash_code(self, code: str) -> str:
        """Hash a code using SHA256"""
        return hashlib.sha256(code.encode()).hexdigest()

    async def generate_link_code(self, db, user_id: int, device_id: int | None = None) -> dict[str, Any]:
        """
        Generate a new linking code for a user.

        Args:
            db: Database session
            user_id: User ID
            device_id: Optional device ID

        Returns:
            Dictionary with display_code, expires_at, and qr_data

        Raises:
            ValueError: If rate limit exceeded
        """
        # Check rate limiting - count active codes
        from sqlalchemy import func

        result = await db.execute(
            select(func.count())
            .select_from(DeviceLinkCode)
            .where(
                DeviceLinkCode.source_user_id == user_id,
                DeviceLinkCode.status == "pending",
                DeviceLinkCode.expires_at > datetime.now(UTC),
            )
        )
        active_codes = result.scalar()

        if active_codes >= self.MAX_ACTIVE_CODES_PER_USER:
            raise ValueError(f"Too many active link codes. Maximum {self.MAX_ACTIVE_CODES_PER_USER} allowed.")

        # Generate secure random token
        token = secrets.token_urlsafe(32)
        hashed_code = self._hash_code(token)

        # Generate user-friendly display code
        display_code = self._generate_display_code()

        # Ensure display code is unique
        max_attempts = 10
        for _ in range(max_attempts):
            result = await db.execute(
                select(DeviceLinkCode).where(DeviceLinkCode.display_code == display_code)
            )
            existing = result.scalar_one_or_none()
            if not existing:
                break
            display_code = self._generate_display_code()

        # Calculate expiration
        expires_at = datetime.now(UTC) + timedelta(minutes=self.LINK_CODE_EXPIRY_MINUTES)

        # Create link code record
        link_code = DeviceLinkCode(
            code=hashed_code,
            display_code=display_code,
            source_user_id=user_id,
            source_device_id=device_id,
            expires_at=expires_at,
            status="pending",
        )

        db.add(link_code)
        await db.flush()
        await db.refresh(link_code)

        return {
            "display_code": display_code,
            "expires_at": expires_at.isoformat(),
            "qr_data": display_code,  # QR code will encode the display code
        }

    async def validate_and_use_code(
        self, db, display_code: str, target_user_id: int, target_device_id: int | None = None
    ) -> dict[str, Any]:
        """
        Validate a linking code and perform device linking.

        Args:
            db: Database session
            display_code: The display code to validate
            target_user_id: User ID attempting to link
            target_device_id: Optional device ID

        Returns:
            Dictionary with success status and merged user info

        Raises:
            ValueError: If code is invalid, expired, or already used
        """
        # Find code by display_code
        result = await db.execute(
            select(DeviceLinkCode).where(DeviceLinkCode.display_code == display_code.upper().strip())
        )
        link_code = result.scalar_one_or_none()

        if not link_code:
            raise ValueError("Invalid link code")

        # Check if same user
        if link_code.source_user_id == target_user_id:
            raise ValueError("Cannot link device to itself")

        # Check expiration
        now = datetime.now(UTC)
        # Make expires_at timezone-aware if it isn't already
        expires_at = link_code.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= now:
            # Mark as expired
            link_code.status = "expired"
            await db.flush()
            raise ValueError("This code has expired. Please generate a new one.")

        # Check status
        if link_code.status != "pending":
            if link_code.status == "used":
                raise ValueError("This code has already been used")
            elif link_code.status == "expired":
                raise ValueError("This code has expired")
            elif link_code.status == "revoked":
                raise ValueError("This code has been revoked")
            else:
                raise ValueError("Invalid code status")

        # Mark as used
        link_code.status = "used"
        link_code.used_at = now
        link_code.target_user_id = target_user_id
        link_code.target_device_id = target_device_id

        # Merge users
        kept_user_id = await self.merge_users(db, link_code.source_user_id, target_user_id)

        # Get the kept user's anonymous_id
        result = await db.execute(select(User).where(User.id == kept_user_id))
        kept_user = result.scalar_one_or_none()

        return {
            "success": True,
            "new_anonymous_id": kept_user.anonymous_id,
            "message": "Devices linked successfully",
        }

    async def merge_users(self, db, source_user_id: int, target_user_id: int) -> int:
        """
        Merge two users' data (union merge).

        Args:
            db: Database session
            source_user_id: Source user ID
            target_user_id: Target user ID

        Returns:
            ID of the kept user
        """
        from sqlalchemy import update

        # Get both users
        result = await db.execute(select(User).where(User.id == source_user_id))
        source_user = result.scalar_one_or_none()
        result = await db.execute(select(User).where(User.id == target_user_id))
        target_user = result.scalar_one_or_none()

        if not source_user or not target_user:
            raise ValueError("User not found")

        # Determine which user to keep (higher device_count, or newer if equal)
        if source_user.device_count > target_user.device_count:
            kept_user = source_user
            deleted_user = target_user
        elif target_user.device_count > source_user.device_count:
            kept_user = target_user
            deleted_user = source_user
        else:
            # Equal device counts, keep newer user
            if source_user.created_at > target_user.created_at:
                kept_user = source_user
                deleted_user = target_user
            else:
                kept_user = target_user
                deleted_user = source_user

        kept_user_id = kept_user.id
        deleted_user_id = deleted_user.id

        # Merge insights (many-to-many) - transfer user_insights links
        stmt = select(user_insights).where(user_insights.c.user_id == deleted_user_id)
        result = await db.execute(stmt)
        deleted_user_insights = result.all()

        for insight_link in deleted_user_insights:
            insight_id = insight_link.insight_id
            # Check if kept user already has this insight linked
            result = await db.execute(
                select(user_insights).where(
                    user_insights.c.user_id == kept_user_id, user_insights.c.insight_id == insight_id
                )
            )
            existing = result.first()

            if not existing:
                # Create new link for kept user
                await db.execute(user_insights.insert().values(user_id=kept_user_id, insight_id=insight_id))

        # Merge chat messages (one-to-many) - update user_id
        await db.execute(
            update(ChatMessage).where(ChatMessage.user_id == deleted_user_id).values(user_id=kept_user_id)
        )

        # Merge standalone chats (one-to-many) - update user_id
        await db.execute(
            update(StandaloneChat)
            .where(StandaloneChat.user_id == deleted_user_id)
            .values(user_id=kept_user_id)
        )

        # Transfer devices - update user_id
        await db.execute(
            update(UserDevice).where(UserDevice.user_id == deleted_user_id).values(user_id=kept_user_id)
        )

        # Update device count
        kept_user.device_count = source_user.device_count + target_user.device_count

        # Delete old user_insights links for deleted user (already transferred)
        await db.execute(user_insights.delete().where(user_insights.c.user_id == deleted_user_id))

        # Delete the deleted user (CASCADE will handle relationships)
        await db.delete(deleted_user)

        await db.flush()

        return kept_user_id

    async def get_user_devices(self, db, user_id: int) -> list[dict[str, Any]]:
        """
        Get all devices for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of device dictionaries
        """
        result = await db.execute(
            select(UserDevice).where(UserDevice.user_id == user_id).order_by(UserDevice.last_active.desc())
        )
        devices = result.scalars().all()

        return [
            {
                "id": device.id,
                "device_name": device.device_name,
                "device_type": device.device_type,
                "user_agent": device.user_agent,
                "created_at": device.created_at.isoformat() if device.created_at else None,
                "last_active": device.last_active.isoformat() if device.last_active else None,
            }
            for device in devices
        ]

    async def unlink_device(self, db, device_id: int, user_id: int) -> dict[str, Any]:
        """
        Unlink a specific device from user account.

        Args:
            db: Database session
            device_id: Device ID to unlink
            user_id: User ID (for verification)

        Returns:
            Dictionary with device_count and deletion info

        Raises:
            ValueError: If device doesn't belong to user
        """
        # Verify device belongs to user
        result = await db.execute(
            select(UserDevice).where(UserDevice.id == device_id, UserDevice.user_id == user_id)
        )
        device = result.scalar_one_or_none()

        if not device:
            raise ValueError("Device not found or doesn't belong to user")

        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        # Decrement device count
        user.device_count -= 1

        # Delete device record
        await db.delete(device)

        # If this was the last device, delete all user data
        data_deleted = False
        if user.device_count == 0:
            # Delete all user data
            await self.user_service.clear_user_data(db, user_id)
            # Delete user record
            await db.delete(user)
            data_deleted = True

        return {
            "device_count": user.device_count if not data_deleted else 0,
            "data_deleted": data_deleted,
            "should_clear_cookie": data_deleted,
            "message": (
                "Device unlinked successfully"
                if not data_deleted
                else "Last device unlinked and data deleted"
            ),
        }

    async def create_or_update_device(
        self,
        db,
        user_id: int,
        device_name: str | None = None,
        device_type: str | None = None,
        user_agent: str | None = None,
    ) -> UserDevice:
        """
        Create or update a device record.

        Args:
            db: Database session
            user_id: User ID
            device_name: Optional device name
            device_type: Optional device type
            user_agent: Optional user agent string

        Returns:
            UserDevice instance
        """
        # Try to find existing device by user_agent
        device = None
        if user_agent:
            result = await db.execute(
                select(UserDevice).where(UserDevice.user_id == user_id, UserDevice.user_agent == user_agent)
            )
            device = result.scalar_one_or_none()

        if device:
            # Update last_active
            device.last_active = datetime.now(UTC)
            if device_name:
                device.device_name = device_name
            if device_type:
                device.device_type = device_type
        else:
            # Create new device
            device = UserDevice(
                user_id=user_id,
                device_name=device_name,
                device_type=device_type or "unknown",
                user_agent=user_agent,
            )
            db.add(device)

        await db.flush()
        await db.refresh(device)

        return device

    async def cleanup_expired_codes(self, db) -> int:
        """
        Mark expired codes as expired (can be run as background task).

        Args:
            db: Database session

        Returns:
            Number of codes marked as expired
        """
        from sqlalchemy import update

        now = datetime.now(UTC)

        result = await db.execute(
            update(DeviceLinkCode)
            .where(DeviceLinkCode.status == "pending", DeviceLinkCode.expires_at <= now)
            .values(status="expired")
        )

        return result.rowcount

    async def revoke_user_codes(self, db, user_id: int) -> int:
        """
        Revoke all pending link codes for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Number of codes revoked
        """
        from sqlalchemy import update

        result = await db.execute(
            update(DeviceLinkCode)
            .where(DeviceLinkCode.source_user_id == user_id, DeviceLinkCode.status == "pending")
            .values(status="revoked")
        )

        return result.rowcount
