-- Fix Foreign Key Constraint on Submissions Table

-- 1. Drop the existing constraint (which likely points to auth.users or a different table)
ALTER TABLE public.submissions
DROP CONSTRAINT IF EXISTS submissions_user_id_fkey;

-- 2. Add the new constraint pointing to our custom public.users table
ALTER TABLE public.submissions
ADD CONSTRAINT submissions_user_id_fkey
FOREIGN KEY (user_id) REFERENCES public.users(id);

-- Optional: Verify the users table exists and has the correct ID type (UUID)
-- (This was checked in previous step, assuming public.users(id) is UUID)
