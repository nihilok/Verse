"""
Definition/Word Study Prompts

Prompts for generating word definitions and biblical word studies.
"""

from app.prompts.base_prompts import (
    build_word_study_prompt,
    build_definition_context,
)


def build_definition_prompt(word: str, passage_reference: str, verse_text: str) -> str:
    """
    Build complete prompt for generating a word definition.
    
    Args:
        word: The word to define
        passage_reference: Where the word appears
        verse_text: The full verse containing the word
        
    Returns:
        Complete formatted prompt for definition generation
    """
    intro = build_word_study_prompt()
    context = build_definition_context(word, passage_reference, verse_text)
    
    instructions = """Please provide:
1. Definition: A clear, accessible definition of this word as used in this specific biblical context. Start with what it means here, then expand.

2. Biblical Usage: How this word appears throughout Scripture and its significance. Help the reader see patterns and connections to other passages they might encounter.

3. Original Language: The Hebrew/Greek word, transliteration, and any important nuances lost or gained in translation. Make this enlightening rather than overwhelming.

Keep your tone warm and educational—like explaining to a curious friend rather than writing an academic paper.

Format your response as follows:
DEFINITION: [your definition]
BIBLICAL_USAGE: [your analysis]
ORIGINAL_LANGUAGE: [your analysis]"""

    return f"""{intro}

{context}

{instructions}"""
