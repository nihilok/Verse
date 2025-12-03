from abc import ABC, abstractmethod

from pydantic import BaseModel


class InsightRequest(BaseModel):
    """Model for insight request."""

    passage_text: str
    passage_reference: str


class InsightResponse(BaseModel):
    """Model for AI-generated insights."""

    historical_context: str
    theological_significance: str
    practical_application: str


class DefinitionRequest(BaseModel):
    """Model for definition request."""

    word: str
    verse_text: str  # The full verse text with the word marked
    passage_reference: str  # e.g., "John 3:16"


class DefinitionResponse(BaseModel):
    """Model for AI-generated word definition."""

    definition: str
    biblical_usage: str
    original_language: str


class AIClient(ABC):
    """Abstract base class for AI insight providers."""

    @abstractmethod
    async def generate_insights(self, request: InsightRequest) -> InsightResponse | None:
        """Generate insights for a Bible passage."""
        pass

    @abstractmethod
    async def generate_definition(self, request: DefinitionRequest) -> DefinitionResponse | None:
        """Generate a definition for a word in context."""
        pass
