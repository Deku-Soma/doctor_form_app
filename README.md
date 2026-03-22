# HealthCorp360 — Doctor Form App

> A **PyQt5 desktop application** for occupational health practitioners to manage companies, employees, and generate standardized medical assessment PDFs — with full **offline-first** data persistence and cloud sync.

---

## Quick Start

### Prerequisites
- **Python 3.9+**
- **Windows OS** (built and tested on Windows; uses `ctypes` for file hiding)

### Setup

```bash
# 1. Clone and enter
cd doctor_form_app

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
#    Create .env with your Supabase credentials:
#    SUPERBASE_URL=https://your-project.supabase.co
#    SUPERBASE_API_KEY=your-anon-key

# 5. Run the app
python main.py
```

### First-Time Admin Setup

```bash
# Create the first user (requires internet for Supabase)
python add_user.py --username "Admin" --email admin@example.com
```

> [!IMPORTANT]
> The **first login on any device requires an internet connection** to download and cache credentials from Supabase. Subsequent logins work offline.

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    main.py                          │
│              MainApp (QStackedWidget)               │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐    │
│  │LoginPage │→│ HomePage │→│ Form Pages (x13) │    │
│  └──────────┘ └──────────┘ └──────────────────┘    │
│                    │                │               │
│             ┌──────┴──────┐   ┌────┴─────┐         │
│             │CompanyPage  │   │ Employee │         │
│             │EmployeePage │   │ Selector │         │
│             └─────────────┘   └──────────┘         │
├─────────────────────────────────────────────────────┤
│                  Data Layer                         │
│  ┌────────────┐  ┌───────────┐  ┌───────────────┐  │
│  │  db.py     │  │ local_db  │  │ file_manager  │  │
│  │ (Supabase) │  │ (SQLite)  │  │ (PDF output)  │  │
│  └────────────┘  └───────────┘  └───────────────┘  │
├─────────────────────────────────────────────────────┤
│                 PDF Pipeline                        │
│  Form Data → Jinja2 Templates → WeasyPrint → PDF   │
│         (templates/jinja2/*.html)                   │
└─────────────────────────────────────────────────────┘
```

### Core Tech Stack

| Layer        | Technology                     |
|-------------|-------------------------------|
| UI          | PyQt5 (QStackedWidget router) |
| Styling     | QSS (Qt Stylesheet)          |
| Local DB    | SQLite3 via `local_db.py`     |
| Cloud DB    | Supabase (PostgreSQL)         |
| PDF Engine  | Jinja2 + WeasyPrint           |
| Auth        | bcrypt password hashing       |
| IDs         | ULID (sortable unique IDs)    |
| Packaging   | PyInstaller (`.spec` files)   |

---

## Dependency & Data Flow

### Entry Point

**`main.py`** → `MainApp.__init__()` → Instantiates all pages → Sets `LoginPage` as initial view.

### Data Flow: Form Submission

```
User fills form → submit_form()
  │
  ├─ 1. Save signature → temp PNG → base64 encode → cleanup temp
  │
  ├─ 2. local_db.save_submission()
  │     → SQLite INSERT with ULID primary key
  │     → last_synced_at = NULL (marks as unsynced)
  │
  ├─ 3. threading.Thread(target=db.sync_to_cloud)
  │     → Reads unsynced rows → Upserts to Supabase
  │     → Marks rows synced on success
  │
  └─ 4. generate_pdf_for_form()
        → Jinja2 renders HTML template with form data
        → Embeds signatures, logo, stamps as data URIs
        → WeasyPrint converts HTML → PDF
        → FileManager saves to: outputs/{company}/{employee}/{form}_{date}.pdf
        → local_db.record_document() logs the PDF metadata
```

### Data Flow: Login

```
User enters credentials
  │
  ├─ Online? → Supabase query → bcrypt verify
  │     → Success: Cache user to SQLite → Create session.json
  │
  └─ Offline? → SQLite lookup → bcrypt verify against cached hash
        → Success: Create session.json
```

---

## Module Breakdown

### Root Files

| File | Purpose |
|------|---------|
| `main.py` | Application entry point. Defines `MainApp` (`QStackedWidget`) — the page router. Instantiates all 17 pages and manages navigation. |
| `db.py` | Cloud data layer. Initializes Supabase client, handles `validate_login()` (online/offline), `create_user()`, `sync_to_cloud()`, and `encode_signature_to_base64()`. |
| `add_user.py` | CLI admin tool to provision new users into Supabase. Standalone script. |
| `requirements.txt` | Frozen pip dependencies (52 packages). |
| `.env` | Supabase credentials (`SUPERBASE_URL`, `SUPERBASE_API_KEY`). |
| `installer_script.iss` | Inno Setup installer script for Windows distribution. |
| `DoctorFormApp.spec` / `AddUserTool.spec` | PyInstaller build specs. |

### `pages/` — UI Layer

See [pages/README.md](pages/README.md) for details.

| File | Purpose |
|------|---------|
| `login_page.py` | Email/password login form. Calls `db.validate_login()`, writes `session.json`. |
| `home_page.py` | Dashboard with categorized form cards (Consent, Questionnaires, Certificates). Search bar filters cards. |
| `company_page.py` | CRUD table for companies. Add/Edit via `AddCompanyDialog`. |
| `employee_page.py` | CRUD table for employees with company filter dropdown. |
| `employee_selector.py` | Modal dialog — select company then employee before opening any form. |
| `form_card.py` | Reusable clickable card widget with hover effects (teal→purple). |
| `template_generator.py` | **The PDF engine.** Maps form types → Jinja2 templates, handles signature data URIs, logo/stamp embedding, and WeasyPrint rendering. |
| `signiture.py` | Custom `SignaturePad` widget — captures mouse-drawn signatures on a `QPixmap`. |
| `formA.py` / `formB.py` | Legacy form implementations (pre-factory pattern). |
| `pdf_generator.py` | Stub/minimal PDF generation wrapper. |

### `pages/forms/` — Medical Form Classes

See [pages/forms/README.md](pages/forms/README.md) for details.

11 form classes, each following the same pattern:
1. Build a scrollable `QFormLayout` with specific medical fields
2. Pre-fill employee data from `main_window.selected_employee` via `showEvent()`
3. Capture signatures → base64 encode → build data dict
4. Save to SQLite → trigger background cloud sync → generate PDF

### `Utility/` — Support Modules

See [Utility/README.md](Utility/README.md) for details.

| File | Purpose |
|------|---------|
| `local_db.py` | **The data backbone.** `LocalDB` class managing SQLite with tables: `submissions`, `users`, `companies`, `employees`, `documents`. Singleton instance `local_db`. |
| `form_factory.py` | Schema-driven form builder. `FormFactory.build()` takes a JSON schema → returns a `FormWidget` with auto-generated fields, validation, and PDF generation. |
| `file_manager.py` | Manages the `outputs/` folder hierarchy: `outputs/{company}/{employee}/{form}_{date}.pdf`. Handles deduplication. Singleton `file_manager`. |
| `app_context.py` | `get_resource_path()` — resolves file paths for both development and PyInstaller-bundled environments. |

### `templates/` — HTML Templates

See [templates/README.md](templates/README.md) for details.

- **`templates/`** — 12 legacy raw HTML form templates (not actively used for PDF generation)
- **`templates/jinja2/`** — 11 Jinja2 HTML templates used by `template_generator.py` to render PDFs via WeasyPrint

### `themes/` — Visual Assets

See [themes/README.md](themes/README.md) for details.

- `modern.qss` — Dark theme QSS stylesheet (teal accent, dark grey backgrounds)
- `Logo.png` — HealthCorp360 logo (embedded in PDF headers)
- `Dr.R.Malebye stamp.png` / `helthcorp stamp.png` — Doctor/clinic stamps for PDF footers

### `Sessions/` — Runtime State

See [Sessions/README.md](Sessions/README.md) for details.

- `session.json` — Stores the currently logged-in user's data (written on login, read on page navigation).

---

## Logic Deep-Dives

### 1. Offline-First Authentication (`db.py` → `validate_login()`)

The most architecturally significant piece. The system tries Supabase first, then falls back to locally cached credentials:

```python
def validate_login(email, password):
    if supabase:                         # Online path
        result = supabase.table("users").select("*").eq("user_email", email).execute()
        if bcrypt.checkpw(password, stored_hash):
            local_db.upsert_user(...)    # Cache for offline use
            return {"success": True, "mode": "online"}
    # Offline fallback
    local_user = local_db.get_user_by_email(email)
    if bcrypt.checkpw(password, local_user["password_hash"]):
        return {"success": True, "mode": "offline"}
```

**Design intent:** Clinical environments (mines, remote sites) may lack internet. The app must work regardless, syncing when connectivity returns.

### 2. ULID-Based Submission IDs (`local_db.py` → `save_submission()`)

Uses [ULID](https://github.com/ulid/spec) instead of UUID4 for primary keys. ULIDs are:
- **Chronologically sortable** (timestamp-prefixed)
- **Collision-free** across devices (random suffix)
- Ideal for offline-first multi-device sync where auto-increment IDs would collide.

### 3. PDF Generation Pipeline (`template_generator.py` → `generate_pdf_for_form()`)

The most complex function (~100 lines). Key decisions:
- **Data URIs for images:** Signatures, logos, and stamps are embedded as `data:image/png;base64,...` directly in HTML to avoid WeasyPrint file-path issues.
- **Employee-based file organization:** PDFs are saved to `outputs/{company_folder}/{employee_folder}/{form_type}_{date}.pdf`.
- **Debug HTML output:** Every PDF also saves a `_debug.html` file for troubleshooting template rendering issues.

---

## The "Gotchas" List

### ⚠️ Critical

1. **Session file stores password hash in plaintext JSON** — `Sessions/session.json` contains the bcrypt hash. While bcrypt is one-way, exposing the hash on disk is a security surface. The file is not encrypted or access-controlled.

2. **Supabase env var is misspelled** — The env vars are named `SUPERBASE_URL` and `SUPERBASE_API_KEY` (should be `SUPABASE_*`). This is a naming-only issue but could confuse new developers.

3. **`os.getcwd()` everywhere** — Many path resolutions use `os.getcwd()` instead of `__file__`-relative paths. If the app is launched from a different working directory, paths will break. The `get_resource_path()` utility exists but isn't consistently used.

4. **Temp signature files not always cleaned up** — Some forms (e.g., `formA.py`) save to hardcoded paths like `temp_signature.png` without guaranteed cleanup. Leftover temp files exist in the repo root.

### ⚡ Non-Obvious Behavior

5. **`go_to_page()` uses a long if/elif chain** — Navigation in `main.py` maps string page names to widget instances via 13 conditionals instead of a dictionary lookup. Adding a new form requires editing this chain.

6. **`FormFactory` exists but isn't used by actual forms** — `form_factory.py` provides a schema-driven `FormWidget` builder, but all 11 production forms in `pages/forms/` are hand-coded. The factory is only used by the legacy `formA.py`/`formB.py` through the `generate_html_pdf()` legacy path.

7. **`generate_pdf_form()` in `formA.py` just calls `submit_form()`** — The "Generate PDF Only" button actually saves to the database AND generates a PDF. There's no PDF-only path.

8. **Singleton `local_db` is imported at module level** — This means the SQLite connection is opened immediately when any module that imports `local_db` is loaded, even during testing or CLI usage.

9. **`sync_to_cloud()` returns `False` on first failure** — If any single record fails to sync, the entire sync operation stops and returns `False`. Previously-successful records in the same batch are already synced, but remaining ones are left unsynced. There's no retry mechanism.

10. **`SignaturePad` doesn't have an `isEmpty()` method** — The `FormFactory.validate()` checks for `hasattr(w, "isEmpty")`, but `SignaturePad` doesn't implement it. Signature fields are never validated as required.

11. **Hidden database file** — On Windows, `local_data.db` is set as a hidden file via `ctypes.windll.kernel32.SetFileAttributesW`. This could confuse developers looking for the database.

12. **No database migrations** — The SQL files (`migrate_users_table.sql`, `supabase_setup.sql`, `supabase_fix_fk.sql`) exist as standalone scripts but aren't integrated into any migration framework.

---

## Directory Structure

```
doctor_form_app/
├── main.py                         # App entry point
├── db.py                           # Supabase client + auth + sync
├── add_user.py                     # CLI user provisioning tool
├── requirements.txt                # Python dependencies
├── .env                            # Supabase credentials
├── DoctorFormApp.spec              # PyInstaller build config
├── installer_script.iss            # Inno Setup Windows installer
│
├── pages/                          # All UI screens
│   ├── login_page.py               # Authentication UI
│   ├── home_page.py                # Dashboard with form cards
│   ├── company_page.py             # Company CRUD
│   ├── employee_page.py            # Employee CRUD
│   ├── employee_selector.py        # Pre-form employee picker dialog
│   ├── form_card.py                # Clickable card widget
│   ├── template_generator.py       # PDF generation engine
│   ├── signiture.py                # Signature capture widget
│   ├── formA.py / formB.py         # Legacy forms
│   ├── pdf_generator.py            # Minimal PDF wrapper
│   └── forms/                      # 11 medical form classes
│       ├── form_drug_testing.py
│       ├── form_vitamin_b.py
│       ├── form_certificate_fitness.py
│       ├── form_heights_questionnaire.py
│       ├── form_hot_cold_exposure.py
│       ├── form_confined_spaces.py
│       ├── form_musculoskeletal.py
│       ├── form_psychology.py
│       ├── form_cwb_referral.py
│       ├── form_complete_wellbeing.py
│       └── form_annexure3.py
│
├── Utility/                        # Support modules
│   ├── local_db.py                 # SQLite data layer (5 tables)
│   ├── form_factory.py             # Schema-driven form builder
│   ├── file_manager.py             # PDF output folder manager
│   └── app_context.py              # PyInstaller path resolver
│
├── templates/                      # HTML templates
│   ├── *.html                      # 12 legacy raw templates
│   └── jinja2/                     # 11 Jinja2 templates for PDF
│
├── themes/                         # Visual assets + QSS
│   ├── modern.qss                  # Dark theme stylesheet
│   ├── Logo.png                    # Company logo
│   └── *.png                       # Doctor/clinic stamps
│
├── Sessions/                       # Runtime session state
│   └── session.json
│
├── outputs/                        # Generated PDFs
│   └── {company}/{employee}/*.pdf
│
└── Doc details/                    # Reference documents & stamps
```
