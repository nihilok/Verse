"""
Chat Conversation Prompts

Prompts for ongoing conversations about passages and general biblical topics.
"""

from typing import Optional
from app.prompts.base_prompts import (
    build_continued_study_prompt,
    build_general_conversation_prompt,
    build_passage_context,
    build_passage_context_exploration,
    build_insights_context,
    build_engagement_guidelines,
    add_rag_context,
)


def build_chat_system_prompt(
    passage_reference: str,
    passage_text: str,
    historical_context: str,
    theological_significance: str,
    practical_application: str,
    rag_context: str = "",
    max_context_length: int = 1000
) -> str:
    """
    Build system prompt for chat about a specific passage (with insights).
    
    Args:
        passage_reference: Bible reference
        passage_text: The passage text
        historical_context: Historical context insight
        theological_significance: Theological significance insight
        practical_application: Practical application insight
        rag_context: Formatted RAG context from RagService
        max_context_length: Maximum length for insight fields
        
    Returns:
        Complete system prompt for passage-based chat
    """
    intro = build_continued_study_prompt()
    passage = build_passage_context(passage_reference, passage_text)
    insights = build_insights_context(
        historical_context,
        theological_significance,
        practical_application,
        max_context_length
    )
    guidelines = build_engagement_guidelines(for_passage=True)
    
    base_prompt = f"""{intro}

{passage}

{insights}

{guidelines}"""
    
    return add_rag_context(base_prompt, rag_context)


def build_standalone_chat_system_prompt(
    passage_reference: Optional[str] = None,
    passage_text: Optional[str] = None,
    rag_context: str = ""
) -> str:
    """
    Build system prompt for standalone chat (general questions or passage without insights).
    
    Args:
        passage_reference: Optional Bible reference if discussing a specific passage
        passage_text: Optional passage text if discussing a specific passage
        rag_context: Formatted RAG context from RagService
        
    Returns:
        Complete system prompt for standalone chat
    """
    if passage_reference and passage_text:
        # Chat about a specific passage without prior insights
        intro = f"""{build_general_conversation_prompt().split('.')[0]}. The user is exploring this passage and has questions about it.

Context About Your Role:
- Users are actively reading and responding to passages they've chosen
- They might be encountering this text for the first time or returning with new insights
- You illuminate what they're reading, helping them understand and apply it
- You're a thoughtful companion in their study, not a lecturer
- Remember what you've discussed and build on previous conversations"""
        
        passage = build_passage_context_exploration(passage_reference, passage_text)
        guidelines = build_engagement_guidelines(for_passage=True)
        
        base_prompt = f"""{intro}

{passage}

{guidelines}"""
    else:
        # General biblical conversation without a specific passage
        intro = build_general_conversation_prompt()
        guidelines = build_engagement_guidelines(for_passage=False)
        
        base_prompt = f"""{intro}

{guidelines}"""
    
    return add_rag_context(base_prompt, rag_context)
