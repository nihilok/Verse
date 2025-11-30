-- Migration: Add was_truncated column to chat message tables
-- Date: 2025-11-30
-- Description: Adds truncation tracking to support "continue response" feature

-- Add was_truncated column to chat_messages table
ALTER TABLE chat_messages
ADD COLUMN IF NOT EXISTS was_truncated BOOLEAN NOT NULL DEFAULT FALSE;

-- Add was_truncated column to standalone_chat_messages table
ALTER TABLE standalone_chat_messages
ADD COLUMN IF NOT EXISTS was_truncated BOOLEAN NOT NULL DEFAULT FALSE;

-- Verify the columns were added
SELECT
    table_name,
    column_name,
    data_type,
    column_default
FROM information_schema.columns
WHERE table_name IN ('chat_messages', 'standalone_chat_messages')
  AND column_name = 'was_truncated';
