import sqlite3
import json
import os
import ulid
import platform
import uuid
from datetime import datetime, timezone

DB_NAME = "local_data.db"
DEVICE_ID_FILE = "device_id.txt"

class LocalDB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_table()
        self.device_id = self._get_or_create_device_id()

    def _create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS submissions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            device_id TEXT,
            form_type TEXT,
            patient_name TEXT,
            patient_identifier TEXT,
            form_data TEXT,
            created_at TEXT,
            updated_at TEXT,
            is_deleted INTEGER DEFAULT 0,
            last_synced_at TEXT
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def _get_or_create_device_id(self):
        if os.path.exists(DEVICE_ID_FILE):
            with open(DEVICE_ID_FILE, "r") as f:
                return f.read().strip()
        
        # unique enough for our needs: hostname + random uuid
        new_id = f"{platform.node()}_{uuid.uuid4().hex[:8]}"
        with open(DEVICE_ID_FILE, "w") as f:
            f.write(new_id)
        return new_id

    def save_submission(self, form_type, data, user_id=None):
        """
        Saves a completely new submission or updates an existing one if 'id' is in data.
        Returns the ID (ULID).
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # If ID exists, it's an update, otherwise new
        sub_id = data.get("id")
        if not sub_id:
            sub_id = str(ulid.ULID())
            data["id"] = sub_id
        
        # Extract searchable fields
        patient_name = f"{data.get('name', '')} {data.get('surname', '')}".strip()
        patient_identifier = data.get("id_number", "")
        
        # JSON dump
        json_data = json.dumps(data)

        query = """
        INSERT INTO submissions (
            id, user_id, device_id, form_type, 
            patient_name, patient_identifier, form_data, 
            created_at, updated_at, last_synced_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
        ON CONFLICT(id) DO UPDATE SET
            form_data = excluded.form_data,
            updated_at = excluded.updated_at,
            patient_name = excluded.patient_name,
            patient_identifier = excluded.patient_identifier,
            last_synced_at = NULL
        """
        
        self.conn.execute(query, (
            sub_id, user_id, self.device_id, form_type,
            patient_name, patient_identifier, json_data,
            now_iso, now_iso
        ))
        self.conn.commit()
        return sub_id

    def get_unsynced(self):
        cursor = self.conn.execute("SELECT * FROM submissions WHERE last_synced_at IS NULL")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def mark_synced(self, sub_id):
        now_iso = datetime.now(timezone.utc).isoformat()
        self.conn.execute("UPDATE submissions SET last_synced_at = ? WHERE id = ?", (now_iso, sub_id))
        self.conn.commit()

    def close(self):
        self.conn.close()

# Singleton instance
local_db = LocalDB()
