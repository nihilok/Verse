"""
Insight Generation Prompts

Prompts for generating initial insights on Bible passages.
"""

from app.prompts.base_prompts import (
    build_initial_study_prompt,
    build_passage_context,
)


def build_insights_prompt(passage_reference: str, passage_text: str) -> str:
    """
    Build complete prompt for generating insights on a passage.
    
    Args:
        passage_reference: Bible reference (e.g., "Romans 8:28")
        passage_text: The actual passage text
        
    Returns:
        Complete formatted prompt for insight generation
    """
    intro = build_initial_study_prompt()
    passage = build_passage_context(passage_reference, passage_text)
    
    instructions = """Please provide insights in three categories:

1. Historical Context: The historical background, cultural setting, and circumstances of writing. Help readers understand what was happening when this was written and why.

2. Theological Significance: The theological themes, doctrines, and spiritual meaning. Connect this passage to broader biblical narratives and God's character.

3. Practical Application: How this passage applies to modern life. Provide concrete, accessible ways readers can apply these teachings today.

Keep your tone warm and educational—like a knowledgeable study companion rather than a lecturer. Remember, they chose this specific passage for a reason.

Format your response as follows:
HISTORICAL_CONTEXT: [your analysis]
THEOLOGICAL_SIGNIFICANCE: [your analysis]
PRACTICAL_APPLICATION: [your analysis]"""

    return f"""{intro}

{passage}

{instructions}"""
