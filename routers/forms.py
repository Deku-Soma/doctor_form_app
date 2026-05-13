"""
routers/forms.py — Form submission and autofill endpoints.

POST /forms/{form_type}/submit
    Accepts employee_id, company_id, status, and a data payload.
    Dynamically imports the correct process_submission() function and calls it.
    Returns {success, pdf_path, submission_id, error}.

GET /forms/{form_type}/autofill
    Returns the pre-fill context for the given employee and company.
    Used by the web UI to populate form fields on page load.
"""
import importlib
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from routers._deps import require_secret
from Utility.autofill import build_autofill_context
from Utility.local_db import local_db

router = APIRouter(
    prefix="/forms",
    tags=["forms"],
    dependencies=[Depends(require_secret)],
)

# ── Mapping from URL form_type → Python module path ──────────────────────────
# The URL slugs match the FORM_TYPE constants on each form class.
_FORM_MODULE_MAP: Dict[str, str] = {
    "annexure3_cwb":                 "pages.forms.form_annexure3",
    "certificate_of_fitness":        "pages.forms.form_certificate_fitness",
    "complete_wellbeing":            "pages.forms.form_complete_wellbeing",
    "workplace_drug_testing":        "pages.forms.form_drug_testing",
    "cwb_medical_referral":          "pages.forms.form_cwb_referral",
    "heights_questionnaire":         "pages.forms.form_heights_questionnaire",
    "hot_cold_exposure":             "pages.forms.form_hot_cold_exposure",
    "confined_spaces_questionnaire": "pages.forms.form_confined_spaces",
    "musculoskeletal_questionnaire": "pages.forms.form_musculoskeletal",
    "psychology_questionnaire":      "pages.forms.form_psychology",
    "vitamin_b_consent":             "pages.forms.form_vitamin_b",
}

# Cache imported modules so we only import each once per process
_module_cache: Dict[str, Any] = {}


def _get_process_fn(form_type: str):
    """Return the process_submission callable for the given form_type."""
    if form_type not in _FORM_MODULE_MAP:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown form type: '{form_type}'. "
                   f"Valid types: {sorted(_FORM_MODULE_MAP.keys())}",
        )
    if form_type not in _module_cache:
        module_path = _FORM_MODULE_MAP[form_type]
        try:
            mod = importlib.import_module(module_path)
        except ImportError as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Could not import form module '{module_path}': {exc}",
            )
        if not hasattr(mod, "process_submission"):
            raise HTTPException(
                status_code=500,
                detail=f"Module '{module_path}' has no process_submission() function.",
            )
        _module_cache[form_type] = mod.process_submission
    return _module_cache[form_type]


# ── Request / response models ─────────────────────────────────────────────────

class SubmitRequest(BaseModel):
    employee_id: str
    company_id: str
    data: Dict[str, Any]
    status: Optional[str] = "approved"
    # Optional: pass the full employee record so process_submission can use it
    # for PDF file organisation (same as getattr(main_window, 'selected_employee'))
    employee_data: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/{form_type}/submit")
def submit_form(form_type: str, body: SubmitRequest):
    """
    Submit a form.  Calls the extracted process_submission() function directly.
    No PyQt5 involved.  Returns the same dict that the desktop submit_form() uses.
    """
    process_fn = _get_process_fn(form_type)

    result = process_fn(
        employee_id=body.employee_id,
        company_id=body.company_id,
        data=body.data,
        status=body.status or "approved",
        employee_data=body.employee_data,
        user_id=body.user_id,
    )

    if not result.get("success"):
        # Return 422 with the error detail rather than 500 — it's a validation/
        # business-logic error, not a server crash.
        raise HTTPException(status_code=422, detail=result.get("error", "Submission failed"))

    return result


@router.get("/{form_type}/autofill")
def autofill(
    form_type: str,
    company_id: str = Query(...),
    employee_id: str = Query(...),
):
    """
    Return the autofill context for a form.  The web UI calls this on page load
    to pre-populate fields.  Returns {field_key: {value, source, is_locked}}.
    """
    if form_type not in _FORM_MODULE_MAP:
        raise HTTPException(status_code=404, detail=f"Unknown form type: '{form_type}'")

    # Fetch the employee record so build_autofill_context() can use personal data
    employee_row = local_db.get_employee(employee_id)
    employee = dict(employee_row) if employee_row else {}

    context = build_autofill_context(company_id, employee, form_type)
    return {"autofill": context}


@router.get("")
def list_form_types():
    """Return all supported form type slugs."""
    return {"form_types": sorted(_FORM_MODULE_MAP.keys())}
