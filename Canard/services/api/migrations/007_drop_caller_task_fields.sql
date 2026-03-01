-- 007_drop_caller_task_fields.sql
-- Remove attack_type and description from callers table.
-- These are task/direction concerns that belong on the scripts table.
-- Callers should only store identity/persona fields.

ALTER TABLE callers DROP COLUMN IF EXISTS attack_type;
ALTER TABLE callers DROP COLUMN IF EXISTS description;