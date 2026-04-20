import json
import os
import bcrypt
import base64
import sqlite3
import logging
import sys
from dotenv import load_dotenv
from supabase import create_client
from Utility.local_db import local_db
from Utility.app_context import get_resource_path

# Setup logging
log_path = os.path.join(os.getcwd(), 'app_debug.log')
logging.basicConfig(filename=log_path, level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Load env from resource path
env_path = get_resource_path(".env")
logging.info(f"Loading .env from: {env_path}")
load_dotenv(dotenv_path=env_path)

url = os.getenv("SUPERBASE_URL")
key = os.getenv("SUPERBASE_API_KEY")

try:
    if not url or not key:
        logging.error("Supabase URL or Key missing from environment variables")
        raise ValueError("Missing Supabase credentials")
        
    logging.info(f"Connecting to Supabase at: {url}")
    supabase = create_client(url, key)
    logging.info("Supabase client initialized")
except Exception as e:
    logging.error(f"Supabase init failed: {e}")
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
    # 1. Try Online Login (Supabase)
    if supabase:
        try:
            print("Attempting Online Login...")
            logging.info(f"Attempting online login for: {email}")
            result = supabase.table("users").select("*").eq("user_email", email).execute()
            
            if result.data:
                user = result.data[0]
                # Verify password against cloud hash
                if bcrypt.checkpw(password.encode(), user["user_password"].encode()):
                    # Success: Cache to local DB
                    # Map Supabase fields to Local keys if needed, assuming one-to-one for now based on previous code
                    # The local_db.upsert_user expects: id, email, password_hash, role
                    # The custom table has: user_email, user_password, user_role (presumably, code said 'user_role': 'Regular')
                    # We need a UUID. The existing code didn't show an ID column in the insert, 
                    # but Supabase tables usually have an 'id'. Let's assume 'id' exists or use email as fallback for ID if missing 
                    # (though UUID is better).
                    
                    user_id = user.get("id") or user.get("user_id") # Handle potential column naming
                    # If we truly don't have an ID, we might have issues. But let's assume standard Supabase row.
                    
                    local_user_data = {
                        "id": str(user_id) if user_id else email, # Fallback to email if no ID found to prevent crash
                        "email": user["user_email"],
                        "password_hash": user["user_password"],
                        "role": user.get("user_role", "user")
                    }
                    local_db.upsert_user(local_user_data)
                    return {"success": True, "user": user, "mode": "online"}
                else:
                    return {"success": False, "message": "Incorrect password"}
            else:
                # Email not found online, check if it's a first time wrong email or just not there
                pass 
                # Fall through to check offline? 
                # No, if we are online and email doesn't exist, it doesn't exist.
                # UNLESS we are "online" but the user was created offline? 
                # But requirement says "Admin-Only Provisioning" so users exist on cloud first.
                return {"success": False, "message": "Email not found (Online)"}

        except Exception as e:
            msg = f"Online login failed (connection issue?): {e}"
            print(msg)
            logging.error(msg)
            # Fall through to offline handling
    
    # 2. Offline Fallback
    print("Attempting Offline Login...")
    logging.info("Attempting offline login...")
    local_user = local_db.get_user_by_email(email)
    
    if local_user:
        # Verify password against cached hash
        stored_hash = local_user["password_hash"]
        if bcrypt.checkpw(password.encode(), stored_hash.encode()):
             return {"success": True, "user": local_user, "mode": "offline"}
        else:
             return {"success": False, "message": "Incorrect password (Offline)"}
    else:
        return {"success": False, "message": "Login failed. If this is a new device, you must be online for the first login."}
    


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


def sync_company_templates_to_cloud(company_id: str) -> bool:
    """
    Push unsynced company_templates rows for this company to Supabase.
    Follows the same last_synced_at IS NULL pattern as sync_to_cloud().
    Call in a background thread after save_company_template().
    """
    if not supabase:
        return False

    unsynced = local_db.get_unsynced_company_templates(company_id)
    if not unsynced:
        return True

    for record in unsynced:
        try:
            payload = {
                "id":           record["id"],
                "company_id":   record["company_id"],
                "form_type":    record["form_type"],
                "field_key":    record["field_key"],
                "field_value":  record["field_value"],
                "field_label":  record["field_label"],
                "is_locked":    bool(record["is_locked"]),
                "last_updated": record["last_updated"],
            }
            supabase.table("company_templates").upsert(payload).execute()
            local_db.mark_template_synced(record["id"])
            print(f"Synced template record {record['id']}")
        except Exception as e:
            print(f"Failed to sync template record {record['id']}: {e}")
            return False

    return True
