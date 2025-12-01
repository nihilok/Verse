# Prompts Module Documentation

## Overview

The `app/prompts/` module provides centralized, composable prompt components for consistent AI interactions across Verse. This eliminates duplication and makes it easy to maintain and update system prompts.

## Why This Module Exists

**Problem:** System prompts were duplicated across 6 different methods in ClaudeAIClient:
- `generate_insights()`
- `generate_definition()`
- `generate_chat_response()`
- `generate_standalone_chat_response()`
- `generate_chat_response_stream()`
- `generate_standalone_chat_response_stream()`

Any change to the core "study companion" role or Verse app context required updating all 6 places, risking inconsistencies.

**Solution:** Extract prompts into reusable components that can be composed together.

## Module Structure

```
app/prompts/
├── __init__.py                  # Public API exports
├── base_prompts.py              # Reusable prompt components
├── insight_prompts.py           # Initial passage insights
├── definition_prompts.py        # Word definitions
└── chat_prompts.py              # Conversation prompts
```

## Base Components (`base_prompts.py`)

### Constants

#### `VERSE_APP_CONTEXT`
Core context that appears in all prompts:
```python
"You are a study companion in Verse, an interactive Bible reading app."
```

#### `STUDY_COMPANION_ROLE`
Role explanation for passage-based interactions:
```python
"""Context About Your Role:
- Users are actively reading and responding to specific passages
- They might be encountering this text for the first time
- Your job is to illuminate what they're reading RIGHT NOW
- You're more like a thoughtful study companion than a lecturer
- They might jump around Scripture non-linearly or return to passages later"""
```

#### `STUDY_COMPANION_ROLE_GENERAL`
Role explanation for general biblical conversations:
```python
"""Context About Your Role:
- Users are on a journey of biblical discovery
- They might ask about passages, concepts, or how to apply Scripture
- You serve as their thoughtful study companion
- Remember their previous questions and build on them
- Connect ideas to biblical texts they might explore in the app"""
```

### Builder Functions

#### `build_passage_context(reference, text)`
Formats passage information:
```python
passage = build_passage_context("John 3:16", "For God so loved...")
# Returns:
# "The Passage They're Studying:
#  Reference: John 3:16
#  Text: For God so loved..."
```

#### `build_insights_context(historical, theological, practical, max_length=1000)`
Formats previous insights:
```python
insights = build_insights_context(
    historical_context="Written in 1st century...",
    theological_significance="Shows God's love...",
    practical_application="We should love others...",
    max_length=1000
)
```

#### `build_engagement_guidelines(for_passage=True)`
Engagement instructions (passage-specific or general):
```python
guidelines = build_engagement_guidelines(for_passage=True)
# Returns passage-focused guidelines

guidelines = build_engagement_guidelines(for_passage=False)
# Returns general conversation guidelines
```

#### `add_rag_context(base_prompt, rag_context)`
Appends RAG context if available:
```python
prompt = add_rag_context(base_prompt, rag_context_string)
# If rag_context is empty, returns base_prompt unchanged
```

## High-Level Builders

### Insights (`insight_prompts.py`)

```python
from app.prompts import build_insights_prompt

prompt = build_insights_prompt(
    passage_reference="Romans 8:28",
    passage_text="And we know that in all things..."
)
```

**Returns:** Complete prompt for initial passage analysis with instructions for historical context, theological significance, and practical application.

### Definitions (`definition_prompts.py`)

```python
from app.prompts import build_definition_prompt

prompt = build_definition_prompt(
    word="faith",
    passage_reference="Hebrews 11:1",
    verse_text="Now faith is..."
)
```

**Returns:** Complete prompt for word definition with biblical usage and original language information.

### Chat (`chat_prompts.py`)

#### Passage-Based Chat (with insights)

```python
from app.prompts import build_chat_system_prompt

prompt = build_chat_system_prompt(
    passage_reference="John 3:16",
    passage_text="For God so loved...",
    historical_context="Written in 1st century...",
    theological_significance="Central message of gospel...",
    practical_application="Shows God's sacrificial love...",
    rag_context="[formatted RAG context from RagService]",
    max_context_length=1000
)
```

**Returns:** Complete system prompt for follow-up conversation about a passage.

#### Standalone Chat

```python
from app.prompts import build_standalone_chat_system_prompt

# Without a specific passage
prompt = build_standalone_chat_system_prompt(
    rag_context="[optional RAG context]"
)

# With a passage (but no prior insights)
prompt = build_standalone_chat_system_prompt(
    passage_reference="Psalm 23",
    passage_text="The Lord is my shepherd...",
    rag_context="[optional RAG context]"
)
```

**Returns:** Complete system prompt for general biblical conversation.

## Usage in ClaudeAIClient

### Before (Duplicated)

```python
async def generate_insights(self, request):
    prompt = f"""You are a biblical scholar and theologian serving as a study companion in Verse, an interactive Bible reading app. Users have just highlighted a passage...
    
    Passage Reference: {request.passage_reference}
    Passage Text: {request.passage_text}
    
    Please provide insights in three categories:
    1. Historical Context...
    2. Theological Significance...
    3. Practical Application...
    """
    # ... rest of method
```

This was repeated (with variations) across 6 methods!

### After (Composable)

```python
from app.prompts import build_insights_prompt

async def generate_insights(self, request):
    prompt = build_insights_prompt(
        passage_reference=request.passage_reference,
        passage_text=request.passage_text
    )
    # ... rest of method
```

Clean, consistent, maintainable!

## Benefits

### 1. Single Source of Truth
Update the "study companion" role once, it applies everywhere:
```python
# In base_prompts.py
STUDY_COMPANION_ROLE = """Context About Your Role:
- Users are actively reading passages...  # Change here
- ...
"""
```

All 6 methods automatically get the update.

### 2. Easy Testing
Test prompt components in isolation:
```python
def test_passage_context():
    result = build_passage_context("John 3:16", "For God so loved...")
    assert "John 3:16" in result
    assert "For God so loved" in result
```

### 3. Consistent Tone
No more accidentally different wording between streaming/non-streaming versions.

### 4. Easier Experimentation
Want to try a different engagement style? Change `build_engagement_guidelines()` and see how it affects all interactions.

### 5. Clear Structure
New developers can see exactly what components make up each prompt type.

## Updating Prompts

### Change Core Context

Edit `base_prompts.py`:
```python
VERSE_APP_CONTEXT = """You are a study companion in Verse, 
an interactive Bible reading and study app."""  # Updated
```

All prompts automatically include the new context.

### Change Role Instructions

Edit `STUDY_COMPANION_ROLE` in `base_prompts.py`:
```python
STUDY_COMPANION_ROLE = """Context About Your Role:
- Users are actively reading passages
- New instruction here  # Added
- ...
"""
```

### Add New Prompt Type

1. Create new file: `app/prompts/new_feature_prompts.py`
2. Import base components
3. Build your prompt:
```python
from app.prompts.base_prompts import VERSE_APP_CONTEXT

def build_new_feature_prompt(param1, param2):
    return f"""{VERSE_APP_CONTEXT} 
    
    {param1}
    {param2}
    
    Instructions..."""
```
4. Export in `__init__.py`
5. Use in ClaudeAIClient

### Modify Specific Prompt

Edit the relevant file (`insight_prompts.py`, `definition_prompts.py`, etc.):
```python
def build_insights_prompt(passage_reference, passage_text):
    intro = build_initial_study_prompt()
    passage = build_passage_context(passage_reference, passage_text)
    
    # Change instructions here
    instructions = """New instructions format..."""
    
    return f"{intro}\n\n{passage}\n\n{instructions}"
```

## Best Practices

### 1. Use Builder Functions
Don't concatenate strings manually:
```python
# ❌ Don't do this
prompt = f"You are a study companion in Verse. Reference: {ref}"

# ✅ Do this
prompt = build_passage_context(ref, text)
```

### 2. Keep Components Focused
Each function should do one thing:
- `build_passage_context()` - formats passage info
- `build_insights_context()` - formats insights info
- `build_engagement_guidelines()` - formats guidelines

### 3. Compose, Don't Duplicate
Build complex prompts from simple components:
```python
def build_new_prompt():
    return f"""{VERSE_APP_CONTEXT}
    
{STUDY_COMPANION_ROLE}

{build_passage_context(...)}

{build_engagement_guidelines()}"""
```

### 4. Test Components
Write unit tests for base components:
```python
def test_add_rag_context_empty():
    result = add_rag_context("base prompt", "")
    assert result == "base prompt"

def test_add_rag_context_with_content():
    result = add_rag_context("base", "RAG content")
    assert "RAG content" in result
```

### 5. Document Changes
When updating prompts, document the change and reasoning:
```python
# 2024-12-01: Updated to emphasize accessibility over academic tone
STUDY_COMPANION_ROLE = """..."""
```

## Migration Notes

### What Changed

**Before:** Prompts hardcoded in `claude_client.py` (6 places)
**After:** Prompts in `app/prompts/` module (1 source of truth)

### Files Added
- `app/prompts/__init__.py`
- `app/prompts/base_prompts.py`
- `app/prompts/insight_prompts.py`
- `app/prompts/definition_prompts.py`
- `app/prompts/chat_prompts.py`

### Files Modified
- `app/clients/claude_client.py` - Now imports and uses prompt builders

### Breaking Changes
None - this is a pure refactoring. All prompts generate identical output.

## Future Enhancements

Possible future additions:

1. **Prompt Versioning**
   ```python
   build_chat_system_prompt(version="v2")
   ```

2. **User Preferences**
   ```python
   build_chat_system_prompt(
       tone="academic",  # vs "conversational"
       depth="detailed"   # vs "concise"
   )
   ```

3. **A/B Testing**
   ```python
   prompt = build_chat_system_prompt(
       experiment_id="study_companion_v2"
   )
   ```

4. **Localization**
   ```python
   prompt = build_insights_prompt(
       ...,
       language="es"
   )
   ```

## Related Documentation

- `docs/system-prompt-philosophy.md` - Why prompts are designed this way
- `docs/rag-quick-reference.md` - How RAG context integrates with prompts
- `backend/app/clients/claude_client.py` - How prompts are used in practice

## Questions?

**Q: Can I still customize prompts per-method?**
A: Yes! Pass different parameters or extend the builders:
```python
custom_prompt = build_chat_system_prompt(...) + "\n\nSpecial instructions..."
```

**Q: How do I preview what a prompt looks like?**
A: Import and call the builder:
```python
from app.prompts import build_insights_prompt
print(build_insights_prompt("John 3:16", "For God so loved..."))
```

**Q: What if I need a completely different prompt?**
A: Create a new builder function. You don't have to use the base components if they don't fit.

**Q: How do I keep streaming/non-streaming in sync?**
A: They both use the same builder functions, so they stay in sync automatically.

---

**Version:** 1.0
**Last Updated:** December 1, 2024
**Maintainer:** Verse Development Team
