import ulid
try:
    u = ulid.ULID()
    print(f"ULID generated successfully: {u}")
except Exception as e:
    print(f"Error: {e}")
