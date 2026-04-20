# Utility/autofill.py
"""
Centralised autofill logic for all 11 form types.

Usage in each form's showEvent():
    from Utility.autofill import build_autofill_context, apply_autofill_to_form
    context = build_autofill_context(company_id, employee, self.FORM_TYPE)
    apply_autofill_to_form(self, context)

Each form class must have:
    - FORM_TYPE class constant (matching TEMPLATE_MAP key)
    - self.fields dict mapping field_key -> QWidget (registered in init_ui)
"""

from PyQt5.QtWidgets import QLineEdit, QComboBox, QCheckBox
from Utility.local_db import local_db


def build_autofill_context(company_id: str, employee: dict, form_type: str) -> dict:
    """
    Returns a merged dict of field_key -> {"value": ..., "source": ..., "is_locked": bool}
    for pre-filling a form.

    Priority (lowest to highest):
      1. Company template defaults (from company_templates table)
      2. Employee personal data (from selected_employee in session)

    Employee data always overwrites company template data on key collision.

    Args:
        company_id: ID of the selected company (from main_window.selected_company)
        employee:   Dict from local_db.get_employee() — keys: full_name, id_number, etc.
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

    # Layer 2: employee personal data (overwrites template on collision)
    # Keys are standardised names registered in self.fields across all form classes
    employee_fields = {
        # Drug testing form uses these
        "full_name":           employee.get("full_name", ""),
        "id_number":           employee.get("id_number", ""),
        "job_title":           employee.get("job_title", ""),
        # Certificate fitness form splits name/surname
        "first_name":          employee.get("full_name", "").split()[0] if employee.get("full_name") else "",
        "surname":             " ".join(employee.get("full_name", "").split()[1:]) if employee.get("full_name") else "",
        "id_pp_number":        employee.get("id_number", ""),
        "occupation":          employee.get("job_title", ""),
        # Heights/other forms use full_name_surname
        "full_name_surname":   employee.get("full_name", ""),
        # Standardised keys for autofill system
        "employee_name":       employee.get("full_name", ""),
        "employee_id_no":      employee.get("id_number", ""),
        "employee_job_title":  employee.get("job_title", ""),
        "employee_department": employee.get("department", ""),
    }
    for key, value in employee_fields.items():
        if value:
            context[key] = {"value": value, "source": "employee", "is_locked": False}

    return context


def apply_autofill_to_form(form_widget, context: dict):
    """
    Populate a form's widgets from a context dict returned by build_autofill_context().

    Expects form_widget to have a self.fields dict mapping field_key -> QWidget.
    Fields sourced from "company_template" get a teal left border and tooltip.
    Fields sourced from "employee" are set silently (no visual marking).
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
