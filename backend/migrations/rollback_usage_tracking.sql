-- Rollback Migration: Remove usage tracking and pro subscription features
-- Date: 2025-12-06
-- Description: Removes usage_tracking table and pro_subscription column

BEGIN;

-- Drop trigger and function
DROP TRIGGER IF EXISTS update_usage_tracking_updated_at ON usage_tracking;
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop usage_tracking table (CASCADE will drop indexes and constraints)
DROP TABLE IF EXISTS usage_tracking CASCADE;

-- Remove pro_subscription column from users table
ALTER TABLE users
DROP COLUMN IF EXISTS pro_subscription;

COMMIT;
