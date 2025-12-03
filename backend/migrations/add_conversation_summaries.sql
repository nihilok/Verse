-- Migration: Add conversation_summaries table for RAG context enhancement
-- Description: Caches conversation summaries to improve RAG context with temporal memory
-- Date: 2025-12-01

-- Create conversation_summaries table
CREATE TABLE IF NOT EXISTS conversation_summaries (
    id SERIAL PRIMARY KEY,
    conversation_type VARCHAR(20) NOT NULL,
    conversation_id INTEGER NOT NULL,
    summary_text TEXT NOT NULL,
    message_count INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create unique composite index for lookup
CREATE UNIQUE INDEX IF NOT EXISTS idx_conversation_lookup
ON conversation_summaries(conversation_type, conversation_id);

-- Add comment for documentation
COMMENT ON TABLE conversation_summaries IS 'Caches AI-generated summaries of conversations for enhanced RAG context';
COMMENT ON COLUMN conversation_summaries.conversation_type IS 'Type of conversation: insight or standalone';
COMMENT ON COLUMN conversation_summaries.conversation_id IS 'Foreign key to saved_insights.id or standalone_chats.id';
COMMENT ON COLUMN conversation_summaries.message_count IS 'Number of messages in conversation when summary was generated (for cache invalidation)';
