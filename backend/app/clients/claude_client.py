import anthropic
import logging
from typing import Optional, List
from app.clients.ai_client import AIClient, InsightRequest, InsightResponse, DefinitionRequest, DefinitionResponse
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ClaudeAIClient(AIClient):
    """Implementation of AIClient using Anthropic's Claude."""

    # API Configuration Constants
    API_TIMEOUT_SECONDS = 30.0
    MODEL_NAME = "claude-sonnet-4-5-20250929"

    # Token Limits for Different Operations
    MAX_TOKENS_INSIGHTS = 1500  # For generating biblical insights
    MAX_TOKENS_DEFINITION = 1000  # For word definitions
    MAX_TOKENS_CHAT = 2000  # For chat responses

    # Text Truncation Limits (to avoid token limits)
    MAX_PASSAGE_TEXT_LENGTH = 2000  # Maximum passage text length in characters
    MAX_REFERENCE_LENGTH = 200  # Maximum reference string length
    MAX_CONTEXT_LENGTH = 1000  # Maximum length for each insight context field

    def __init__(self):
        settings = get_settings()
        self.client = anthropic.Anthropic(
            api_key=settings.anthropic_api_key,
            timeout=self.API_TIMEOUT_SECONDS
        )
    
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
                model=self.MODEL_NAME,
                max_tokens=self.MAX_TOKENS_INSIGHTS,
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
            logger.error(f"Error generating insights: {e}", exc_info=True)
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
    
    async def generate_definition(
        self,
        request: DefinitionRequest
    ) -> Optional[DefinitionResponse]:
        """Generate a definition for a word in context using Claude."""
        try:
            prompt = f"""You are a biblical scholar and linguist. Define the following word in its biblical context.

Word: {request.word}
Verse Reference: {request.passage_reference}
Full Verse: {request.verse_text}

Please provide:
1. Definition: A clear definition of this word as used in this specific biblical context
2. Biblical Usage: How this word is used throughout the Bible and its significance in Scripture
3. Original Language: Information about the original Hebrew/Greek word, its transliteration, and any nuances in meaning

Format your response as follows:
DEFINITION: [your definition]
BIBLICAL_USAGE: [your analysis of biblical usage]
ORIGINAL_LANGUAGE: [original language information]
"""
            
            message = self.client.messages.create(
                model=self.MODEL_NAME,
                max_tokens=self.MAX_TOKENS_DEFINITION,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse the response
            content = message.content[0].text
            definition_parts = self._parse_definition(content)
            
            return DefinitionResponse(
                definition=definition_parts.get("definition", ""),
                biblical_usage=definition_parts.get("biblical_usage", ""),
                original_language=definition_parts.get("original_language", "")
            )
        except Exception as e:
            logger.error(f"Error generating definition: {e}", exc_info=True)
            return None
    
    def _parse_definition(self, content: str) -> dict:
        """Parse the structured definition response from Claude."""
        definition_parts = {
            "definition": "",
            "biblical_usage": "",
            "original_language": ""
        }
        
        # Split by the markers
        parts = content.split("DEFINITION:")
        if len(parts) > 1:
            remaining = parts[1]
            usage_parts = remaining.split("BIBLICAL_USAGE:")
            if len(usage_parts) > 1:
                definition_parts["definition"] = usage_parts[0].strip()
                remaining = usage_parts[1]
                
                lang_parts = remaining.split("ORIGINAL_LANGUAGE:")
                if len(lang_parts) > 1:
                    definition_parts["biblical_usage"] = lang_parts[0].strip()
                    definition_parts["original_language"] = lang_parts[1].strip()
                else:
                    definition_parts["biblical_usage"] = remaining.strip()
        
        return definition_parts
    
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
            truncated_passage = passage_text[:self.MAX_PASSAGE_TEXT_LENGTH] + (
                "..." if len(passage_text) > self.MAX_PASSAGE_TEXT_LENGTH else ""
            )
            truncated_reference = passage_reference[:self.MAX_REFERENCE_LENGTH]

            # Build the system message with context
            system_prompt = f"""You are a knowledgeable biblical scholar and theologian having a conversation about a Bible passage.

Passage Reference: {truncated_reference}
Passage Text: {truncated_passage}

You previously provided these insights:
- Historical Context: {insight_context.get('historical_context', '')[:self.MAX_CONTEXT_LENGTH]}
- Theological Significance: {insight_context.get('theological_significance', '')[:self.MAX_CONTEXT_LENGTH]}
- Practical Application: {insight_context.get('practical_application', '')[:self.MAX_CONTEXT_LENGTH]}

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
                model=self.MODEL_NAME,
                max_tokens=self.MAX_TOKENS_CHAT,
                system=system_prompt,
                messages=messages
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error generating chat response: {e}", exc_info=True)
            return None
    
    async def generate_standalone_chat_response(
        self,
        user_message: str,
        passage_text: Optional[str] = None,
        passage_reference: Optional[str] = None,
        chat_history: List = None
    ) -> Optional[str]:
        """
        Generate a chat response for standalone chats (not linked to insights).
        
        Args:
            user_message: The user's question
            passage_text: Optional Bible passage text for context
            passage_reference: Optional Bible passage reference
            chat_history: List of previous StandaloneChatMessage objects
            
        Returns:
            The AI's response text
        """
        if chat_history is None:
            chat_history = []
        
        try:
            # Build the system message
            system_prompt = """You are a knowledgeable biblical scholar and theologian having a conversation. 
Answer questions about the Bible, theology, and faith thoughtfully and in depth. Draw from biblical scholarship, 
theology, and practical wisdom."""
            
            # If there's a passage, add it to the system prompt
            if passage_text and passage_reference:
                truncated_passage = passage_text[:self.MAX_PASSAGE_TEXT_LENGTH] + (
                    "..." if len(passage_text) > self.MAX_PASSAGE_TEXT_LENGTH else ""
                )
                truncated_reference = passage_reference[:self.MAX_REFERENCE_LENGTH]

                system_prompt = f"""You are a knowledgeable biblical scholar and theologian having a conversation about a Bible passage.

Passage Reference: {truncated_reference}
Passage Text: {truncated_passage}

Answer questions thoughtfully and in depth. Draw from biblical scholarship, theology, and practical wisdom."""
            
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
                model=self.MODEL_NAME,
                max_tokens=self.MAX_TOKENS_CHAT,
                system=system_prompt,
                messages=messages
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error generating standalone chat response: {e}", exc_info=True)
            return None
