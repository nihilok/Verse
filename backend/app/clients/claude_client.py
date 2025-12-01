import anthropic
import logging
from typing import Optional, List, AsyncGenerator, Tuple
from app.clients.ai_client import AIClient, InsightRequest, InsightResponse, DefinitionRequest, DefinitionResponse
from app.core.config import get_settings
from app.prompts import (
    build_insights_prompt,
    build_definition_prompt,
    build_chat_system_prompt,
    build_standalone_chat_system_prompt,
)

logger = logging.getLogger(__name__)


class ClaudeAIClient(AIClient):
    """Implementation of AIClient using Anthropic's Claude."""

    # API Configuration Constants
    API_TIMEOUT_SECONDS = 30.0
    MODEL_NAME = "claude-sonnet-4-5-20250929"

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
        # Token limits from settings (configurable via environment variables)
        self.MAX_TOKENS_INSIGHTS = settings.max_tokens_insights
        self.MAX_TOKENS_DEFINITION = settings.max_tokens_definition
        self.MAX_TOKENS_CHAT = settings.max_tokens_chat

    def _build_conversation_messages(
        self,
        user_message: str,
        chat_history: List
    ) -> List[dict]:
        """
        Build conversation messages from chat history and current message.

        Args:
            user_message: The current user's message
            chat_history: List of previous message objects

        Returns:
            List of message dicts formatted for Claude API
        """
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

        return messages

    async def generate_insights(
        self, 
        request: InsightRequest
    ) -> Optional[InsightResponse]:
        """Generate insights using Claude."""
        try:
            prompt = build_insights_prompt(
                passage_reference=request.passage_reference,
                passage_text=request.passage_text
            )
            
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
            prompt = build_definition_prompt(
                word=request.word,
                passage_reference=request.passage_reference,
                verse_text=request.verse_text
            )
            
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
        chat_history: List,
        rag_context: str = ""
    ) -> Optional[str]:
        """
        Generate a chat response using Claude with conversation context.

        Args:
            user_message: The user's question
            passage_text: The Bible passage text
            passage_reference: The Bible passage reference
            insight_context: Dict with historical_context, theological_significance, practical_application
            chat_history: List of previous ChatMessage objects
            rag_context: Formatted RAG context string from RagService (optional)

        Returns:
            The AI's response text
        """
        try:
            # Truncate passage text if too long to avoid token limits
            truncated_passage = passage_text[:self.MAX_PASSAGE_TEXT_LENGTH] + (
                "..." if len(passage_text) > self.MAX_PASSAGE_TEXT_LENGTH else ""
            )
            truncated_reference = passage_reference[:self.MAX_REFERENCE_LENGTH]

            # Build system prompt using prompt builder
            system_prompt = build_chat_system_prompt(
                passage_reference=truncated_reference,
                passage_text=truncated_passage,
                historical_context=insight_context.get('historical_context', ''),
                theological_significance=insight_context.get('theological_significance', ''),
                practical_application=insight_context.get('practical_application', ''),
                rag_context=rag_context,
                max_context_length=self.MAX_CONTEXT_LENGTH
            )

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
        chat_history: List = None,
        rag_context: str = ""
    ) -> Optional[str]:
        """
        Generate a chat response for standalone chats (not linked to insights).

        Args:
            user_message: The user's question
            passage_text: Optional Bible passage text for context
            passage_reference: Optional Bible passage reference
            chat_history: List of previous StandaloneChatMessage objects
            rag_context: Formatted RAG context string from RagService (optional)

        Returns:
            The AI's response text
        """
        if chat_history is None:
            chat_history = []

        try:
            # Handle passage truncation if provided
            truncated_passage = None
            truncated_reference = None
            if passage_text and passage_reference:
                truncated_passage = passage_text[:self.MAX_PASSAGE_TEXT_LENGTH] + (
                    "..." if len(passage_text) > self.MAX_PASSAGE_TEXT_LENGTH else ""
                )
                truncated_reference = passage_reference[:self.MAX_REFERENCE_LENGTH]
            
            # Build system prompt using prompt builder
            system_prompt = build_standalone_chat_system_prompt(
                passage_reference=truncated_reference,
                passage_text=truncated_passage,
                rag_context=rag_context
            )

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

    async def generate_chat_response_stream(
        self,
        user_message: str,
        passage_text: str,
        passage_reference: str,
        insight_context: dict,
        chat_history: List,
        rag_context: str = ""
    ) -> AsyncGenerator[Tuple[str, Optional[str]], None]:
        """
        Generate a streaming chat response using Claude with conversation context.

        Args:
            user_message: The user's question
            passage_text: The Bible passage text
            passage_reference: The Bible passage reference
            insight_context: Dict with historical_context, theological_significance, practical_application
            chat_history: List of previous ChatMessage objects
            rag_context: Formatted RAG context string from RagService (optional)

        Yields:
            Tuple[str, Optional[str]]: (text_chunk, stop_reason)
                - text_chunk: Text content from the stream
                - stop_reason: None for intermediate chunks, set to stop reason on final chunk
        """
        try:
            # Truncate passage text if too long to avoid token limits
            truncated_passage = passage_text[:self.MAX_PASSAGE_TEXT_LENGTH] + (
                "..." if len(passage_text) > self.MAX_PASSAGE_TEXT_LENGTH else ""
            )
            truncated_reference = passage_reference[:self.MAX_REFERENCE_LENGTH]

            # Build system prompt using prompt builder
            system_prompt = build_chat_system_prompt(
                passage_reference=truncated_reference,
                passage_text=truncated_passage,
                historical_context=insight_context.get('historical_context', ''),
                theological_significance=insight_context.get('theological_significance', ''),
                practical_application=insight_context.get('practical_application', ''),
                rag_context=rag_context,
                max_context_length=self.MAX_CONTEXT_LENGTH
            )

            # Build conversation messages
            messages = self._build_conversation_messages(user_message, chat_history)

            # Stream response
            stop_reason = None
            with self.client.messages.stream(
                model=self.MODEL_NAME,
                max_tokens=self.MAX_TOKENS_CHAT,
                system=system_prompt,
                messages=messages
            ) as stream:
                for text in stream.text_stream:
                    yield (text, None)

                # Get final message to extract stop_reason
                final_message = stream.get_final_message()
                stop_reason = final_message.stop_reason

            # Yield final empty chunk with stop_reason
            yield ("", stop_reason)
        except Exception as e:
            logger.error(f"Error generating streaming chat response: {e}", exc_info=True)
            raise

    async def generate_standalone_chat_response_stream(
        self,
        user_message: str,
        passage_text: Optional[str] = None,
        passage_reference: Optional[str] = None,
        chat_history: List = None,
        rag_context: str = ""
    ) -> AsyncGenerator[Tuple[str, Optional[str]], None]:
        """
        Generate a streaming chat response for standalone chats (not linked to insights).

        Args:
            user_message: The user's question
            passage_text: Optional Bible passage text for context
            passage_reference: Optional Bible passage reference
            chat_history: List of previous StandaloneChatMessage objects
            rag_context: Formatted RAG context string from RagService (optional)

        Yields:
            Tuple[str, Optional[str]]: (text_chunk, stop_reason)
                - text_chunk: Text content from the stream
                - stop_reason: None for intermediate chunks, set to stop reason on final chunk
        """
        if chat_history is None:
            chat_history = []

        try:
            # Handle passage truncation if provided
            truncated_passage = None
            truncated_reference = None
            if passage_text and passage_reference:
                truncated_passage = passage_text[:self.MAX_PASSAGE_TEXT_LENGTH] + (
                    "..." if len(passage_text) > self.MAX_PASSAGE_TEXT_LENGTH else ""
                )
                truncated_reference = passage_reference[:self.MAX_REFERENCE_LENGTH]
            
            # Build system prompt using prompt builder
            system_prompt = build_standalone_chat_system_prompt(
                passage_reference=truncated_reference,
                passage_text=truncated_passage,
                rag_context=rag_context
            )

            # Build conversation messages
            messages = self._build_conversation_messages(user_message, chat_history)

            # Stream response
            stop_reason = None
            with self.client.messages.stream(
                model=self.MODEL_NAME,
                max_tokens=self.MAX_TOKENS_CHAT,
                system=system_prompt,
                messages=messages
            ) as stream:
                for text in stream.text_stream:
                    yield (text, None)

                # Get final message to extract stop_reason
                final_message = stream.get_final_message()
                stop_reason = final_message.stop_reason

            # Yield final empty chunk with stop_reason
            yield ("", stop_reason)
        except Exception as e:
            logger.error(f"Error generating standalone streaming chat response: {e}", exc_info=True)
            raise

    async def generate_conversation_summary(
        self,
        conversation_text: str
    ) -> Optional[str]:
        """
        Generate a 1-2 sentence summary of a conversation using Claude Haiku.
        
        This is used for RAG context enhancement to provide quick summaries
        of past conversations. Uses Haiku for cost efficiency.
        
        Args:
            conversation_text: Formatted conversation history
            
        Returns:
            Summary text (1-2 sentences) or None on error
        """
        try:
            # Use Haiku for fast, cheap summaries
            HAIKU_MODEL = "claude-3-haiku-20240307"
            MAX_TOKENS_SUMMARY = 100  # Keep summaries concise
            
            system_prompt = """You are a helpful assistant that creates concise summaries of conversations.
Summarize the following conversation in 1-2 sentences, focusing on the main topics discussed."""
            
            message = self.client.messages.create(
                model=HAIKU_MODEL,
                max_tokens=MAX_TOKENS_SUMMARY,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Summarize this conversation:\n\n{conversation_text}"
                }]
            )
            
            if message.content and len(message.content) > 0:
                summary = message.content[0].text.strip()
                logger.debug(f"Generated conversation summary: {summary[:100]}...")
                return summary
            else:
                logger.warning("Empty response from Claude Haiku for summary generation")
                return None
                
        except Exception as e:
            logger.error(f"Error generating conversation summary: {e}", exc_info=True)
            return None
