"""
Simple migration verification test
"""
import sys
sys.path.insert(0, '.')

from db import validate_login, sync_to_cloud

print("Testing authentication...")
result = validate_login("admin@example.com", "password123")

if result.get("success"):
    print(f"SUCCESS: Logged in as {result.get('user', {}).get('user_email')}")
    print(f"Mode: {result.get('mode')}")
else:
    print(f"FAILED: {result.get('message')}")

print("\nTesting sync...")
try:
    success = sync_to_cloud()
    print(f"Sync result: {success}")
except Exception as e:
    print(f"Sync error: {e}")
    import traceback
    traceback.print_exc()
