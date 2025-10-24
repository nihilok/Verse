from abc import ABC, abstractmethod
from typing import Optional
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


class AIClient(ABC):
    """Abstract base class for AI insight providers."""
    
    @abstractmethod
    async def generate_insights(
        self, 
        request: InsightRequest
    ) -> Optional[InsightResponse]:
        """Generate insights for a Bible passage."""
        pass
