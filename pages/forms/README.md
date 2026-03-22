# `pages/forms/` — Medical Form Classes

This directory contains 11 specialized medical/occupational health form widgets. Each is a standalone `QWidget` page.

## Pattern

Every form class follows **the same pattern**:

```python
class FormXxx(QWidget):
    def __init__(self, main_window):
        # Store reference, build UI

    def showEvent(self, event):
        # Pre-fill fields from main_window.selected_employee

    def init_ui(self):
        # QScrollArea → QFormLayout with:
        #   - Employee info fields (name, ID, employer)
        #   - Form-specific medical fields
        #   - SignaturePad(s) for employee/examiner/OHN
        #   - Submit & Back buttons

    def submit_form(self):
        # 1. Gather data into nested dict
        # 2. Save signatures → temp file → base64 → cleanup
        # 3. local_db.save_submission(form_type, data)
        # 4. threading.Thread(target=db.sync_to_cloud).start()
        # 5. generate_pdf_for_form(form_type, data, employee_data)
```

## Form Registry

| File | Class | Form Type Key | Signatures |
|------|-------|--------------|------------|
| `form_drug_testing.py` | `FormDrugTesting` | `workplace_drug_testing` | Employee, OHN |
| `form_vitamin_b.py` | `FormVitaminB` | `vitamin_b_consent` | Employee, Practitioner |
| `form_certificate_fitness.py` | `FormCertificateFitness` | `certificate_of_fitness` | Employee, Examiner |
| `form_heights_questionnaire.py` | `FormHeightsQuestionnaire` | `heights_questionnaire` | Employee |
| `form_hot_cold_exposure.py` | `FormHotColdExposure` | `hot_cold_exposure` | Employee |
| `form_confined_spaces.py` | `FormConfinedSpaces` | `confined_spaces_questionnaire` | Employee |
| `form_musculoskeletal.py` | `FormMusculoskeletal` | `musculoskeletal_questionnaire` | Employee |
| `form_psychology.py` | `FormPsychology` | `psychology_questionnaire` | Employee |
| `form_cwb_referral.py` | `FormCWBReferral` | `cwb_medical_referral` | Employee, OHNP |
| `form_complete_wellbeing.py` | `FormCompleteWellbeing` | `complete_wellbeing` | Employee |
| `form_annexure3.py` | `FormAnnexure3` | `annexure3_cwb` | Employee, Examiner |

## Interdependencies

- `pages.signiture.SignaturePad` — Signature capture widget
- `pages.template_generator.generate_pdf_for_form` — PDF generation
- `Utility.local_db.local_db` — SQLite persistence
- `db` — Cloud sync trigger
- `main_window` — Navigation + employee context

## Key Notes

- **The `FormFactory` in `Utility/form_factory.py` is NOT used here.** These forms are all hand-coded because each has unique field layouts, medication tables, test-result grids, etc. that go beyond what the schema-driven factory supports.
- Each form type key must match an entry in `template_generator.TEMPLATE_MAP` and have a corresponding Jinja2 template in `templates/jinja2/`.
- The `__init__.py` re-exports all form classes for cleaner imports in `main.py`.
