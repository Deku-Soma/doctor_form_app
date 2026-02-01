"""
Test script to verify database migration success
Run this to test authentication and sync functionality
"""

from db import validate_login, sync_to_cloud
from Utility.local_db import local_db
import json

print("=" * 60)
print("DATABASE MIGRATION VERIFICATION TEST")
print("=" * 60)

# Test 1: Authentication
print("\n[TEST 1] Testing Authentication...")
print("-" * 60)
result = validate_login("admin@example.com", "password123")

if result.get("success"):
    print("✅ Authentication SUCCESSFUL")
    print(f"   Mode: {result.get('mode')}")
    print(f"   User: {result.get('user', {}).get('user_email')}")
    print(f"   Role: {result.get('user', {}).get('user_role')}")
else:
    print("❌ Authentication FAILED")
    print(f"   Error: {result.get('message')}")

# Test 2: Create Test Submission
print("\n[TEST 2] Creating Test Submission...")
print("-" * 60)

test_data = {
    "name": "Migration",
    "surname": "Test",
    "id_number": "9999999999999",
    "test_field": "This is a test submission after migration"
}

try:
    # Get user ID from login result
    user_id = result.get('user', {}).get('id') if result.get('success') else None
    
    sub_id = local_db.save_submission("test_form", test_data, user_id=user_id)
    print(f"✅ Submission created successfully")
    print(f"   Submission ID: {sub_id}")
    print(f"   User ID: {user_id}")
except Exception as e:
    print(f"❌ Submission creation FAILED")
    print(f"   Error: {e}")

# Test 3: Sync to Cloud
print("\n[TEST 3] Syncing to Supabase...")
print("-" * 60)

try:
    success = sync_to_cloud()
    if success:
        print("✅ Sync to cloud SUCCESSFUL")
        print("   No foreign key constraint errors!")
    else:
        print("⚠️  Sync completed with some errors")
        print("   Check console output above for details")
except Exception as e:
    print(f"❌ Sync FAILED")
    print(f"   Error: {e}")

# Test 4: Verify Unsynced Count
print("\n[TEST 4] Checking Unsynced Records...")
print("-" * 60)

unsynced = local_db.get_unsynced()
print(f"   Unsynced records: {len(unsynced)}")

if len(unsynced) == 0:
    print("✅ All records synced successfully")
else:
    print(f"⚠️  {len(unsynced)} records still unsynced")
    for record in unsynced[:3]:  # Show first 3
        print(f"   - {record['id']} ({record['form_type']})")

# Summary
print("\n" + "=" * 60)
print("MIGRATION VERIFICATION SUMMARY")
print("=" * 60)
print("\n✅ Migration appears successful if:")
print("   1. Authentication works")
print("   2. Submissions can be created")
print("   3. Sync completes without foreign key errors")
print("   4. No unsynced records remain (or they sync on retry)")
print("\n❌ Check for issues if:")
print("   - You see 'submissions_user_id_fkey' errors")
print("   - Sync fails repeatedly")
print("   - Authentication fails")
print("\n" + "=" * 60)
