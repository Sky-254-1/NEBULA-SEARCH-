-- Migration 012: Add pending_email column to email_verification table
-- Supports the change-email flow where a user requests to change their email
-- and must verify the new address before it takes effect.

ALTER TABLE email_verification ADD COLUMN pending_email TEXT;