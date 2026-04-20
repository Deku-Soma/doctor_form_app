# Utility/template_fields.py
"""
Defines which form fields are company-level (not employee-specific).
Used by the template capture and autofill systems.

IMPORTANT: form_type keys must match the keys in pages/template_generator.py's TEMPLATE_MAP exactly.
"""

# Maps form_type -> list of field keys that are company-level (not employee-specific)
COMPANY_TEMPLATE_FIELDS = {
    "workplace_drug_testing": [
        "practitioner_name", "practitioner_reg_no", "clinic_name",
        "hazard_exposure", "reason_for_test"
    ],
    "certificate_of_fitness": [
        "practitioner_name", "practitioner_reg_no", "clinic_name",
        "practitioner_address", "job_title", "hazard_categories", "industry_type"
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
