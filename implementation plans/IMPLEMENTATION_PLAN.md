# HealthCorp360 — Implementation Plan

> This document targets the actual codebase. Each feature section contains context, file targets, schema changes, and step-by-step tasks. Work through features in the order shown at the bottom — Feature 2 and 3 share a database dependency that must be built first.

---

## Table of Contents

1. [Feature 1 — Android Tablet Port](#feature-1--android-tablet-port)
2. [Feature 2 — Company Form Templates](#feature-2--company-form-templates)
3. [Feature 3 — Cross-Form Autofill](#feature-3--cross-form-autofill)
4. [Feature 4 — Dynamic Stamp Positioning](#feature-4--dynamic-stamp-positioning)

---

## Feature 1 — Android Tablet Port

### Strategy: Local Server + WebView (Recommended)

Rather than rewriting the PyQt5 UI in a new framework, the recommended approach is to:
- Keep all existing Python business logic (`db.py`, `Utility/local_db.py`, form logic, PDF generation) **unchanged**
- Replace the PyQt5 UI layer with a **FastAPI local server** serving HTML/JS pages
- On Android, run the Python server via **Chaquopy** (Android Studio plugin that runs Python inside an APK) and render the UI in a **WebView**

This means your existing Supabase sync, SQLite, WeasyPrint PDF pipeline, and all form logic carries over without modification.

> **⚠️ WeasyPrint on Android — Critical Risk**
>
> WeasyPrint requires native C libraries (Cairo, Pango, GLib) that are not trivially bundled on Android ARM via Chaquopy. Before committing to WeasyPrint for Android, verify availability of pre-built wheels for `arm64-v8a`. **If unavailable, use `reportlab` for Android PDF generation** — it is already in `requirements.txt` and is pure-Python. The desktop build can retain WeasyPrint.

> **⚠️ SQLite path on Android**
>
> `local_db.py` opens the database with `sqlite3.connect("local_data.db")` — a relative path that resolves to the current working directory. On Android, the writable directory is `context.filesDir`, not the APK root. In `MainActivity.kt`, pass the correct writable path to Python before initialising the server:
> ```kotlin
> Python.getInstance().getModule("set_db_path").callAttr("set_path", filesDir.absolutePath)
> ```
> Add a `set_db_path.py` shim that updates `local_db.DB_NAME` before the singleton is created.

> **⚠️ Keep PyQt5 during the transition**
>
> Do **not** remove `PyQt5` from `requirements.txt` until Feature 1 is fully working on Android and the desktop app is confirmed no longer needed. The two builds can co-exist by using a `BUILD_TARGET` environment variable to switch entry points.

### Architecture After Change

```
Android APK (Chaquopy)
├── Python backend (FastAPI, port 8765)
│   ├── main_server.py          ← replaces main.py
│   ├── set_db_path.py          ← Android DB path shim (new)
│   ├── db.py                   ← unchanged
│   ├── Utility/local_db.py     ← unchanged (path shim handles DB location)
│   ├── Utility/file_manager.py ← unchanged
│   ├── pages/forms/            ← logic extracted, UI removed
│   └── pages/template_generator.py  ← unchanged
└── WebView (Android)
    └── web_ui/
        ├── index.html          ← login
        ├── home.html           ← dashboard
        ├── company.html        ← company CRUD
        ├── employee.html       ← employee CRUD
        ├── forms/              ← one HTML file per form type
        └── static/
            ├── app.js          ← shared fetch helpers, auth state
            ├── styles.css      ← tablet-optimised stylesheet
            └── signature.js    ← canvas signature capture
```

### New Files to Create

| File | Purpose |
|------|---------|
| `main_server.py` | FastAPI app entry point. Mounts all routers. Runs on `localhost:8765`. |
| `set_db_path.py` | Android shim — called from Kotlin before server starts to set writable DB path. |
| `routers/auth.py` | `POST /login`, `POST /logout`. Wraps `db.validate_login()`. |
| `routers/companies.py` | `GET/POST/PUT/DELETE /companies`. Wraps `local_db` company methods. |
| `routers/employees.py` | `GET/POST/PUT/DELETE /employees` and `GET /employees/{company_id}/list`. Wraps `local_db` employee methods. |
| `routers/forms.py` | `POST /forms/{form_type}/submit`. Accepts JSON body, calls extracted `process_submission()`, triggers PDF. |
| `routers/documents.py` | `GET /documents/{employee_id}`. Returns list of PDF records from `local_db.get_employee_documents()`. |
| `web_ui/static/app.js` | Shared JS: `apiFetch()` wrapper, session token storage, nav helpers. |
| `web_ui/static/styles.css` | Tablet-first CSS. Minimum tap target 48px. Large labels. Touch-friendly inputs. |
| `web_ui/static/signature.js` | Canvas-based signature capture. Exports base64 PNG. Replaces `pages/signiture.py`. |

### Files to Modify

| File | Change |
|------|--------|
| `pages/forms/*.py` (all 11) | Extract the data-dict building and PDF call into a standalone `process_submission(employee_id, company_id, data: dict, status: str) -> dict` function. Leave the PyQt5 class intact. |
| `requirements.txt` | Add: `fastapi`, `uvicorn[standard]`. Do **not** remove `PyQt5` yet. |

### Step-by-Step Tasks

**Step 1 — Refactor form logic out of PyQt5 classes**

For each file in `pages/forms/`:
- Find the `submit_form()` method (it currently takes `status="approved"` or `status="pending"`)
- Extract the data-dict construction + `local_db.save_submission()` + `generate_pdf_for_form()` into a standalone module-level function:
  ```python
  def process_submission(employee_id: str, company_id: str, data: dict, status: str = "approved") -> dict:
      """Framework-agnostic submission handler. Called by both PyQt5 submit_form() and the FastAPI router."""
      try:
          from Utility.local_db import local_db
          from pages.template_generator import generate_pdf_for_form
          import db, threading
          sub_id = local_db.save_submission(FORM_TYPE, data, user_id=None)
          threading.Thread(target=db.sync_to_cloud).start()
          emp_data = local_db.get_employee(employee_id) if employee_id else None
          generate_pdf_for_form(FORM_TYPE, data, employee_data=emp_data, status=status)
          return {"success": True, "submission_id": sub_id, "error": None}
      except Exception as e:
          return {"success": False, "submission_id": None, "error": str(e)}
  ```
- The existing PyQt5 `submit_form()` method can then delegate to `process_submission()`.
- Note: `FORM_TYPE` should match the keys in `pages/template_generator.py`'s `TEMPLATE_MAP` dict (e.g. `"workplace_drug_testing"`, not `"drug_testing"`).

**Step 2 — Create `main_server.py`**

```python
# main_server.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

from routers import auth, companies, employees, forms, documents
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(employees.router)
app.include_router(forms.router)
app.include_router(documents.router)

app.mount("/", StaticFiles(directory="web_ui", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765)
```

**Step 3 — Build the web UI shell**

Create `web_ui/index.html` with:
- Email + password fields (min height 56px for touch)
- Submit button (full width, 56px tall)
- Error message div
- Calls `POST /login`, stores session token in memory, redirects to `home.html`

Create `web_ui/home.html` with:
- Card grid matching existing form categories (Consent, Questionnaires, Certificates)
- Employee selector per card before opening the form page
- Search bar filtering cards client-side

**Step 4 — Build the signature capture widget (`web_ui/static/signature.js`)**

```javascript
// Initialise on any <canvas id="sig-pad"> element
function initSignaturePad(canvasId) {
    const canvas = document.getElementById(canvasId);
    const ctx = canvas.getContext('2d');
    let drawing = false;
    canvas.addEventListener('pointerdown', e => { drawing = true; ctx.beginPath(); ctx.moveTo(...pos(e, canvas)); });
    canvas.addEventListener('pointermove', e => { if (!drawing) return; ctx.lineTo(...pos(e, canvas)); ctx.stroke(); });
    canvas.addEventListener('pointerup', () => drawing = false);
    return {
        toBase64: () => canvas.toDataURL('image/png').split(',')[1],
        clear: () => ctx.clearRect(0, 0, canvas.width, canvas.height),
        isEmpty: () => !ctx.getImageData(0,0,canvas.width,canvas.height).data.some(x => x !== 0)
    };
}
function pos(e, canvas) {
    const r = canvas.getBoundingClientRect();
    return [e.clientX - r.left, e.clientY - r.top];
}
```

**Step 5 — Create tablet-optimised CSS**

Key rules for `web_ui/static/styles.css`:
```css
/* Tablet baseline — targets 768px+ landscape Android */
:root { --tap: 48px; --font-base: 16px; --radius: 12px; }
input, select, textarea { min-height: var(--tap); font-size: var(--font-base); border-radius: var(--radius); padding: 10px 14px; width: 100%; box-sizing: border-box; }
button { min-height: var(--tap); font-size: var(--font-base); border-radius: var(--radius); padding: 0 24px; cursor: pointer; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
```

**Step 6 — Android packaging with Chaquopy**

- Create a new Android Studio project
- Add Chaquopy to `build.gradle`:
  ```groovy
  python { pip { install "fastapi"; install "uvicorn"; install "supabase"; install "bcrypt"; install "jinja2"; install "reportlab"; } }
  ```
  > Note: Use `reportlab` instead of `weasyprint` here — WeasyPrint requires native C libraries not available on Android ARM.
- In `MainActivity.kt`:
  1. Set the DB path before Python initialises: pass `filesDir.absolutePath` to `set_db_path.py`
  2. Start the FastAPI server in a background thread
  3. Load `http://127.0.0.1:8765` in a `WebView`
  4. Set `webView.settings.javaScriptEnabled = true` and `webView.settings.domStorageEnabled = true`

### Testing Checklist

- [ ] Login works offline (SQLite cached credentials)
- [ ] Login works online (Supabase)
- [ ] Company and employee CRUD round-trips correctly
- [ ] All 11 forms submit and generate a PDF
- [ ] Signature capture exports valid base64 PNG
- [ ] PDF appears in `outputs/{company}/{employee}/` on device storage
- [ ] Supabase sync fires in background after submission

---

## Feature 2 — Company Form Templates

### Overview

When a practitioner completes the first employee's form for a given company, the system captures company-level field values (hazard exposure, industry risk profile, practitioner info, stamp/logo details) and stores them as a reusable template. Every subsequent employee at that company gets those fields pre-filled.

Templates are stored in SQLite (and synced to Supabase). They are editable from `pages/company_page.py`.

### Database Changes

**New SQLite table — add to `Utility/local_db.py` inside `_create_table()` (note: existing method is called `_create_table`, not `_create_tables`):**

```sql
CREATE TABLE IF NOT EXISTS company_templates (
    id TEXT PRIMARY KEY,                  -- ULID
    company_id TEXT NOT NULL,
    form_type TEXT NOT NULL,              -- matches keys in TEMPLATE_MAP, e.g. "workplace_drug_testing"
    field_key TEXT NOT NULL,              -- matches a field name in the form data dict
    field_value TEXT,                     -- stored as string; cast on retrieval
    field_label TEXT,                     -- human-readable label for UI display
    is_locked INTEGER DEFAULT 0,          -- 1 = pre-filled and read-only on form
    last_updated TEXT,
    last_synced_at TEXT,
    UNIQUE(company_id, form_type, field_key)
);
```

**New Supabase table — run this in the Supabase SQL editor:**

```sql
CREATE TABLE company_templates (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id),
    form_type TEXT NOT NULL,
    field_key TEXT NOT NULL,
    field_value TEXT,
    field_label TEXT,
    is_locked INTEGER DEFAULT 0,
    last_updated TIMESTAMPTZ,
    last_synced_at TIMESTAMPTZ,
    UNIQUE(company_id, form_type, field_key)
);
```

### New Methods to Add to `Utility/local_db.py`

Add these inside the `LocalDB` class, following the same style as existing methods (using `ON CONFLICT ... DO UPDATE` for upserts):

```python
def save_company_template(self, company_id: str, form_type: str, fields: dict):
    """
    Upsert template fields for a company+form combination.
    `fields` is a dict of {field_key: {"value": ..., "label": ..., "is_locked": bool}}
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    for field_key, meta in fields.items():
        record_id = str(ulid.ULID())
        query = """
        INSERT INTO company_templates
            (id, company_id, form_type, field_key, field_value, field_label, is_locked, last_updated, last_synced_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)
        ON CONFLICT(company_id, form_type, field_key) DO UPDATE SET
            field_value    = excluded.field_value,
            field_label    = excluded.field_label,
            is_locked      = excluded.is_locked,
            last_updated   = excluded.last_updated,
            last_synced_at = NULL
        """
        self.conn.execute(query, (
            record_id, company_id, form_type, field_key,
            str(meta["value"]), meta.get("label", field_key.replace("_", " ").title()),
            1 if meta.get("is_locked") else 0,
            now_iso
        ))
    self.conn.commit()

def get_company_template(self, company_id: str, form_type: str) -> dict:
    """
    Returns {field_key: {"value": ..., "label": ..., "is_locked": bool}}
    Returns empty dict if no template exists yet.
    """
    cursor = self.conn.execute(
        "SELECT field_key, field_value, field_label, is_locked FROM company_templates "
        "WHERE company_id = ? AND form_type = ?",
        (company_id, form_type)
    )
    rows = cursor.fetchall()
    return {
        row["field_key"]: {
            "value": row["field_value"],
            "label": row["field_label"],
            "is_locked": bool(row["is_locked"])
        }
        for row in rows
    }

def list_company_templates(self, company_id: str) -> list:
    """
    Returns list of distinct form_type strings that have a saved template for this company.
    """
    cursor = self.conn.execute(
        "SELECT DISTINCT form_type FROM company_templates WHERE company_id = ? ORDER BY form_type",
        (company_id,)
    )
    return [row["form_type"] for row in cursor.fetchall()]

def get_unsynced_company_templates(self, company_id: str) -> list:
    """Used by sync to find rows not yet pushed to Supabase."""
    cursor = self.conn.execute(
        "SELECT * FROM company_templates WHERE company_id = ? AND last_synced_at IS NULL",
        (company_id,)
    )
    return [dict(row) for row in cursor.fetchall()]

def mark_template_synced(self, record_id: str):
    now_iso = datetime.now(timezone.utc).isoformat()
    self.conn.execute(
        "UPDATE company_templates SET last_synced_at = ? WHERE id = ?",
        (now_iso, record_id)
    )
    self.conn.commit()

def delete_company_template_field(self, company_id: str, form_type: str, field_key: str):
    """Remove a single field from a company template."""
    self.conn.execute(
        "DELETE FROM company_templates WHERE company_id = ? AND form_type = ? AND field_key = ?",
        (company_id, form_type, field_key)
    )
    self.conn.commit()
```

### New Method to Add to `db.py`

Add this standalone function alongside the existing `sync_to_cloud()`. It follows the same `last_synced_at IS NULL` + upsert pattern:

```python
def sync_company_templates_to_cloud(company_id: str):
    """
    Push unsynced company_templates rows for this company to Supabase.
    Call in a background thread after save_company_template().
    """
    if not supabase:
        return False
    unsynced = local_db.get_unsynced_company_templates(company_id)
    for record in unsynced:
        try:
            payload = {
                "id":             record["id"],
                "company_id":     record["company_id"],
                "form_type":      record["form_type"],
                "field_key":      record["field_key"],
                "field_value":    record["field_value"],
                "field_label":    record["field_label"],
                "is_locked":      bool(record["is_locked"]),
                "last_updated":   record["last_updated"],
            }
            supabase.table("company_templates").upsert(payload).execute()
            local_db.mark_template_synced(record["id"])
        except Exception as e:
            print(f"Failed to sync template record {record['id']}: {e}")
    return True
```

### Fields to Capture Per Form Type

Define this mapping in a new file `Utility/template_fields.py`.

> **Important:** `form_type` keys here must match the keys in `pages/template_generator.py`'s `TEMPLATE_MAP` exactly (e.g. `"workplace_drug_testing"`, not `"drug_testing"`).

```python
# Utility/template_fields.py

# Maps form_type -> list of field keys that are company-level (not employee-specific)
COMPANY_TEMPLATE_FIELDS = {
    "workplace_drug_testing": [
        "practitioner_name", "practitioner_reg_no", "clinic_name",
        "hazard_exposure", "reason_for_test"
    ],
    "certificate_of_fitness": [
        "practitioner_name", "practitioner_reg_no", "clinic_name",
        "job_title", "hazard_categories", "industry_type"
    ],
    "heights_questionnaire": [
        "practitioner_name", "hazard_exposure", "work_at_heights_category"
    ],
    "hot_cold_exposure": [
        "practitioner_name", "exposure_type", "environment_description"
    ],
    "confined_spaces_questionnaire": [
        "practitioner_name", "space_classification", "hazard_exposure"
    ],
    "musculoskeletal_questionnaire": [
        "practitioner_name", "job_category", "physical_demands_rating"
    ],
    "psychology_questionnaire": [
        "practitioner_name", "assessment_context"
    ],
    "cwb_medical_referral": [
        "practitioner_name", "clinic_name", "referral_reason"
    ],
    "complete_wellbeing": [
        "practitioner_name", "clinic_name", "industry_type"
    ],
    "annexure3_cwb": [
        "practitioner_name", "practitioner_reg_no", "clinic_name"
    ],
    "vitamin_b_consent": [
        "practitioner_name", "clinic_name"
    ],
}

# Fields that apply to ALL form types (always included in template capture)
UNIVERSAL_TEMPLATE_FIELDS = [
    "practitioner_name",
    "practitioner_reg_no",
    "clinic_name",
    "clinic_address",
    "clinic_phone",
]
```

### Template Capture Logic

**Add this standalone function (not inside any class) to each form file, below the imports. Call it at the end of a successful `submit_form()` (or inside `process_submission()` if refactored):**

```python
import threading
import ulid  # already imported in local_db; add to form file if not present
from Utility.template_fields import COMPANY_TEMPLATE_FIELDS, UNIVERSAL_TEMPLATE_FIELDS

def _capture_company_template_if_first(company_id: str, form_type: str, data: dict):
    """
    After a successful submission, save company-level fields as a template.
    Only saves if no template exists yet for this company+form_type combination.
    Runs in the calling thread (fast — just a SQLite read/write).
    """
    if not company_id:
        return
    existing = local_db.get_company_template(company_id, form_type)
    if existing:
        return  # Template already captured — don't overwrite

    capturable_keys = list(set(
        COMPANY_TEMPLATE_FIELDS.get(form_type, []) + UNIVERSAL_TEMPLATE_FIELDS
    ))
    fields_to_save = {}

    # data may be a flat dict or contain nested dicts — try both
    def _get(d, key):
        if key in d:
            return d[key]
        for v in d.values():
            if isinstance(v, dict) and key in v:
                return v[key]
        return None

    for key in capturable_keys:
        value = _get(data, key)
        if value:
            fields_to_save[key] = {
                "value": value,
                "label": key.replace("_", " ").title(),
                "is_locked": False
            }

    if fields_to_save:
        local_db.save_company_template(company_id, form_type, fields_to_save)
        threading.Thread(
            target=sync_company_templates_to_cloud, args=(company_id,), daemon=True
        ).start()
```

> **Note:** Import `sync_company_templates_to_cloud` from `db` at the top of the form file: `from db import sync_company_templates_to_cloud`.

### `is_locked` Behaviour — Decision Required

The `is_locked` flag controls how pre-filled fields look and behave on the form. **Choose one of the two behaviours below before implementing Feature 3:**

| Option | Behaviour | Implementation |
|--------|-----------|----------------|
| **A — Visual only** (recommended) | Field is pre-filled and highlighted with teal border, but the user can still overwrite it | Apply `setStyleSheet()` in `autofill.py`, never call `setReadOnly()` |
| **B — Enforced read-only** | Field is pre-filled and the user cannot change it without going to the template editor | Call `widget.setReadOnly(True)` in `apply_autofill_to_form()` when `is_locked == True` |

The code examples in Feature 3 implement **Option A**. If you choose Option B, add `widget.setReadOnly(meta.get("is_locked", False))` in `apply_autofill_to_form()`.

### UI Changes — `pages/company_page.py`

Add a "Form Templates" button to each company row in the table. Clicking it opens a new `CompanyTemplateDialog`.

**New file: `pages/company_template_dialog.py`**

```python
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QFormLayout,
    QLineEdit, QCheckBox, QPushButton, QLabel, QHBoxLayout, QMessageBox
)
from Utility.local_db import local_db
import db, threading


class CompanyTemplateDialog(QDialog):
    def __init__(self, company_id: str, company_name: str, parent=None):
        super().__init__(parent)
        self.company_id = company_id
        self.setWindowTitle(f"Form Templates — {company_name}")
        self.setMinimumSize(700, 500)
        self._widgets = {}  # {form_type: {field_key: {"value_edit": QLineEdit, "lock_cb": QCheckBox}}}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()

        form_types = local_db.list_company_templates(self.company_id)
        if not form_types:
            layout.addWidget(QLabel("No templates saved for this company yet."))
            return

        for form_type in form_types:
            tab, tab_widgets = self._build_tab(form_type)
            self.tabs.addTab(tab, form_type.replace("_", " ").title())
            self._widgets[form_type] = tab_widgets

        layout.addWidget(self.tabs)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save All Changes")
        save_btn.clicked.connect(self._save_all)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _build_tab(self, form_type: str):
        """Returns (QWidget tab, dict of {field_key: {"value_edit", "lock_cb"}})."""
        template = local_db.get_company_template(self.company_id, form_type)
        tab = QWidget()
        form = QFormLayout(tab)
        tab_widgets = {}

        for field_key, meta in template.items():
            row = QHBoxLayout()
            value_edit = QLineEdit(str(meta["value"]))
            lock_cb = QCheckBox("Locked")
            lock_cb.setChecked(meta.get("is_locked", False))
            lock_cb.setToolTip("If checked, this field will be read-only when the form opens.")
            row.addWidget(value_edit)
            row.addWidget(lock_cb)
            form.addRow(meta.get("label", field_key), row)
            tab_widgets[field_key] = {"value_edit": value_edit, "lock_cb": lock_cb}

        return tab, tab_widgets

    def _save_all(self):
        for form_type, fields in self._widgets.items():
            updated = {
                field_key: {
                    "value": w["value_edit"].text(),
                    "label": field_key.replace("_", " ").title(),
                    "is_locked": w["lock_cb"].isChecked()
                }
                for field_key, w in fields.items()
            }
            local_db.save_company_template(self.company_id, form_type, updated)
            threading.Thread(
                target=db.sync_company_templates_to_cloud,
                args=(self.company_id,), daemon=True
            ).start()

        QMessageBox.information(self, "Saved", "All template changes saved.")
```

---

## Feature 3 — Cross-Form Autofill

### Overview

Currently `showEvent()` in each form only pre-fills employee personal data (as seen in `form_drug_testing.py`). This feature extends it to merge two layers of data in priority order:

```
Priority 1 (lowest)  — Company template defaults        (from company_templates table)
Priority 2 (highest) — Employee personal data           (from selected_employee in session)
```

> **Note:** A third priority layer (pre-filling from a previously saved submission for edit mode) is **out of scope for this implementation**. The current forms have no edit/re-open flow. This can be added later without breaking the autofill architecture.

Fields pre-filled from the company template are visually marked with a teal left border and a tooltip indicating they are company defaults. They remain editable (Option A from Feature 2).

### New Helper — `Utility/autofill.py`

Create this file. It is the single source of truth for all autofill logic.

```python
# Utility/autofill.py
from PyQt5.QtWidgets import QLineEdit, QComboBox, QCheckBox
from Utility.local_db import local_db


def build_autofill_context(company_id: str, employee: dict, form_type: str) -> dict:
    """
    Returns a merged dict of field_key -> {"value": ..., "source": ..., "is_locked": bool}
    for pre-filling a form. Employee data always overwrites company template data.

    Args:
        company_id: ID of the selected company
        employee:   Dict from local_db.get_employee() — keys include full_name, id_number, etc.
        form_type:  Must match a key in TEMPLATE_MAP in pages/template_generator.py
    """
    context = {}

    # Layer 1: company template defaults (lowest priority)
    if company_id:
        template = local_db.get_company_template(company_id, form_type)
        for key, meta in template.items():
            context[key] = {
                "value":     meta["value"],
                "source":    "company_template",
                "is_locked": meta.get("is_locked", False)
            }

    # Layer 2: employee personal data (always overwrites template on key collision)
    # Keys here must match self.fields keys registered in each form class
    employee_fields = {
        "employee_name":       employee.get("full_name", ""),
        "employee_id_no":      employee.get("id_number", ""),
        "employee_job_title":  employee.get("job_title", ""),
        "employee_department": employee.get("department", ""),
        # The drug testing form uses these field names — add form-specific mappings here
        "full_name":           employee.get("full_name", ""),
        "id_number":           employee.get("id_number", ""),
        "job_title":           employee.get("job_title", ""),
    }
    for key, value in employee_fields.items():
        if value:
            context[key] = {"value": value, "source": "employee", "is_locked": False}

    return context


def apply_autofill_to_form(form_widget, context: dict):
    """
    Populate a form's widgets using a context dict from build_autofill_context().

    Expects form_widget to have a `self.fields` dict mapping field_key -> QWidget.
    Fields sourced from "company_template" get a teal left border.
    """
    TEMPLATE_STYLE = "border-left: 3px solid #1D9E75; padding-left: 6px;"

    for key, meta in context.items():
        widget = form_widget.fields.get(key)
        if widget is None:
            continue

        value = meta["value"]
        source = meta["source"]

        if isinstance(widget, QLineEdit):
            widget.setText(str(value))
        elif isinstance(widget, QComboBox):
            idx = widget.findText(str(value))
            if idx >= 0:
                widget.setCurrentIndex(idx)
        elif isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))

        if source == "company_template":
            widget.setStyleSheet(TEMPLATE_STYLE)
            widget.setToolTip("Pre-filled from company template — you can still edit this")
```

### Changes to All 11 Form Files in `pages/forms/`

The existing forms (e.g. `form_drug_testing.py`) store widgets as direct `self.` attributes (`self.full_name`, `self.id_number`, etc.) rather than in a `self.fields` dict. The autofill system requires `self.fields`.

**In each form class, make these three changes:**

1. **Add `self.fields = {}` in `__init__()`**, before `self.init_ui()`:
   ```python
   def __init__(self, main_window):
       super().__init__()
       self.main_window = main_window
       self.fields = {}   # ← add this line
       self.init_ui()
   ```

2. **Register each widget in `self.fields` as it is created in `init_ui()`** (keep the `self.` attribute too — don't break existing references):
   ```python
   self.full_name = QLineEdit()
   self.fields["full_name"] = self.full_name  # ← add this after each widget creation
   ```

3. **Replace the manual pre-fill block in `showEvent()`** with the autofill call:
   ```python
   def showEvent(self, event):
       super().showEvent(event)
       employee = getattr(self.main_window, 'selected_employee', None) or {}
       company = getattr(self.main_window, 'selected_company', None) or {}
       company_id = company.get("id", "")
       from Utility.autofill import build_autofill_context, apply_autofill_to_form
       context = build_autofill_context(company_id, employee, self.FORM_TYPE)
       apply_autofill_to_form(self, context)
   ```

4. **Add a class-level constant** at the top of the class. Use the exact `TEMPLATE_MAP` key from `pages/template_generator.py`:
   ```python
   class FormDrugTesting(QWidget):
       FORM_TYPE = "workplace_drug_testing"  # must match TEMPLATE_MAP key
   ```

### `FORM_TYPE` Constant Map

| Class file | `FORM_TYPE` value |
|---|---|
| `form_drug_testing.py` | `"workplace_drug_testing"` |
| `form_vitamin_b.py` | `"vitamin_b_consent"` |
| `form_certificate_fitness.py` | `"certificate_of_fitness"` |
| `form_heights_questionnaire.py` | `"heights_questionnaire"` |
| `form_hot_cold_exposure.py` | `"hot_cold_exposure"` |
| `form_confined_spaces.py` | `"confined_spaces_questionnaire"` |
| `form_musculoskeletal.py` | `"musculoskeletal_questionnaire"` |
| `form_psychology.py` | `"psychology_questionnaire"` |
| `form_cwb_referral.py` | `"cwb_medical_referral"` |
| `form_complete_wellbeing.py` | `"complete_wellbeing"` |
| `form_annexure3.py` | `"annexure3_cwb"` |

### Shared Field Naming Convention

To make the autofill system work, all 11 forms must use consistent `field_key` names for shared fields in their `self.fields` dict. The `self.` widget attributes can keep their original names — only the `self.fields["key"]` registration key needs to be standardised.

| Standardised `self.fields` key | Notes |
|---|---|
| `full_name` | Already used by `form_drug_testing.py` |
| `id_number` | Already used by `form_drug_testing.py` |
| `job_title` | Already used by `form_drug_testing.py` |
| `practitioner_name` | Register the practitioner/doctor name field under this key |
| `practitioner_reg_no` | Register the HPCSA/registration number field under this key |
| `clinic_name` | Register the practice/clinic name field under this key |

### Visual Treatment — `themes/modern.qss`

> **Correction from original plan:** `QLineEdit[data-source="template"]` CSS attribute selectors do **not** work in PyQt5. The inline `setStyleSheet()` call in `apply_autofill_to_form()` is the correct approach.

Add only the tooltip style to `themes/modern.qss` (the teal border is applied inline):

```css
/* Tooltip style */
QToolTip {
    background-color: #1D9E75;
    color: #ffffff;
    border: none;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
}
```

---

## Feature 4 — Dynamic Stamp Positioning

### Overview

Currently stamps (doctor and clinic) are placed at hardcoded positions in `pages/template_generator.py` using the variable names `stamp1_data_uri` and `stamp2_data_uri`. This feature introduces a `stamp_config.json` file that defines position, scale, and opacity per form type. The values are passed into `generate_pdf_for_form()` as part of the Jinja2 context, so each form's PDF can have the stamp in the right place.

A simple editor UI lets the practitioner preview and adjust stamp position per form without touching code.

> **⚠️ WeasyPrint CSS Transform Support**
>
> WeasyPrint supports a limited subset of CSS. `transform: scale() rotate()` may be silently ignored. Use percentage `left`/`top` positioning (which works reliably) for placement, and test rotation support with an actual PDF render before relying on it. If rotation is ignored, consider pre-rotating stamp images at source instead.

> **Existing stamp variable names:** The current templates use `stamp1_data_uri` (doctor stamp) and `stamp2_data_uri` (clinic stamp). The new Jinja2 variables introduced here (`doctor_stamp`, `clinic_stamp`) are **additive** — `stamp1_data_uri` and `stamp2_data_uri` remain in the render context so existing templates are not broken.

### New File — `themes/stamp_config.json`

```json
{
  "_comment": "Position values are percentages of the page width/height. Rotation in degrees.",
  "default": {
    "doctor_stamp": { "x": 70, "y": 88, "scale": 1.0, "rotation": 0, "opacity": 0.85 },
    "clinic_stamp":  { "x": 15, "y": 88, "scale": 1.0, "rotation": 0, "opacity": 0.85 }
  },
  "workplace_drug_testing": {
    "doctor_stamp": { "x": 72, "y": 90, "scale": 0.9, "rotation": 0, "opacity": 0.8 },
    "clinic_stamp":  { "x": 12, "y": 90, "scale": 0.9, "rotation": 0, "opacity": 0.8 }
  },
  "certificate_of_fitness": {
    "doctor_stamp": { "x": 68, "y": 85, "scale": 1.1, "rotation": 0, "opacity": 0.9 },
    "clinic_stamp":  { "x": 10, "y": 85, "scale": 1.0, "rotation": 0, "opacity": 0.85 }
  },
  "heights_questionnaire": {
    "doctor_stamp": { "x": 70, "y": 88, "scale": 1.0, "rotation": 0, "opacity": 0.85 },
    "clinic_stamp":  { "x": 15, "y": 88, "scale": 1.0, "rotation": 0, "opacity": 0.85 }
  },
  "hot_cold_exposure": {
    "doctor_stamp": { "x": 70, "y": 88, "scale": 1.0, "rotation": 0, "opacity": 0.85 },
    "clinic_stamp":  { "x": 15, "y": 88, "scale": 1.0, "rotation": 0, "opacity": 0.85 }
  },
  "confined_spaces_questionnaire": {
    "doctor_stamp": { "x": 70, "y": 88, "scale": 1.0, "rotation": 0, "opacity": 0.85 },
    "clinic_stamp":  { "x": 15, "y": 88, "scale": 1.0, "rotation": 0, "opacity": 0.85 }
  },
  "musculoskeletal_questionnaire": {
    "doctor_stamp": { "x": 70, "y": 88, "scale": 1.0, "rotation": 0, "opacity": 0.85 },
    "clinic_stamp":  { "x": 15, "y": 88, "scale": 1.0, "rotation": 0, "opacity": 0.85 }
  },
  "psychology_questionnaire": {
    "doctor_stamp": { "x": 70, "y": 88, "scale": 1.0, "rotation": 0, "opacity": 0.85 },
    "clinic_stamp":  { "x": 15, "y": 88, "scale": 1.0, "rotation": 0, "opacity": 0.85 }
  },
  "cwb_medical_referral": {
    "doctor_stamp": { "x": 70, "y": 92, "scale": 0.85, "rotation": 0, "opacity": 0.8 },
    "clinic_stamp":  { "x": 15, "y": 92, "scale": 0.85, "rotation": 0, "opacity": 0.8 }
  },
  "complete_wellbeing": {
    "doctor_stamp": { "x": 70, "y": 88, "scale": 1.0, "rotation": 0, "opacity": 0.85 },
    "clinic_stamp":  { "x": 15, "y": 88, "scale": 1.0, "rotation": 0, "opacity": 0.85 }
  },
  "annexure3_cwb": {
    "doctor_stamp": { "x": 70, "y": 88, "scale": 1.0, "rotation": 0, "opacity": 0.85 },
    "clinic_stamp":  { "x": 15, "y": 88, "scale": 1.0, "rotation": 0, "opacity": 0.85 }
  },
  "vitamin_b_consent": {
    "doctor_stamp": { "x": 70, "y": 88, "scale": 1.0, "rotation": 0, "opacity": 0.85 },
    "clinic_stamp":  { "x": 15, "y": 88, "scale": 1.0, "rotation": 0, "opacity": 0.85 }
  }
}
```

### Changes to `pages/template_generator.py`

**Add a stamp config loader near the top of the file, after the existing imports:**

```python
import json
# (get_resource_path is already imported in this file)

def _load_stamp_config() -> dict:
    config_path = get_resource_path("themes/stamp_config.json")
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

_STAMP_CONFIG = _load_stamp_config()

def get_stamp_config(form_type: str) -> dict:
    """Returns stamp config for a form type, falling back to 'default'."""
    return _STAMP_CONFIG.get(form_type, _STAMP_CONFIG.get("default", {
        "doctor_stamp": {"x": 70, "y": 88, "scale": 1.0, "rotation": 0, "opacity": 0.85},
        "clinic_stamp":  {"x": 15, "y": 88, "scale": 1.0, "rotation": 0, "opacity": 0.85}
    }))

def reload_stamp_config():
    """Hot-reload stamp config after the editor saves changes. No restart required."""
    global _STAMP_CONFIG
    _STAMP_CONFIG = _load_stamp_config()
```

**In `generate_pdf_for_form()`, inject stamp config into `render_data`** — find the block that builds `render_data` (around line 161) and add to it:

```python
stamp_config = get_stamp_config(form_type)
render_data["doctor_stamp"] = stamp_config.get("doctor_stamp", {})
render_data["clinic_stamp"]  = stamp_config.get("clinic_stamp", {})
# stamp1_data_uri / stamp2_data_uri remain in render_data unchanged
```

### Changes to All 11 Jinja2 Templates (`templates/jinja2/*.html`)

Replace every hardcoded stamp `<img>` tag with the dynamic version below.

**Before (hardcoded — using existing variable names):**
```html
<img src="{{ stamp1_data_uri }}" style="position:absolute; bottom:40px; right:60px; width:120px;">
```

**After (dynamic):**
```html
<img src="{{ stamp1_data_uri }}"
     style="
       position: absolute;
       left: {{ doctor_stamp.x }}%;
       top:  {{ doctor_stamp.y }}%;
       transform: scale({{ doctor_stamp.scale }});
       transform-origin: top left;
       opacity: {{ doctor_stamp.opacity }};
       width: 120px;
     ">

<img src="{{ stamp2_data_uri }}"
     style="
       position: absolute;
       left: {{ clinic_stamp.x }}%;
       top:  {{ clinic_stamp.y }}%;
       transform: scale({{ clinic_stamp.scale }});
       transform-origin: top left;
       opacity: {{ clinic_stamp.opacity }};
       width: 120px;
     ">
```

> **Note:** Rotation is omitted from the template above due to uncertain WeasyPrint support. Add `rotate({{ doctor_stamp.rotation }}deg)` to `transform` only after confirming it renders correctly in a test PDF.

> **Note:** Ensure the parent container in each template has `position: relative` and a defined height so percentage positioning works correctly in WeasyPrint.

### New UI — Stamp Position Editor

Add a "Stamp Settings" button to `pages/home_page.py`. This opens `StampEditorDialog`.

**New file: `pages/stamp_editor_dialog.py`**

```python
import json
from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QLabel, QComboBox,
    QSlider, QPushButton, QWidget, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import QRect, QPoint
from Utility.app_context import get_resource_path
from pages.template_generator import reload_stamp_config


class StampEditorDialog(QDialog):
    """
    Visual editor for stamp_config.json.
    Shows a preview area representing an A4 page with stamp position indicators.
    Sliders control x, y, scale, and opacity.
    Saves directly to themes/stamp_config.json and hot-reloads template_generator.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stamp Position Editor")
        self.setMinimumSize(800, 600)
        self.config = self._load_config()
        self.current_form_type = "default"
        self._build_ui()
        self._load_sliders_for(self.current_form_type)

    def _load_config(self) -> dict:
        path = get_resource_path("themes/stamp_config.json")
        with open(path) as f:
            return json.load(f)

    def _build_ui(self):
        layout = QHBoxLayout(self)

        # Left panel: form type selector + sliders
        left = QVBoxLayout()
        self.form_selector = QComboBox()
        # Exclude the _comment key
        self.form_selector.addItems([k for k in self.config.keys() if not k.startswith("_")])
        self.form_selector.currentTextChanged.connect(self._on_form_changed)
        left.addWidget(QLabel("Form type:"))
        left.addWidget(self.form_selector)

        self._sliders = {}  # { "doctor_stamp_x": QSlider, ... }
        for stamp_key in ["doctor_stamp", "clinic_stamp"]:
            left.addWidget(QLabel(f"\n{stamp_key.replace('_', ' ').title()}"))
            # (prop, min, max, scale_factor)  — stored value = slider_value / scale_factor
            for prop, min_val, max_val, factor in [
                ("x",       0,   100, 1),
                ("y",       0,   100, 1),
                ("scale",  50,   200, 100),
                ("opacity", 10,  100, 100),
            ]:
                slider = QSlider(Qt.Horizontal)
                slider.setRange(min_val, max_val)
                slider.valueChanged.connect(
                    lambda v, sk=stamp_key, p=prop, f=factor: self._on_slider(sk, p, v, f)
                )
                self._sliders[f"{stamp_key}_{prop}"] = (slider, factor)
                row = QHBoxLayout()
                row.addWidget(QLabel(f"  {prop}:"))
                row.addWidget(slider)
                left.addLayout(row)

        save_btn = QPushButton("Save to stamp_config.json")
        save_btn.clicked.connect(self._save_config)
        left.addWidget(save_btn)
        left.addStretch()

        self.preview = StampPreviewWidget()
        layout.addLayout(left, 1)
        layout.addWidget(self.preview, 2)

    def _load_sliders_for(self, form_type: str):
        """Update all sliders to reflect the loaded config for the given form type."""
        cfg = self.config.get(form_type, self.config.get("default", {}))
        for stamp_key in ["doctor_stamp", "clinic_stamp"]:
            stamp_cfg = cfg.get(stamp_key, {})
            for prop, factor in [("x", 1), ("y", 1), ("scale", 100), ("opacity", 100)]:
                slider, _ = self._sliders[f"{stamp_key}_{prop}"]
                slider.blockSignals(True)
                slider.setValue(int(stamp_cfg.get(prop, 0) * factor))
                slider.blockSignals(False)
        self._refresh_preview()

    def _on_form_changed(self, form_type: str):
        self.current_form_type = form_type
        if form_type not in self.config:
            # Copy default config if this form type doesn't have its own entry yet
            import copy
            self.config[form_type] = copy.deepcopy(self.config.get("default", {}))
        self._load_sliders_for(form_type)

    def _on_slider(self, stamp_key: str, prop: str, value: int, factor: int):
        adjusted = value / factor
        if self.current_form_type not in self.config:
            self.config[self.current_form_type] = {}
        if stamp_key not in self.config[self.current_form_type]:
            self.config[self.current_form_type][stamp_key] = {}
        self.config[self.current_form_type][stamp_key][prop] = adjusted
        self._refresh_preview()

    def _refresh_preview(self):
        self.preview.update_stamps(self.config.get(self.current_form_type, {}))

    def _save_config(self):
        path = get_resource_path("themes/stamp_config.json")
        with open(path, "w") as f:
            json.dump(self.config, f, indent=2)
        reload_stamp_config()  # Hot-reload — no restart needed
        QMessageBox.information(self, "Saved", "Stamp configuration saved and reloaded.")


class StampPreviewWidget(QWidget):
    """Draws an A4 rectangle and two coloured circles representing stamp positions."""

    def __init__(self):
        super().__init__()
        self.stamp_config = {}
        self.setMinimumSize(300, 420)

    def update_stamps(self, config: dict):
        self.stamp_config = config
        self.update()  # triggers paintEvent

    def paintEvent(self, event):
        painter = QPainter(self)
        page_rect = QRect(20, 20, self.width() - 40, self.height() - 40)
        painter.setPen(QPen(Qt.gray, 1))
        painter.setBrush(Qt.white)
        painter.drawRect(page_rect)

        for stamp_key, color in [("doctor_stamp", QColor("#1D9E75")), ("clinic_stamp", QColor("#534AB7"))]:
            cfg = self.stamp_config.get(stamp_key, {})
            x_pct = cfg.get("x", 70) / 100
            y_pct = cfg.get("y", 88) / 100
            cx = int(page_rect.left() + x_pct * page_rect.width())
            cy = int(page_rect.top()  + y_pct * page_rect.height())
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.setOpacity(cfg.get("opacity", 0.85))
            painter.drawEllipse(QPoint(cx, cy), 18, 18)
            painter.setOpacity(1.0)
            painter.setPen(Qt.white)
            painter.drawText(
                QRect(cx - 18, cy - 10, 36, 20), Qt.AlignCenter,
                "D" if stamp_key == "doctor_stamp" else "C"
            )
```

---

## Implementation Order

Work through features in this order to respect dependencies:

```
Feature 2 (DB schema + template capture)
    ↓
Feature 3 (Autofill — depends on Feature 2's company_templates table)
    ↓
Feature 4 (Stamp config — independent, but benefits from form refactor done in F3)
    ↓
Feature 1 (Android port — do last; depends on form logic being cleanly separated from PyQt5)
```

> ⚠️ Do **not** start Feature 1 before Features 2–4 are complete and tested on desktop. The PyQt5 form refactor in F1 touches every form file — doing this after F2/F3 changes are applied prevents double-touching those files.

## Files Changed Summary

| File | Feature(s) | Status |
|------|-----------|--------|
| `Utility/local_db.py` | 2, 3 | Modify |
| `db.py` | 2 | Modify |
| `Utility/template_fields.py` | 2, 3 | **New file** |
| `Utility/autofill.py` | 3 | **New file** |
| `pages/forms/*.py` (all 11) | 2, 3 | Modify |
| `pages/company_page.py` | 2 | Modify |
| `pages/company_template_dialog.py` | 2 | **New file** |
| `pages/stamp_editor_dialog.py` | 4 | **New file** |
| `pages/template_generator.py` | 4 | Modify |
| `templates/jinja2/*.html` (all 11) | 4 | Modify |
| `themes/stamp_config.json` | 4 | **New file** |
| `themes/modern.qss` | 3 | Modify (tooltip only) |
| `main_server.py` | 1 | **New file** |
| `set_db_path.py` | 1 | **New file** |
| `routers/*.py` | 1 | **New directory** |
| `web_ui/` | 1 | **New directory** |
| `requirements.txt` | 1 | Modify (add FastAPI/uvicorn) |
