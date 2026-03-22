# `templates/jinja2/` — Active PDF Templates

These 11 Jinja2 HTML templates are the **production templates** used by `generate_pdf_for_form()` in `template_generator.py` to render medical form PDFs via WeasyPrint.

## Template Mapping

Templates are resolved via the `TEMPLATE_MAP` dict in `template_generator.py`:

| Form Type Key | Template File |
|--------------|---------------|
| `workplace_drug_testing` | `drug_testing.html` |
| `vitamin_b_consent` | `vitamin_b.html` |
| `certificate_of_fitness` | `certificate_fitness.html` |
| `heights_questionnaire` | `heights_questionnaire.html` |
| `hot_cold_exposure` | `hot_cold_exposure.html` |
| `confined_spaces_questionnaire` | `confined_spaces.html` |
| `musculoskeletal_questionnaire` | `musculoskeletal.html` |
| `psychology_questionnaire` | `psychology.html` |
| `cwb_medical_referral` | `cwb_referral.html` |
| `complete_wellbeing` | `complete_wellbeing.html` |
| `annexure3_cwb` | `annexure3.html` |

## Template Variables

All templates receive a flat `render_data` dict containing:

- **Form fields** — All values from the form's `submit_form()` data dict (may be nested: `employee.full_name`, `results.cocaine`, etc.)
- **Signature data URIs** — `{field_name}_base64` = `data:image/png;base64,...` for each signature field
- **Branding** — `logo_data_uri`, `stamp1_data_uri`, `stamp2_data_uri`
- **Employee info** (if selected) — `company_name`, `employee_name`, `employee_id`, `job_title`, `department`

## Rendering Pipeline

```
Form data dict ──→ Jinja2 template.render(**data) ──→ HTML string ──→ WeasyPrint ──→ PDF file
```

## Adding a New Template

1. Create `new_form.html` in this directory
2. Add mapping to `TEMPLATE_MAP` in `template_generator.py`
3. Create corresponding form class in `pages/forms/`
4. Register in `main.py`
