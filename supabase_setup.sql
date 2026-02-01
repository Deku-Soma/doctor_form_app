-- Enable UUID extension if not already enabled
create extension if not exists "uuid-ossp";

-- Create the custom users table
create table public.users (
  id uuid default uuid_generate_v4() primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  user_email text unique not null,
  user_password text not null, -- Stores bcrypt hash
  user_name text,
  user_role text default 'user'::text
);

-- Enable Row Level Security (RLS)
alter table public.users enable row level security;

-- Policy: Allow anyone to read data (needed for login check)
-- WARNING: In a real production app, you might want to restrict this further 
-- or use a database function for login to avoid exposing hashes.
create policy "Allow public read"
on public.users
for select
to anon, authenticated
using (true);

-- Policy: Allow only authenticated users (or admins) to insert/update?
-- Since we removed Sign Up, technically only you via Dashboard should insert.
-- But if your 'create_user' function is used by an admin logged in app, enable this:
create policy "Allow authenticated insert"
on public.users
for insert
to authenticated
with check (true);

-- INSERT ADMIN USER
-- Password is: password123
-- Resulting Hash: $2b$12$h7AcRq5w4IasoRGCO3VAfOXbkr5qU19lPHJ0pWP2dCPB5JocATWti
INSERT INTO public.users (user_email, user_password, user_name, user_role)
VALUES (
    'admin@example.com', 
    '$2b$12$h7AcRq5w4IasoRGCO3VAfOXbkr5qU19lPHJ0pWP2dCPB5JocATWti', 
    'Super Admin', 
    'admin'
);
