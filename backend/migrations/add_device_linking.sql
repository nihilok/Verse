-- Migration: Add Device Linking Feature
-- Description: Adds tables and columns to support device linking functionality
-- Date: 2025-01-03

-- ============================================================================
-- UPGRADE
-- ============================================================================

-- Add device_count column to users table
ALTER TABLE users ADD COLUMN device_count INTEGER NOT NULL DEFAULT 1;

-- Create user_devices table
CREATE TABLE user_devices (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_name VARCHAR(100),
    device_type VARCHAR(20),  -- 'mobile', 'desktop', 'tablet', 'unknown'
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for user_devices
CREATE INDEX idx_user_devices_user_id ON user_devices(user_id);
CREATE INDEX idx_user_devices_last_active ON user_devices(user_id, last_active DESC);

-- Create device_link_codes table
CREATE TABLE device_link_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(64) UNIQUE NOT NULL,  -- Hashed token
    display_code VARCHAR(20) UNIQUE NOT NULL,  -- User-friendly format (XXXX-XXXX-XXXX)
    source_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_device_id INTEGER REFERENCES user_devices(id) ON DELETE CASCADE,
    target_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    target_device_id INTEGER REFERENCES user_devices(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    CONSTRAINT check_status CHECK (status IN ('pending', 'used', 'expired', 'revoked'))
);

-- Create indexes for device_link_codes
CREATE INDEX idx_device_link_codes_code ON device_link_codes(code);
CREATE INDEX idx_device_link_codes_display_code ON device_link_codes(display_code);
CREATE INDEX idx_device_link_codes_source_user ON device_link_codes(source_user_id);
CREATE INDEX idx_device_link_codes_pending ON device_link_codes(display_code) WHERE status = 'pending';
CREATE INDEX idx_device_link_codes_expires ON device_link_codes(expires_at) WHERE status = 'pending';

-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================

-- To rollback this migration, run the following SQL:

-- DROP TABLE device_link_codes;
-- DROP TABLE user_devices;
-- ALTER TABLE users DROP COLUMN device_count;
