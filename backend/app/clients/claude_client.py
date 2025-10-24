import anthropic
from typing import Optional
from app.clients.ai_client import AIClient, InsightRequest, InsightResponse
from app.core.config import get_settings


class ClaudeAIClient(AIClient):
    """Implementation of AIClient using Anthropic's Claude."""
    
    def __init__(self):
        settings = get_settings()
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    
    async def generate_insights(
        self, 
        request: InsightRequest
    ) -> Optional[InsightResponse]:
        """Generate insights using Claude."""
        try:
            prompt = f"""You are a biblical scholar and theologian. Analyze the following Bible passage and provide insights in three categories:

Passage Reference: {request.passage_reference}
Passage Text: {request.passage_text}

Please provide:
1. Historical Context: The historical background, cultural setting, and when/why this was written
2. Theological Significance: The theological themes, doctrines, and spiritual meaning
3. Practical Application: How this passage applies to modern life and practical ways to apply its teachings

Format your response as follows:
HISTORICAL_CONTEXT: [your analysis]
THEOLOGICAL_SIGNIFICANCE: [your analysis]
PRACTICAL_APPLICATION: [your analysis]
"""
            
            message = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse the response
            content = message.content[0].text
            insights = self._parse_insights(content)
            
            return InsightResponse(
                historical_context=insights.get("historical_context", ""),
                theological_significance=insights.get("theological_significance", ""),
                practical_application=insights.get("practical_application", "")
            )
        except Exception as e:
            print(f"Error generating insights: {e}")
            return None
    
    def _parse_insights(self, content: str) -> dict:
        """Parse the structured response from Claude."""
        insights = {
            "historical_context": "",
            "theological_significance": "",
            "practical_application": ""
        }
        
        # Split by the markers
        parts = content.split("HISTORICAL_CONTEXT:")
        if len(parts) > 1:
            remaining = parts[1]
            theo_parts = remaining.split("THEOLOGICAL_SIGNIFICANCE:")
            if len(theo_parts) > 1:
                insights["historical_context"] = theo_parts[0].strip()
                remaining = theo_parts[1]
                
                prac_parts = remaining.split("PRACTICAL_APPLICATION:")
                if len(prac_parts) > 1:
                    insights["theological_significance"] = prac_parts[0].strip()
                    insights["practical_application"] = prac_parts[1].strip()
                else:
                    insights["theological_significance"] = remaining.strip()
        
        return insights
