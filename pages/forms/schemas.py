FormA_schema = {
    "title": "Occupational Health Examination",
    "description": "Please complete the employee details and medical test results.",
    "template_id": "1",   # forwards to your generate_html_pdf(..., template_id)
    "fields": [
        # Basic details
        {"name": "name",        "label": "Name",             "type": "text",     "required": True},
        {"name": "surname",     "label": "Surname",          "type": "text",     "required": True},
        {"name": "id_number",   "label": "ID Number",        "type": "text",     "required": True},
        {"name": "employer",    "label": "Employer",         "type": "text"},
        {"name": "job_title",   "label": "Job Title",        "type": "text"},
        {"name": "exam_date",   "label": "Examination Date", "type": "date",     "default": "today", "required": True},

        # Medical tests (each as a simple text input)
        {"name": "Glucose",                         "label": "Glucose",                          "type": "text"},
        {"name": "Cholesterol",                     "label": "Cholesterol",                      "type": "text"},
        {"name": "Blood Pressure",                  "label": "Blood Pressure",                   "type": "text"},
        {"name": "Weight",                          "label": "Weight",                           "type": "text"},
        {"name": "Height",                          "label": "Height",                           "type": "text"},
        {"name": "Audiometry",                      "label": "Audiometry",                       "type": "text"},
        {"name": "Urine Analysis",                  "label": "Urine Analysis",                   "type": "text"},
        {"name": "Lung Function",                   "label": "Lung Function",                    "type": "text"},
        {"name": "Vision",                          "label": "Vision",                           "type": "text"},
        {"name": "Working at heights",              "label": "Working at heights",               "type": "text"},
        {"name": "Hot/Cold Environments Questionnaire", "label": "Hot/Cold Environments Questionnaire", "type": "text"},
        {"name": "Psycho-social Questionnaire",     "label": "Psycho-social Questionnaire",      "type": "text"},
        {"name": "Musculoskeletal Questionnaire",   "label": "Musculoskeletal Questionnaire",    "type": "text"},

        {"name": "comments",     "label": "Comments / Notes", "type": "textarea"},
        {"name": "signature",    "label": "Digital Signature", "type": "signature", "required": True},
    ],
    "actions": ["submit", "generate_pdf", "back"],   # which buttons to show
    "submit_text": "Submit",
    "pdf_text": "Generate PDF",
    "back_text": "Back"
}


PreEmployment_schema = {
    "title": "Pre-Employment Medical",
    "description": "Fill in the candidate’s details and initial screening values.",
    "template_id": "pre_emp_v1",
    "fields": [
        {"name": "first_name", "label": "First Name", "type": "text", "required": True},
        {"name": "last_name",  "label": "Last Name",  "type": "text", "required": True},
        {"name": "id_number",  "label": "ID Number",  "type": "text", "required": True},
        {"name": "date",       "label": "Date",       "type": "date", "default": "today"},
        {"name": "bp",         "label": "BP",         "type": "text"},
        {"name": "hr",         "label": "Heart Rate", "type": "text"},
        {"name": "notes",      "label": "Notes",      "type": "textarea"},
        {"name": "signature",  "label": "Doctor Signature", "type": "signature", "required": True},
    ],
    "actions": ["submit", "back"]
}
