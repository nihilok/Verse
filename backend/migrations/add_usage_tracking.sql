-- Migration: Add usage tracking and pro subscription features
-- Date: 2025-12-06
-- Description: Adds pro_subscription column to users table and creates usage_tracking table

-- Add pro_subscription column to users table (idempotent)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'pro_subscription'
    ) THEN
        ALTER TABLE users ADD COLUMN pro_subscription BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
END $$;

-- Create usage_tracking table (idempotent)
CREATE TABLE IF NOT EXISTS usage_tracking (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    llm_calls INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uix_user_date UNIQUE (user_id, date)
);

-- Create indexes for usage_tracking (idempotent)
CREATE INDEX IF NOT EXISTS idx_usage_tracking_user_id ON usage_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_date ON usage_tracking(date);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_user_date ON usage_tracking(user_id, date);

-- Create function to update updated_at timestamp (idempotent)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for usage_tracking updated_at (idempotent)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'update_usage_tracking_updated_at'
    ) THEN
        CREATE TRIGGER update_usage_tracking_updated_at
            BEFORE UPDATE ON usage_tracking
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;
