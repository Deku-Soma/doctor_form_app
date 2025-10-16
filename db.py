from dotenv import load_dotenv
import os 
from supabase import create_client
import bcrypt
import base64
import sqlite3

load_dotenv(dotenv_path=".env")  # Optional: give full path if needed

url = os.getenv("SUPERBASE_URL")
key = os.getenv("SUPERBASE_API_KEY")

supabase = create_client(url, key)


def create_user(email: str, password: str, username: str = "") -> dict:
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    data = {
        "user_email": email,
        "user_password": hashed_pw,
        "user_name": username,
        "user_role":"Regular"
    }
    result = supabase.table("users").insert(data).execute()
    return result


def validate_login(email: str, password: str) -> dict:
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
