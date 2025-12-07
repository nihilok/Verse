"""Schemas for Bible translations."""

from pydantic import BaseModel


class TranslationInfo(BaseModel):
    """Information about a Bible translation."""

    code: str
    name: str
    requires_pro: bool = False


class TranslationsResponse(BaseModel):
    """Response containing available translations."""

    translations: list[TranslationInfo]
