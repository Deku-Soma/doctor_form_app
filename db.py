import json
import os
import bcrypt
import base64
import sqlite3
from dotenv import load_dotenv
from supabase import create_client
from Utility.local_db import local_db

load_dotenv(dotenv_path=".env")  # Optional: give full path if needed

url = os.getenv("SUPERBASE_URL")
key = os.getenv("SUPERBASE_API_KEY")

try:
    supabase = create_client(url, key)
except Exception as e:
    print(f"Supabase init failed (offline?): {e}")
    supabase = None


def create_user(email: str, password: str, username: str = "") -> dict:
    # Existing code... (keep existing create_user implementation if possible or just use what's there)
    # Re-implementing strictly to avoid deleting it if replace_file_content replaces the whole block
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    data = {
        "user_email": email,
        "user_password": hashed_pw,
        "user_name": username,
        "user_role":"Regular"
    }
    if supabase:
        result = supabase.table("users").insert(data).execute()
        return result
    return {"error": "Offline"}


def validate_login(email: str, password: str) -> dict:
    if not supabase:
        return {"success": False, "message": "Offline - Login not available"}
        
    result = supabase.table("users").select("*").eq("user_email", email).execute()
    if not result.data:
        return {"success": False, "message": "Email not found"}

    user = result.data[0]
    if bcrypt.checkpw(password.encode(), user["user_password"].encode()):
        return {"success": True, "user": user}
    else:
        return {"success": False, "message": "Incorrect password"}
    


def encode_signature_to_base64(signature_path):
    with open(signature_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")
        return encoded

def sync_to_cloud():
    """
    Push unsynced local changes to Supabase.
    """
    if not supabase:
        print("Sync skipped: Supabase client not initialized")
        return False

    unsynced = local_db.get_unsynced()
    if not unsynced:
        return True

    print(f"Syncing {len(unsynced)} records...")
    for record in unsynced:
        try:
            # Parse form_data back to JSON for sending, or send as is if Supabase expects JSONB? 
            # Supabase-py handles dict -> jsonb autoconversion usually.
            # But local_db stores it as string.
            
            payload = {
                "id": record["id"],
                "user_id": record["user_id"], # Ensure this is a valid UUID or None
                "device_id": record["device_id"],
                "form_type": record["form_type"],
                "patient_name": record["patient_name"],
                "patient_identifier": record["patient_identifier"],
                "form_data": json.loads(record["form_data"]), # Convert string back to dict
                "created_at": record["created_at"],
                "updated_at": record["updated_at"],
                "is_deleted": bool(record["is_deleted"])
            }
            
            # Upsert to Supabase
            supabase.table("submissions").upsert(payload).execute()
            
            # Mark synced locally
            local_db.mark_synced(record["id"])
            print(f"Synced {record['id']}")
            
        except Exception as e:
            print(f"Failed to sync {record['id']}: {e}")
            return False
            
    return True
