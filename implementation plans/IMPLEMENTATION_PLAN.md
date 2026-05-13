HealthCorp360
Unified Web UI — Implementation Plan
One codebase. Runs in a browser on desktop, in an Android WebView on tablet, and on any future surface without modification.
Replaces PyQt5 entirely. All Python business logic unchanged.
Guiding Principle
PyQt5 is replaced once, completely. After the cutover there is no dual-UI maintenance burden — the same HTML forms serve every platform. All Python business logic (db.py, local_db.py, form processing, PDF generation, Supabase sync) remains untouched throughout. The migration is additive until Phase 9, when PyQt5 is retired in a single controlled step.





Architecture Overview
The final architecture is identical on every platform. The only difference is how the browser window is launched.





Master Execution Order
Follow phases strictly in sequence. Each phase is safe to hand to Claude Code as a discrete unit of work.






The Spike
Create a throwaway Android Studio project with Chaquopy. In build.gradle add:

Run on a physical ARM tablet and execute:


Path A — WeasyPrint Works
Continue using the existing WeasyPrint + Jinja2 pipeline everywhere. No changes to template_generator.py. Document the exact Chaquopy and WeasyPrint version combination that worked.

Path B — WeasyPrint Fails (Most Likely)

Validation Gate — Phase 1





New SQLite table — add to Utility/local_db.py in _create_tables()

New Supabase table — run in Supabase SQL editor

New methods — Utility/local_db.py

New method — db.py

Validation Gate — Phase 2




Priority order for pre-fill

New file — Utility/autofill.py
UI-agnostic. The same functions are called from a PyQt5 showEvent() now and from a FastAPI router in Phase 6.

Standardised field key names — apply to all 11 forms

Changes to each of the 11 form files in pages/forms/
Add self.fields: dict = {} in __init__(). Populate as each widget is created:  self.fields['practitioner_name'] = QLineEdit()
Add class-level constant:  FORM_TYPE = 'drug_testing'  (use the matching key from COMPANY_TEMPLATE_FIELDS)
Replace manual pre-fill in showEvent() with:

Validation Gate — Phase 3





New file — themes/stamp_config.json
Defines x and y position (as percentage of page), scale, rotation, and opacity per form type. Falls back to the 'default' block if a form type is not listed. See original plan appendix for full JSON contents.

Changes to pages/template_generator.py

Changes to all 11 Jinja2 templates
Replace every hardcoded stamp img tag with dynamic left, top, transform, and opacity values from template variables. Ensure each parent container has position: relative and a defined height so percentage positioning works correctly in WeasyPrint.

Validation Gate — Phase 4





What to do in each of the 11 form files
Find the submit_form() method.
Extract the data-dict construction plus the calls to local_db.save_submission() and generate_pdf_for_form() into a new standalone function at module level with this exact signature:
Rewrite submit_form() to read values from PyQt5 widgets into a data dict, call process_submission(), then handle the result in the UI (show success message or error dialog).
Verify importability from a Python REPL:  from pages.forms.drug_testing import process_submission

Validation Gate — Phase 5




File structure

main_server.py


Shared-secret authentication — routers/_deps.py


Android-aware file paths — Utility/file_manager.py



Validation Gate — Phase 6





web_ui/static/app.js — shared across all pages

web_ui/static/signature.js — DPI-aware canvas


web_ui/static/styles.css

Validation Gate — Phase 7





Pattern for each form
Create web_ui/forms/{form_type}.html. Use the standardised field keys from Phase 3 as HTML input name attributes.
On page load, call GET /forms/{form_type}/autofill?company_id=...&employee_id=... and populate fields. Apply the .template-field CSS class to company-default fields.
For forms requiring a signature, include signature.js and call initSignaturePad('sig-canvas') on DOMContentLoaded.
On submit, build a JSON dict from all field values and POST to /forms/{form_type}/submit with employee_id, company_id, and data payload.
On success, show the pdf_path and a Download / View button. On error, show the error message inline — never alert().
Test in the desktop browser before moving to the next form.

Form completion tracker

Validation Gate — Phase 8





main_server.py already handles desktop launch
The auto-open browser logic added in Phase 6 means python main_server.py is the new entry point. Add a thin double-click launcher for non-technical users:
On Windows, pair with a run.bat file. On Mac, use a .command file or a simple Automator app.

Update requirements.txt

Archive PyQt5 files — do not delete yet
Move pages/, main.py, and themes/modern.qss to archive/pyqt5/ in the repository. Keep in version control history. Delete the archive folder only after one full week of the web UI running in production without issues.

Validation Gate — Phase 9





build.gradle — Chaquopy setup



MainActivity.kt



AndroidManifest.xml — lock orientation

Final Acceptance Checklist — run on a physical ARM tablet



Files Changed — Complete Summary