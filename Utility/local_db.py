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
        
        user_query = """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            password_hash TEXT,
            role TEXT DEFAULT 'user',
            last_login_at TEXT
        )
        """
        self.conn.execute(user_query)
        self.conn.commit()
        
        # Companies table
        companies_query = """
        CREATE TABLE IF NOT EXISTS companies (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            folder_name TEXT NOT NULL,
            contact_email TEXT,
            contact_phone TEXT,
            address TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
        self.conn.execute(companies_query)
        self.conn.commit()
        
        # Employees table
        employees_query = """
        CREATE TABLE IF NOT EXISTS employees (
            id TEXT PRIMARY KEY,
            company_id TEXT REFERENCES companies(id),
            full_name TEXT NOT NULL,
            id_number TEXT NOT NULL UNIQUE,
            job_title TEXT,
            department TEXT,
            folder_name TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT
        )
        """
        self.conn.execute(employees_query)
        self.conn.commit()
        
        # Documents table
        documents_query = """
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            employee_id TEXT REFERENCES employees(id),
            submission_id TEXT,
            form_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_name TEXT NOT NULL,
            generated_at TEXT,
            generated_by TEXT
        )
        """
        self.conn.execute(documents_query)
        self.conn.commit()

    def upsert_user(self, user_data):
        """
        Cache user data locally.
        Expected keys: id, email, password, role (optional)
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # Check if we are storing a raw password or a hash. 
        # The Implementation Plan implies we might need to hash it if it comes from the UI.
        # But if we want to validte offline, we need the hash.
        # For this simple "cache" method, we assume the caller handles hashing if needed, 
        # OR we just store what we get. 
        # The prompt said: "local_data.db to act as the local cache... store a hash of the password even if Supabase manages auth"
        
        query = """
        INSERT INTO users (id, email, password_hash, role, last_login_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            email = excluded.email,
            password_hash = excluded.password_hash,
            role = excluded.role,
            last_login_at = excluded.last_login_at
        """
        self.conn.execute(query, (
            user_data.get("id"),
            user_data.get("email"),
            user_data.get("password_hash"), # Caller must provide the hash
            user_data.get("role", "user"),
            now_iso
        ))
        self.conn.commit()

    def get_user_by_email(self, email):
        cursor = self.conn.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

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

    # ============== COMPANY METHODS ==============
    
    def _sanitize_folder_name(self, name: str) -> str:
        """Remove special chars, replace spaces with underscores"""
        import re
        sanitized = re.sub(r'[^\w\s-]', '', name)  # Remove special chars
        sanitized = re.sub(r'\s+', '_', sanitized)  # Replace spaces with underscores
        return sanitized.strip('_')
    
    def create_company(self, name: str, contact_email: str = None, 
                       contact_phone: str = None, address: str = None) -> str:
        """Create a new company. Returns company ID."""
        now_iso = datetime.now(timezone.utc).isoformat()
        company_id = str(ulid.ULID())
        folder_name = self._sanitize_folder_name(name)
        
        query = """
        INSERT INTO companies (id, name, folder_name, contact_email, contact_phone, address, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(query, (company_id, name, folder_name, contact_email, contact_phone, address, now_iso, now_iso))
        self.conn.commit()
        return company_id
    
    def get_company(self, company_id: str) -> dict:
        """Get a company by ID."""
        cursor = self.conn.execute("SELECT * FROM companies WHERE id = ?", (company_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_company_by_name(self, name: str) -> dict:
        """Get a company by name."""
        cursor = self.conn.execute("SELECT * FROM companies WHERE name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_companies(self) -> list:
        """Get all companies."""
        cursor = self.conn.execute("SELECT * FROM companies ORDER BY name")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def update_company(self, company_id: str, **kwargs) -> bool:
        """Update company fields."""
        now_iso = datetime.now(timezone.utc).isoformat()
        allowed_fields = ['name', 'contact_email', 'contact_phone', 'address']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if 'name' in updates:
            updates['folder_name'] = self._sanitize_folder_name(updates['name'])
        
        if not updates:
            return False
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [now_iso, company_id]
        
        query = f"UPDATE companies SET {set_clause}, updated_at = ? WHERE id = ?"
        self.conn.execute(query, values)
        self.conn.commit()
        return True
    
    def delete_company(self, company_id: str) -> bool:
        """Delete a company (only if no employees linked)."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM employees WHERE company_id = ?", (company_id,))
        count = cursor.fetchone()[0]
        if count > 0:
            return False  # Can't delete company with employees
        
        self.conn.execute("DELETE FROM companies WHERE id = ?", (company_id,))
        self.conn.commit()
        return True

    # ============== EMPLOYEE METHODS ==============
    
    def create_employee(self, company_id: str, full_name: str, id_number: str,
                        job_title: str = None, department: str = None) -> str:
        """Create a new employee. Returns employee ID."""
        now_iso = datetime.now(timezone.utc).isoformat()
        employee_id = str(ulid.ULID())
        folder_name = f"{self._sanitize_folder_name(full_name)}_{id_number}"
        
        query = """
        INSERT INTO employees (id, company_id, full_name, id_number, job_title, department, folder_name, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(query, (employee_id, company_id, full_name, id_number, job_title, department, folder_name, now_iso, now_iso))
        self.conn.commit()
        return employee_id
    
    def get_employee(self, employee_id: str) -> dict:
        """Get an employee by ID with company info."""
        query = """
        SELECT e.*, c.name as company_name, c.folder_name as company_folder
        FROM employees e
        LEFT JOIN companies c ON e.company_id = c.id
        WHERE e.id = ?
        """
        cursor = self.conn.execute(query, (employee_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_employee_by_id_number(self, id_number: str) -> dict:
        """Get an employee by ID number."""
        query = """
        SELECT e.*, c.name as company_name, c.folder_name as company_folder
        FROM employees e
        LEFT JOIN companies c ON e.company_id = c.id
        WHERE e.id_number = ?
        """
        cursor = self.conn.execute(query, (id_number,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_employees_by_company(self, company_id: str) -> list:
        """Get all employees for a company."""
        cursor = self.conn.execute("SELECT * FROM employees WHERE company_id = ? ORDER BY full_name", (company_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_all_employees(self) -> list:
        """Get all employees with company info."""
        query = """
        SELECT e.*, c.name as company_name
        FROM employees e
        LEFT JOIN companies c ON e.company_id = c.id
        ORDER BY c.name, e.full_name
        """
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def update_employee(self, employee_id: str, **kwargs) -> bool:
        """Update employee fields."""
        now_iso = datetime.now(timezone.utc).isoformat()
        allowed_fields = ['company_id', 'full_name', 'id_number', 'job_title', 'department']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if 'full_name' in updates or 'id_number' in updates:
            # Need current values to rebuild folder name
            current = self.get_employee(employee_id)
            if current:
                name = updates.get('full_name', current['full_name'])
                id_num = updates.get('id_number', current['id_number'])
                updates['folder_name'] = f"{self._sanitize_folder_name(name)}_{id_num}"
        
        if not updates:
            return False
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [now_iso, employee_id]
        
        query = f"UPDATE employees SET {set_clause}, updated_at = ? WHERE id = ?"
        self.conn.execute(query, values)
        self.conn.commit()
        return True
    
    def delete_employee(self, employee_id: str) -> bool:
        """Delete an employee."""
        self.conn.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
        self.conn.commit()
        return True

    # ============== DOCUMENT METHODS ==============
    
    def record_document(self, employee_id: str, form_type: str, file_path: str, 
                        file_name: str, submission_id: str = None, generated_by: str = None) -> str:
        """Record a generated PDF document. Returns document ID."""
        now_iso = datetime.now(timezone.utc).isoformat()
        doc_id = str(ulid.ULID())
        
        query = """
        INSERT INTO documents (id, employee_id, submission_id, form_type, file_path, file_name, generated_at, generated_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(query, (doc_id, employee_id, submission_id, form_type, file_path, file_name, now_iso, generated_by))
        self.conn.commit()
        return doc_id
    
    def get_employee_documents(self, employee_id: str) -> list:
        """Get all documents for an employee."""
        cursor = self.conn.execute("SELECT * FROM documents WHERE employee_id = ? ORDER BY generated_at DESC", (employee_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_document(self, doc_id: str) -> dict:
        """Get a document by ID."""
        cursor = self.conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def close(self):
        self.conn.close()

# Singleton instance
local_db = LocalDB()
