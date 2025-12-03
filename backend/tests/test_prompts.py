"""
Tests for Prompts Module

Unit tests for prompt builder functions.
"""

import pytest

from app.prompts import (
    STUDY_COMPANION_ROLE,
    VERSE_APP_CONTEXT,
    build_chat_system_prompt,
    build_definition_prompt,
    build_engagement_guidelines,
    build_insights_context,
    build_insights_prompt,
    build_passage_context,
    build_standalone_chat_system_prompt,
)
from app.prompts.base_prompts import add_rag_context


def test_verse_app_context_constant():
    """Test that VERSE_APP_CONTEXT is defined."""
    assert "Verse" in VERSE_APP_CONTEXT
    assert "interactive Bible reading app" in VERSE_APP_CONTEXT


def test_study_companion_role_constant():
    """Test that STUDY_COMPANION_ROLE is defined."""
    assert "Context About Your Role" in STUDY_COMPANION_ROLE
    assert "study companion" in STUDY_COMPANION_ROLE


def test_build_passage_context():
    """Test passage context formatting."""
    result = build_passage_context("John 3:16", "For God so loved the world")

    assert "John 3:16" in result
    assert "For God so loved the world" in result
    assert "Passage" in result


def test_build_insights_context():
    """Test insights context formatting."""
    result = build_insights_context(
        historical_context="Written in 1st century",
        theological_significance="Central to gospel message",
        practical_application="Love others sacrificially",
    )

    assert "Historical Context" in result
    assert "Written in 1st century" in result
    assert "Theological Significance" in result
    assert "Central to gospel message" in result
    assert "Practical Application" in result
    assert "Love others sacrificially" in result


def test_build_insights_context_truncation():
    """Test that insights are truncated to max_length."""
    long_text = "x" * 2000
    result = build_insights_context(
        historical_context=long_text,
        theological_significance="short",
        practical_application="short",
        max_length=100,
    )

    # Should be truncated to 100 chars
    assert long_text[:100] in result
    assert len(long_text) not in [result.count("x")]


def test_build_engagement_guidelines_for_passage():
    """Test engagement guidelines for passage study."""
    result = build_engagement_guidelines(for_passage=True)

    assert "Engage thoughtfully" in result
    assert "surrounding verses" in result
    assert "passage" in result


def test_build_engagement_guidelines_general():
    """Test engagement guidelines for general conversation."""
    result = build_engagement_guidelines(for_passage=False)

    assert "Engage thoughtfully" in result
    assert "Scripture" in result
    # Should NOT mention "surrounding verses" for general chat
    assert "surrounding verses" not in result


def test_add_rag_context_empty():
    """Test adding empty RAG context."""
    base = "This is a base prompt"
    result = add_rag_context(base, "")

    assert result == base


def test_add_rag_context_with_content():
    """Test adding RAG context with content."""
    base = "This is a base prompt"
    rag = "RAG context from past conversations"
    result = add_rag_context(base, rag)

    assert base in result
    assert rag in result


def test_build_insights_prompt():
    """Test complete insights prompt building."""
    result = build_insights_prompt(
        passage_reference="Romans 8:28",
        passage_text="And we know that in all things God works...",
    )

    assert "Romans 8:28" in result
    assert "And we know that in all things God works" in result
    assert "Historical Context" in result
    assert "Theological Significance" in result
    assert "Practical Application" in result
    assert "Verse" in result  # From VERSE_APP_CONTEXT


def test_build_definition_prompt():
    """Test complete definition prompt building."""
    result = build_definition_prompt(
        word="faith",
        passage_reference="Hebrews 11:1",
        verse_text="Now faith is confidence in what we hope for",
    )

    assert "faith" in result
    assert "Hebrews 11:1" in result
    assert "Now faith is confidence" in result
    assert "Definition" in result
    assert "Biblical Usage" in result
    assert "Original Language" in result


def test_build_chat_system_prompt():
    """Test chat system prompt building with insights."""
    result = build_chat_system_prompt(
        passage_reference="John 3:16",
        passage_text="For God so loved the world",
        historical_context="Written by John",
        theological_significance="Central to salvation",
        practical_application="Share God's love",
        rag_context="",
        max_context_length=1000,
    )

    assert "John 3:16" in result
    assert "For God so loved the world" in result
    assert "Written by John" in result
    assert "Central to salvation" in result
    assert "Share God's love" in result
    assert "Verse" in result


def test_build_chat_system_prompt_with_rag():
    """Test chat system prompt with RAG context."""
    rag_context = "Previous conversation about love"
    result = build_chat_system_prompt(
        passage_reference="John 3:16",
        passage_text="For God so loved",
        historical_context="Context",
        theological_significance="Significance",
        practical_application="Application",
        rag_context=rag_context,
    )

    assert rag_context in result


def test_build_standalone_chat_system_prompt_no_passage():
    """Test standalone chat prompt without passage."""
    result = build_standalone_chat_system_prompt()

    assert "Verse" in result
    assert "study companion" in result
    # Should NOT have passage-specific elements
    assert "Reference:" not in result


def test_build_standalone_chat_system_prompt_with_passage():
    """Test standalone chat prompt with passage."""
    result = build_standalone_chat_system_prompt(
        passage_reference="Psalm 23", passage_text="The Lord is my shepherd"
    )

    assert "Psalm 23" in result
    assert "The Lord is my shepherd" in result
    assert "Exploring" in result or "exploring" in result


def test_build_standalone_chat_system_prompt_with_rag():
    """Test standalone chat prompt with RAG context."""
    rag_context = "Previous discussion about prayer"
    result = build_standalone_chat_system_prompt(rag_context=rag_context)

    assert rag_context in result


def test_prompts_are_non_empty():
    """Test that all prompt builders return non-empty strings."""
    prompts = [
        build_insights_prompt("John 3:16", "text"),
        build_definition_prompt("faith", "Heb 11:1", "verse"),
        build_chat_system_prompt("John 3:16", "text", "h", "t", "p"),
        build_standalone_chat_system_prompt(),
    ]

    for prompt in prompts:
        assert prompt
        assert len(prompt) > 50  # Should be substantial


def test_consistency_across_similar_prompts():
    """Test that similar prompts share common elements."""
    chat_prompt = build_chat_system_prompt("John 3:16", "text", "h", "t", "p")
    standalone_prompt = build_standalone_chat_system_prompt("John 3:16", "text")

    # Both should mention Verse
    assert "Verse" in chat_prompt
    assert "Verse" in standalone_prompt

    # Both should have study companion messaging
    assert "study companion" in chat_prompt.lower()
    assert "study companion" in standalone_prompt.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
