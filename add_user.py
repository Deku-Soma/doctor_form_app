import getpass
import sys
import argparse
import logging

# Add current directory to path so we can import db
sys.path.append('.')

import db
from Utility.local_db import local_db

def add_user():
    print("=== Add New User Tool ===")
    
    parser = argparse.ArgumentParser(description="Add a new standard user to the system.")
    parser.add_argument("--username", help="Username for the new account")
    parser.add_argument("--email", help="Email for the new account")
    parser.add_argument("--password", help="Password for the new account")
    
    args = parser.parse_args()
    
    username = args.username
    email = args.email
    password = args.password
    
    # 1. Get Username
    if not username:
        try:
            username = input("Enter Username: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nError: Reading input failed. Use command line arguments: --username <name> --email <email>")
            return
            
    if not username:
        print("Username is required.")
        return

    # 2. Get Email
    if not email:
        try:
            email = input("Enter Email: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nError: Reading input failed.")
            return
            
    if not email:
        print("Email is required.")
        return

    # Check local db
    existing = local_db.get_user_by_email(email)
    if existing:
        print(f"User with email {email} already exists locally.")
        return

    # 3. Get Password
    if not password:
        try:
            password = getpass.getpass("Enter Password: ")
            confirm = getpass.getpass("Confirm Password: ")
            if password != confirm:
                print("Passwords do not match!")
                return
        except (EOFError, KeyboardInterrupt):
            print("\nError: Reading password failed. Use --password <pass> (Warning: insecure in history)")
            return

    if len(password) < 6:
        print("Password must be at least 6 characters.")
        return

    print(f"\nCreating user '{username}' ({email})...")
    try:
        # Create in Supabase (Cloud)
        result = db.create_user(email, password, username)
        
        # Check result
        if result and hasattr(result, 'data') and result.data:
            print(f"SUCCESS: User '{username}' created in cloud.")
            print("Please ask the user to log in. The first login requires an internet connection.")
        elif result and isinstance(result, dict) and "error" in result:
             print(f"ERROR: {result['error']}")
        else:
            print("Action completed. Please verify login.")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        # import traceback
        # traceback.print_exc()

if __name__ == "__main__":
    add_user()
