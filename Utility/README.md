# `Utility/` — Support Modules

Backend support classes shared across the application.

## Files

### `local_db.py` — The Data Backbone

**Class:** `LocalDB` (singleton instance exported as `local_db`)

The central data persistence layer using SQLite3. Manages five tables:

| Table | Purpose | Primary Key |
|-------|---------|-------------|
| `submissions` | Form data (JSON blob) with sync tracking | ULID |
| `users` | Cached login credentials for offline auth | UUID (from Supabase) |
| `companies` | Registered companies | ULID |
| `employees` | Employees linked to companies (FK) | ULID |
| `documents` | Metadata for generated PDFs | ULID |

**Key Methods:**
- `save_submission()` — Upsert with ULID, serializes form data as JSON, sets `last_synced_at = NULL`
- `get_unsynced()` / `mark_synced()` — Sync queue management
- `upsert_user()` — Cache cloud credentials locally
- Company/Employee CRUD — Full create/read/update/delete operations
- `record_document()` — Log generated PDF metadata

**Design Decisions:**
- Uses `check_same_thread=False` for SQLite (needed because sync runs on background threads)
- Hides the DB file on Windows via `ctypes.windll.kernel32.SetFileAttributesW`
- `_sanitize_folder_name()` strips special chars for file-system-safe names

---

### `form_factory.py` — Schema-Driven Form Builder

**Classes:** `FormWidget`, `FormFactory`

Accepts a JSON schema and dynamically generates a PyQt5 form with:
- Field types: `text`, `textarea`, `date`, `signature`
- Built-in validation for required fields
- Submit/Generate PDF/Back action buttons
- Automatic signature temp file management

**Note:** This factory is an architectural foundation but is **not used by the 11 production form classes** in `pages/forms/`. Those forms require custom UI elements (medication tables, test-result dropdowns) that exceed the factory's schema capabilities.

---

### `file_manager.py` — PDF Output Organization

**Class:** `FileManager` (singleton instance exported as `file_manager`)

Manages the `outputs/` folder hierarchy:

```
outputs/
  └── {company_folder_name}/
        └── {employee_folder_name}/
              └── {form_type}_{YYYY-MM-DD}.pdf
```

**Key Methods:**
- `get_full_pdf_path()` — Returns `(absolute_path, relative_path, filename)` with automatic deduplication (appends `_1`, `_2`, etc.)
- `sanitize_name()` — Removes filesystem-unsafe characters

---

### `app_context.py` — Resource Path Resolver

**Function:** `get_resource_path(relative_path)`

Resolves file paths for both:
- **Development:** Uses `os.path.abspath(".")`
- **PyInstaller bundle:** Uses `sys._MEIPASS` (the temp extract directory)

Used for loading `.env`, themes, templates, and assets.

## Interdependencies

- `local_db.py` depends on: `ulid`, `sqlite3`, `uuid`, `platform`
- `form_factory.py` depends on: `pages.signiture.SignaturePad`, `pages.template_generator`
- `file_manager.py` is standalone (no project dependencies)
- `app_context.py` is standalone
