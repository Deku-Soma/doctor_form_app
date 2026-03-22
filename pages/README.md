# `pages/` — UI Layer

This directory contains all PyQt5 screen/page widgets and UI support modules.

## Navigation Model

The app uses a `QStackedWidget` in `main.py` as a simple page router. Pages are switched via `setCurrentWidget()`.

```
LoginPage → HomePage ↔ CompanyPage
                     ↔ EmployeePage
                     → [Any Form Page] (via EmployeeSelectorDialog)
```

## Files

### Core Pages

| File | Class | Purpose |
|------|-------|---------|
| `login_page.py` | `LoginPage` | Email + password auth. Calls `db.validate_login()`, writes `Sessions/session.json` on success. |
| `home_page.py` | `HomePage` | Dashboard showing categorized form cards in a grid. Contains a search bar and management buttons. Sections: Consent Forms, Health Questionnaires, Certificates & Referrals. |
| `company_page.py` | `CompanyPage`, `AddCompanyDialog` | Table-based CRUD for companies. Uses `local_db` directly. Refreshes on `showEvent()`. |
| `employee_page.py` | `EmployeePage`, `AddEmployeeDialog` | Table-based CRUD for employees with company filter dropdown. Supports pre-filtering when navigated from `CompanyPage`. |

### UI Components

| File | Class | Purpose |
|------|-------|---------|
| `form_card.py` | `FormCard(QFrame)` | Clickable card with emoji icon, title, description. Emits `clicked` signal. Hover: teal (#163b4d) → purple (#685070). |
| `employee_selector.py` | `EmployeeSelectorDialog` | Modal dialog shown before opening any form. Two cascading dropdowns: Company → Employee. Includes inline "Add New" buttons. |
| `signiture.py` | `SignaturePad(QWidget)` | Freehand drawing widget on a `QPixmap`. Captures mouse input, exposes `get_signature_image()` → `QPixmap`, and `clear()`. |

### PDF Generation

| File | Key Functions | Purpose |
|------|---------------|---------|
| `template_generator.py` | `generate_pdf_for_form()`, `generate_html_pdf()` | **The PDF engine.** Maps form types to Jinja2 templates, handles signature/logo/stamp embedding as data URIs, renders via WeasyPrint, saves PDFs to the employee's folder. Also saves `_debug.html` alongside each PDF. |
| `pdf_generator.py` | — | Minimal/stub wrapper. Not actively used by production forms. |

### Legacy Forms

| File | Class | Notes |
|------|-------|-------|
| `formA.py` | `FormA` | Early-stage medical assessment form. Hand-built UI, uses legacy `generate_html_pdf()` path. |
| `formB.py` | `FormB` | Empty/stub form. |

## Interdependencies

- **All pages** depend on `main_window` (the `MainApp` instance) for navigation.
- **Company/Employee pages** depend directly on `Utility.local_db`.
- **Form pages** depend on `Utility.local_db`, `db`, `pages.signiture`, and `pages.template_generator`.
- **`employee_selector.py`** lazy-imports `AddCompanyDialog` and `AddEmployeeDialog` to avoid circular imports.
