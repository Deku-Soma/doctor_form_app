-- ============================================================================
-- Database Migration: Deprecate users_1 → Use users for Authentication
-- ============================================================================
-- Run this script in Supabase SQL Editor
-- Execute each section carefully and verify results before proceeding

-- ============================================================================
-- STEP 1: VERIFY CURRENT STATE
-- ============================================================================

-- Check which user tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'users%';

-- Expected output: Should show 'users' and possibly 'users_1'

-- ============================================================================
-- STEP 2: CHECK FOREIGN KEY CONSTRAINTS
-- ============================================================================

-- Check current foreign key on submissions table
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'submissions' 
AND tc.constraint_type = 'FOREIGN KEY';

-- Note the constraint name and which table it references

-- ============================================================================
-- STEP 3: CHECK DATA IN users_1 (if it exists)
-- ============================================================================

-- Count records in users_1
-- UNCOMMENT if users_1 exists:
-- SELECT COUNT(*) as users_1_count FROM public.users_1;

-- Count records in users
SELECT COUNT(*) as users_count FROM public.users;

-- Compare data (if users_1 exists)
-- UNCOMMENT if users_1 exists:
-- SELECT 
--     u1.id,
--     u1.user_email,
--     CASE WHEN u.id IS NOT NULL THEN 'EXISTS IN USERS' ELSE 'MISSING' END as status
-- FROM public.users_1 u1
-- LEFT JOIN public.users u ON u1.id = u.id;

-- ============================================================================
-- STEP 4: MIGRATE DATA (if users_1 has unique data)
-- ============================================================================

-- ONLY RUN THIS IF users_1 has data that's not in users
-- UNCOMMENT and adjust column names as needed:
-- INSERT INTO public.users (id, created_at, user_email, user_password, user_name, user_role)
-- SELECT 
--     id,
--     created_at,
--     user_email,
--     user_password,
--     user_name,
--     user_role
-- FROM public.users_1
-- ON CONFLICT (id) DO UPDATE SET
--     user_email = EXCLUDED.user_email,
--     user_password = EXCLUDED.user_password,
--     user_name = EXCLUDED.user_name,
--     user_role = EXCLUDED.user_role;

-- ============================================================================
-- STEP 5: FIX FOREIGN KEY CONSTRAINT
-- ============================================================================

-- Drop the existing foreign key constraint
ALTER TABLE public.submissions
DROP CONSTRAINT IF EXISTS submissions_user_id_fkey;

-- Add new constraint pointing to public.users
ALTER TABLE public.submissions
ADD CONSTRAINT submissions_user_id_fkey
FOREIGN KEY (user_id) REFERENCES public.users(id)
ON DELETE SET NULL;

-- Verify the new constraint
SELECT
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'submissions' 
AND tc.constraint_type = 'FOREIGN KEY';

-- Expected: submissions_user_id_fkey should reference public.users(id)

-- ============================================================================
-- STEP 6: CHECK FOR ORPHANED SUBMISSIONS
-- ============================================================================

-- Find submissions with user_ids that don't exist in users table
SELECT 
    COUNT(*) as orphaned_count,
    user_id
FROM public.submissions s
WHERE s.user_id IS NOT NULL
AND s.user_id NOT IN (SELECT id FROM public.users)
GROUP BY user_id;

-- If there are orphaned records, decide how to handle them:
-- Option A: Set to NULL (if user_id is optional)
-- UPDATE public.submissions
-- SET user_id = NULL
-- WHERE user_id NOT IN (SELECT id FROM public.users);

-- Option B: Set to a default admin user (replace <admin-uuid> with actual ID)
-- UPDATE public.submissions
-- SET user_id = '<admin-uuid>'
-- WHERE user_id NOT IN (SELECT id FROM public.users);

-- ============================================================================
-- STEP 7: DROP users_1 TABLE (FINAL STEP)
-- ============================================================================

-- ONLY RUN AFTER CONFIRMING ALL DATA IS MIGRATED AND CONSTRAINTS ARE FIXED

-- Final safety check
-- UNCOMMENT if users_1 exists:
-- SELECT COUNT(*) as final_count FROM public.users_1;

-- Drop the table
-- UNCOMMENT when ready:
-- DROP TABLE IF EXISTS public.users_1 CASCADE;

-- Verify it's gone
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name = 'users_1';

-- Expected: No results (table should be gone)

-- ============================================================================
-- STEP 8: VERIFY FINAL STATE
-- ============================================================================

-- Check tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'users%';

-- Expected: Only 'users' should exist

-- Check foreign keys
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'submissions' 
AND tc.constraint_type = 'FOREIGN KEY';

-- Expected: submissions_user_id_fkey → public.users

-- Check user count
SELECT COUNT(*) as total_users FROM public.users;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Next steps:
-- 1. Test authentication in your application
-- 2. Test submission creation and sync
-- 3. Verify no foreign key errors in logs
-- ============================================================================
