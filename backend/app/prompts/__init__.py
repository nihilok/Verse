"""
AI Prompts Module

Centralized prompt templates and snippets for consistent AI interactions.
"""

from app.prompts.base_prompts import (
    VERSE_APP_CONTEXT,
    STUDY_COMPANION_ROLE,
    build_passage_context,
    build_insights_context,
    build_engagement_guidelines,
)

from app.prompts.insight_prompts import (
    build_insights_prompt,
)

from app.prompts.definition_prompts import (
    build_definition_prompt,
)

from app.prompts.chat_prompts import (
    build_chat_system_prompt,
    build_standalone_chat_system_prompt,
)

__all__ = [
    # Base components
    "VERSE_APP_CONTEXT",
    "STUDY_COMPANION_ROLE",
    "build_passage_context",
    "build_insights_context",
    "build_engagement_guidelines",
    
    # Specific prompts
    "build_insights_prompt",
    "build_definition_prompt",
    "build_chat_system_prompt",
    "build_standalone_chat_system_prompt",
]
