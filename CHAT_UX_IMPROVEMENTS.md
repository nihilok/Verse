# Chat UX Improvements

This document describes the improvements made to the chat user experience in Verse.

## Overview

The chat functionality has been significantly improved to provide a cleaner, more intuitive interface:

1. **Separate Chat Interface** - Chat now opens in a dedicated modal instead of being a tab in the Insights modal
2. **Ask a Question** - Users can now start a chat without getting insights first
3. **Chat History** - New sidebar tab for managing standalone chats
4. **Continue Chat** - Insights with existing chats show a "Continue Chat" button

## Database Changes

### New Models

**StandaloneChat** - Represents a chat session not linked to insights
- `id`: Primary key
- `title`: Optional title derived from first message
- `passage_reference`: Optional passage reference
- `passage_text`: Optional passage text
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

**StandaloneChatMessage** - Messages in standalone chat sessions
- `id`: Primary key
- `chat_id`: Foreign key to StandaloneChat
- `role`: 'user' or 'assistant'
- `content`: Message content
- `created_at`: Creation timestamp

### Existing Models

The existing `ChatMessage` model remains unchanged and continues to work for insight-linked chats.

## API Endpoints

### Standalone Chat Endpoints

**POST /api/standalone-chat**
- Creates a new standalone chat session
- Body: `{ message, passage_text?, passage_reference? }`
- Returns: `{ chat_id, messages[] }`

**POST /api/standalone-chat/message**
- Sends a message in an existing chat
- Body: `{ chat_id, message }`
- Returns: `{ response }`

**GET /api/standalone-chat**
- Gets all standalone chat sessions
- Query: `limit` (default: 50)
- Returns: Array of chat sessions

**GET /api/standalone-chat/{chat_id}/messages**
- Gets all messages for a chat
- Returns: Array of messages

**DELETE /api/standalone-chat/{chat_id}**
- Deletes a chat session
- Returns: Success message

## Frontend Changes

### New Components

**ChatModal** (`src/components/ChatModal.tsx`)
- Generic modal for displaying any chat (standalone or insight-linked)
- Props: `title`, `subtitle`, `messages`, `onSendMessage`, `loading`

**ChatHistory** (`src/components/ChatHistory.tsx`)
- Displays list of standalone chats in sidebar
- Features: Select chat, delete chat, formatted timestamps

### Modified Components

**InsightsModal** (`src/components/InsightsModal.tsx`)
- Removed "Chat" tab
- Added "Continue Chat" button when messages exist
- Now has 3 tabs instead of 4 (Historical, Theological, Practical)

**BibleReader** (`src/components/BibleReader.tsx`)
- Added "Ask a Question" button to text selection tooltip
- Button appears below "Get Insights" button
- Opens standalone chat with selected text as context

**App** (`src/App.tsx`)
- Added state management for standalone chats
- Added three tabs in sidebar: Search, Insights, Chats
- Added handlers for creating and managing standalone chats
- Added separate modals for standalone and insight-linked chats

## User Flows

### Starting a Standalone Chat

1. User selects text in Bible reader
2. Selection tooltip appears with two buttons:
   - "Get Insights" (existing)
   - "Ask a Question" (new)
3. User clicks "Ask a Question"
4. Standalone chat is created with the selected text as context
5. Chat modal opens with initial AI response
6. Chat is saved to history for future access

### Starting a Chat from Insights

1. User gets insights on a passage (via "Get Insights" button)
2. Insights modal displays the three insight categories
3. "Ask Follow-up Question" button appears at bottom of insights modal
4. User clicks "Ask Follow-up Question"
5. Chat modal opens (empty, ready for first message)
6. User types a question about the insight or passage
7. AI responds with full context of the insight
8. Chat is linked to the insight for future access

### Continuing an Insight Chat

1. User views an insight that has previous chat messages
2. "Continue Chat" button appears at bottom of insights modal (showing message count)
3. User clicks "Continue Chat"
4. Chat modal opens with conversation history
5. User can continue the conversation about the insight

### Accessing Chat History

1. User opens sidebar
2. Clicks "Chats" tab
3. Sees list of all standalone chats
4. Can click to open any chat
5. Can delete chats by clicking trash icon

## Technical Details

### State Management

The app maintains separate state for:
- `chatMessages`: Messages for insight-linked chats
- `standaloneChatMessages`: Messages for standalone chats
- `chatHistory`: List of standalone chat sessions
- `currentChatId`: Currently active standalone chat
- `currentInsightId`: Currently active insight

### Chat Differentiation

- **Insight-linked chats**: Associated with a saved insight, include context of the insight's analysis
- **Standalone chats**: Not linked to insights, more flexible Q&A format
- Both types are saved to database and persist between sessions

### AI Context

**Insight-linked chats** receive:
- Passage text and reference
- Historical context from insight
- Theological significance from insight
- Practical application from insight
- Previous conversation history

**Standalone chats** receive:
- Optional passage text and reference (if started from text selection)
- Previous conversation history
- More general theological knowledge base

## Migration Notes

When deploying these changes:

1. Database migrations are automatic via SQLAlchemy's `create_all()`
2. New tables will be created on first startup
3. Existing insights and chat messages are unaffected
4. No data migration needed

## Testing

To test the changes:

1. **Standalone Chat from Selection**:
   - Select text in Bible reader
   - Click "Ask a Question"
   - Verify chat modal opens
   - Send messages and verify responses
   - Check chat appears in Chat History tab

2. **Start Chat from Insights**:
   - Get insights on a passage
   - In insights modal, verify "Ask Follow-up Question" button appears
   - Click the button
   - Verify chat modal opens (empty)
   - Send a message about the insight
   - Verify AI responds with context of the insight
   
3. **Continue Insight Chat**:
   - After starting a chat (from test #2)
   - Close modal
   - Reopen insights from history
   - Verify "Continue Chat" button appears with message count
   - Click and verify conversation continues

4. **Chat History Management**:
   - Create multiple chats
   - Verify all appear in Chat History tab
   - Click different chats and verify correct messages load
   - Delete a chat and verify it's removed

5. **Edge Cases**:
   - Test with very long messages
   - Test with rapid message sending
   - Test network errors during chat
   - Test concurrent chats (multiple tabs)
