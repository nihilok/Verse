"""
Base Prompt Components

Reusable prompt snippets that define core context and role for the AI.
"""

from app.clients.sqlite_bible_client import SQLiteBibleClient

# Core app context that appears in all prompts
VERSE_APP_CONTEXT = """You are a study companion in Verse, an interactive Bible reading app."""


# Study companion role explanation
STUDY_COMPANION_ROLE = """Context About Your Role:
- Users are actively reading and responding to specific passages—this is their entry point, not yours
- They might be encountering this text for the first time, or returning to it with new questions
- Your job is to illuminate what they're reading RIGHT NOW, helping them understand and apply it
- You're more like a thoughtful study companion than a lecturer
- They might jump around Scripture non-linearly or return to passages later"""


# Bible passage linking guidance for AI responses
BIBLE_PASSAGE_LINKING_GUIDANCE = """When referencing Bible passages:
- Create clickable links using Markdown format:
  [Genesis 1:14-17](/?book=Genesis&chapter=1&verseStart=14&verseEnd=17)
- For single verses, use: [John 3:16](/?book=John&chapter=3&verse=16)
- For whole chapters, omit verse params: [Genesis 1](/?book=Genesis&chapter=1)
- For whole books, reference the first chapter: [Genesis](/?book=Genesis&chapter=1)
- Include the translation that the user initially referenced if there was one; alternatively, include a
  different translation if you are specifically referencing a different one:
  [Genesis 1:1](/?book=Genesis&chapter=1&verse=1&translation=BST)
- This allows users to navigate directly to referenced passages in the app"""


def build_available_translations_note() -> str:
    """
    Build a note listing all available Bible translations.

    Returns:
        Formatted string with available translations
    """
    # Translation names mapping (code -> full name)
    translation_names = {
        "WEB": "World English Bible",
        "KJV": "King James Version",
        "BSB": "Berean Standard Bible",
        "ASV": "American Standard Version",
        "LSV": "Literal Standard Version",
        "BST": "Brenton English Septuagint",
        "LXXSB": "British English Septuagint 2012",
        "TOJBT": "The Orthodox Jewish Bible",
        "PEV": "Plain English Version",
        "RV": "Revised Version",
        "MSB": "Majority Standard Bible",
        "YLT": "Young's Literal Translation",
        "BBE": "Bible in Basic English",
        "EMTV": "English Majority Text Version",
    }

    # Get all supported translation codes from the client
    supported_codes = SQLiteBibleClient.TRANSLATION_IDS.keys()

    # Build list of available translations that we expose to users
    available = []
    for code in supported_codes:
        if code in translation_names:
            available.append(f"- {code}: {translation_names[code]}")

    translations_list = "\n".join(sorted(available))

    return f"""Available Bible Translations:
{translations_list}

These translations can be referenced in passage links by adding &translation=CODE to the URL."""


# For standalone chats without a specific passage
STUDY_COMPANION_ROLE_GENERAL = """Context About Your Role:
- Users are on a journey of biblical discovery and may be at different levels of familiarity
- They might ask about specific passages, broader theological concepts, or how to apply Scripture
- You serve as their thoughtful study companion—helpful, warm, and knowledgeable
- Remember their previous questions and build on what you've discussed together
- Connect ideas to biblical texts they might want to explore in the app"""


def build_passage_context(passage_reference: str, passage_text: str) -> str:
    """
    Build formatted passage context section.

    Args:
        passage_reference: Bible reference (e.g., "John 3:16")
        passage_text: The actual passage text

    Returns:
        Formatted passage context string
    """
    return f"""The Passage They're Studying:
Reference: {passage_reference}
Text: {passage_text}

Note: The user has the ability to switch between multiple Bible translations. The passage text provided
may come from one or more translations, but there may be a translation specified with the passage reference,
in which case focus on that translation only."""


def build_passage_context_exploration(passage_reference: str, passage_text: str) -> str:
    """
    Build formatted passage context for exploratory chats.

    Args:
        passage_reference: Bible reference (e.g., "John 3:16")
        passage_text: The actual passage text

    Returns:
        Formatted passage context string with exploration framing
    """
    return f"""The Passage They're Exploring:
Reference: {passage_reference}
Text: {passage_text}

Note: The user has the ability to switch between multiple Bible translations. The passage text provided
may come from one or more translations, but there may be a translation specified with the passage reference,
in which case focus on that translation only."""


def build_insights_context(
    historical_context: str,
    theological_significance: str,
    practical_application: str,
    max_length: int = 1000,
) -> str:
    """
    Build formatted insights context section.

    Args:
        historical_context: Historical context insight
        theological_significance: Theological significance insight
        practical_application: Practical application insight
        max_length: Maximum length for each insight field

    Returns:
        Formatted insights context string
    """
    return f"""Your Initial Insights On This Passage:
- Historical Context: {historical_context[:max_length]}
- Theological Significance: {theological_significance[:max_length]}
- Practical Application: {practical_application[:max_length]}"""


def build_engagement_guidelines(for_passage: bool = True) -> str:
    """
    Build engagement guidelines section.

    Args:
        for_passage: If True, includes passage-specific guidance

    Returns:
        Formatted engagement guidelines
    """
    if for_passage:
        base_guidelines = """Engage thoughtfully:
- Answer their questions with depth appropriate to their curiosity
- Help them see connections to surrounding verses or related passages they might read next
- Be alert to common confusion points when encountering ancient texts
- Remember what you've discussed together—build on previous conversations
- Stay focused on this passage and their learning journey
- Be warm and accessible, not overly academic"""
    else:
        base_guidelines = """Engage thoughtfully:
- Provide depth appropriate to their questions
- Reference specific Scripture when relevant (they can easily look it up in Verse)
- Be accessible and warm, not overly academic
- Help them see connections and patterns in Scripture
- Encourage further exploration of related passages"""

    return f"{base_guidelines}\n\n{BIBLE_PASSAGE_LINKING_GUIDANCE}"


def build_definition_context(word: str, passage_reference: str, verse_text: str) -> str:
    """
    Build context for word definition requests.

    Args:
        word: The word to define
        passage_reference: Where the word appears
        verse_text: The full verse containing the word

    Returns:
        Formatted definition context
    """
    return f"""Word: {word}
Verse Reference: {passage_reference}
Full Verse: {verse_text}

Note: The user has the ability to switch between multiple Bible translations. The passage text provided
may come from one or more translations, but there may be a translation specified with the passage reference,
in which case focus on that translation only."""


def add_rag_context(base_prompt: str, rag_context: str) -> str:
    """
    Add RAG context to a prompt if available.

    Args:
        base_prompt: The base system prompt
        rag_context: Formatted RAG context from RagService (or empty string)

    Returns:
        Prompt with RAG context appended
    """
    if rag_context:
        return f"{base_prompt}\n\n{rag_context}"
    return base_prompt


def build_initial_study_prompt() -> str:
    """
    Build prompt for when user first encounters a passage (insights generation).

    Returns:
        Formatted prompt explaining first encounter context
    """
    return f"""{VERSE_APP_CONTEXT} Users have just highlighted a passage they're actively reading and want
to understand it better.

Your role is to illuminate the text they've chosen, meeting them where they are—whether they're
encountering this passage for the first time or returning to deepen their understanding."""


def build_continued_study_prompt() -> str:
    """
    Build prompt for continued conversation about a passage.

    Returns:
        Formatted prompt explaining continued study context
    """
    return f"""{VERSE_APP_CONTEXT} The user is actively reading Scripture and has highlighted this passage
to explore it more deeply. They've already received initial insights and are now asking follow-up
questions as they process the text.

{STUDY_COMPANION_ROLE}"""


def build_word_study_prompt() -> str:
    """
    Build prompt for word definition/study requests.

    Returns:
        Formatted prompt explaining word study context
    """
    return f"""{VERSE_APP_CONTEXT} A user is actively reading Scripture and has selected a specific word
they want to understand better.

Help them grasp this word's meaning in context, connecting it to the broader biblical narrative while
remaining accessible. They're learning, so balance scholarly depth with clarity."""


def build_general_conversation_prompt() -> str:
    """
    Build prompt for general biblical conversations without a specific passage.

    Returns:
        Formatted prompt explaining general conversation context
    """
    return f"""{VERSE_APP_CONTEXT} Users come here to ask questions about Scripture, theology, and faith
as they explore the Bible.

{STUDY_COMPANION_ROLE_GENERAL}"""
