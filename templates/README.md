# `templates/` — HTML Templates

This directory contains HTML templates used for PDF generation.

## Structure

```
templates/
├── *.html              # 12 legacy raw HTML templates (static, not Jinja2)
└── jinja2/             # 11 active Jinja2 templates used for PDF rendering
```

## Legacy Templates (Root)

The 12 `.html` files in the root of this directory are **earlier versions** of the medical forms. They were likely used before the Jinja2 migration and are referenced by the legacy `generate_html_pdf()` function in `template_generator.py`.

| File | Form |
|------|------|
| `Workplace Drug Testing Consent Form.html` | Drug testing consent |
| `Vitamin B consent form.html` | Vitamin B consent |
| `Certificate of fitness.html` | Fitness certificate |
| `CWB heights questionnaire.html` | Heights questionnaire |
| `Hot and Cold Exposure questionnaire.html` | Temperature exposure |
| `Confined Spaces Questionnaire for Employees.html` | Confined spaces |
| `Muscoskeletal questionnaire.html` | Musculoskeletal assessment |
| `Psychology questionnaire.html` | K10 psychological assessment |
| `CWB Medical Referral.html` | CWB referral |
| `Complete wellbeing.html` | Wellbeing assessment |
| `Annexure 3 cwb.html` | Construction certificate |
| `form.html` | Generic form template |

## Active Templates (`jinja2/`)

See [jinja2/README.md](jinja2/README.md) for details on the active Jinja2 templates.

These are the templates **actively used** by `generate_pdf_for_form()` in `template_generator.py`. The mapping from form type to template file is defined in `TEMPLATE_MAP`.
