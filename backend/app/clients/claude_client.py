import anthropic
from typing import Optional, List
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
                model="claude-sonnet-4-5-20250929",
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
    
    async def generate_chat_response(
        self,
        user_message: str,
        passage_text: str,
        passage_reference: str,
        insight_context: dict,
        chat_history: List
    ) -> Optional[str]:
        """
        Generate a chat response using Claude with conversation context.
        
        Args:
            user_message: The user's question
            passage_text: The Bible passage text
            passage_reference: The Bible passage reference
            insight_context: Dict with historical_context, theological_significance, practical_application
            chat_history: List of previous ChatMessage objects
            
        Returns:
            The AI's response text
        """
        try:
            # Truncate passage text if too long to avoid token limits
            # Claude has a context window, so we limit each field to reasonable size
            max_text_length = 2000
            truncated_passage = passage_text[:max_text_length] + ("..." if len(passage_text) > max_text_length else "")
            truncated_reference = passage_reference[:200]  # References should be short
            
            # Build the system message with context
            system_prompt = f"""You are a knowledgeable biblical scholar and theologian having a conversation about a Bible passage. 

Passage Reference: {truncated_reference}
Passage Text: {truncated_passage}

You previously provided these insights:
- Historical Context: {insight_context.get('historical_context', '')[:1000]}
- Theological Significance: {insight_context.get('theological_significance', '')[:1000]}
- Practical Application: {insight_context.get('practical_application', '')[:1000]}

Continue the conversation by answering the user's questions thoughtfully and in depth. Draw from biblical scholarship, theology, and practical wisdom. Keep your responses focused and relevant to the passage and previous insights."""

            # Build conversation messages
            messages = []
            
            # Add chat history
            for msg in chat_history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Generate response
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2000,
                system=system_prompt,
                messages=messages
            )
            
            return response.content[0].text
        except Exception as e:
            print(f"Error generating chat response: {e}")
            return None
