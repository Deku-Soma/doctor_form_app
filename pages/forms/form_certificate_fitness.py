# form_certificate_fitness.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
    QVBoxLayout, QFormLayout, QScrollArea, QDateEdit, QMessageBox,
    QCheckBox, QRadioButton, QButtonGroup, QGroupBox, QHBoxLayout
)
from PyQt5.QtCore import QDate
from pages.signiture import SignaturePad
from pages.template_generator import generate_html_pdf
import base64
from Utility.local_db import local_db
from Utility.autofill import build_autofill_context, apply_autofill_to_form
from Utility.template_fields import COMPANY_TEMPLATE_FIELDS, UNIVERSAL_TEMPLATE_FIELDS
from db import sync_company_templates_to_cloud
import db
import threading
import os


def _capture_company_template_if_first(company_id: str, form_type: str, data: dict):
    """Save company-level fields as a reusable template on the first submission."""
    if not company_id:
        return
    if local_db.get_company_template(company_id, form_type):
        return
    capturable_keys = list(set(
        COMPANY_TEMPLATE_FIELDS.get(form_type, []) + UNIVERSAL_TEMPLATE_FIELDS
    ))
    def _get(d, key):
        if key in d: return d[key]
        for v in d.values():
            if isinstance(v, dict) and key in v: return v[key]
        return None
    fields_to_save = {
        key: {"value": _get(data, key), "label": key.replace("_", " ").title(), "is_locked": False}
        for key in capturable_keys if _get(data, key)
    }
    if fields_to_save:
        local_db.save_company_template(company_id, form_type, fields_to_save)
        threading.Thread(target=sync_company_templates_to_cloud, args=(company_id,), daemon=True).start()



def process_submission(employee_id: str, company_id: str, data: dict, status: str = "approved", employee_data: dict = None, user_id: str = None) -> dict:
    """
    UI-agnostic form processing for certificate_of_fitness.
    Returns {'success': bool, 'pdf_path': str | None, 'submission_id': str | None, 'error': str | None}
    """
    import traceback
    from pages.template_generator import generate_pdf_for_form
    try:
        sub_id = local_db.save_submission("certificate_of_fitness", data, user_id=user_id)
        _capture_company_template_if_first(company_id, "certificate_of_fitness", data)
        threading.Thread(target=db.sync_to_cloud, daemon=True).start()

        pdf_path = None
        try:
            pdf_path = generate_pdf_for_form("certificate_of_fitness", data, employee_data=employee_data, status=status)
        except Exception as pdf_err:
            print(f"[certificate_fitness] PDF generation failed: {pdf_err}")
            traceback.print_exc()

        return {"success": True, "pdf_path": pdf_path, "submission_id": sub_id, "error": None}
    except Exception as e:
        return {"success": False, "pdf_path": None, "submission_id": None, "error": str(e)}


class FormCertificateFitness(QWidget):
    FORM_TYPE = "certificate_of_fitness"

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.fields = {}
        self.init_ui()

    def showEvent(self, event):
        """Pre-fill employee and company template data."""
        super().showEvent(event)
        employee = getattr(self.main_window, 'selected_employee', None) or {}
        company  = getattr(self.main_window, 'selected_company', None) or {}
        context  = build_autofill_context(company.get('id', ''), employee, self.FORM_TYPE)
        apply_autofill_to_form(self, context)

    def init_ui(self):
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        form_layout = QFormLayout()

        # Title
        title = QLabel("CERTIFICATE OF FITNESS")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        form_layout.addRow(title)

        # Personal Details
        form_layout.addRow(QLabel("<b>Personal Details</b>"))
        self.first_name = QLineEdit()
        self.surname = QLineEdit()
        self.id_pp_number = QLineEdit()
        self.company = QLineEdit()
        self.occupation = QLineEdit()
        # Register for autofill
        self.fields["first_name"]   = self.first_name
        self.fields["surname"]      = self.surname
        self.fields["id_pp_number"] = self.id_pp_number
        self.fields["occupation"]   = self.occupation
        self.date_of_examination = QDateEdit()
        self.date_of_examination.setDate(QDate.currentDate())
        self.date_of_expiry = QDateEdit()
        self.date_of_expiry.setDate(QDate.currentDate().addYears(1))

        form_layout.addRow("Name:", self.first_name)
        form_layout.addRow("Surname:", self.surname)
        form_layout.addRow("ID/PP Number:", self.id_pp_number)
        form_layout.addRow("Company:", self.company)
        form_layout.addRow("Occupation:", self.occupation)
        form_layout.addRow("Date of Examination:", self.date_of_examination)
        form_layout.addRow("Date of Expiry:", self.date_of_expiry)

        # Type of Medical
        form_layout.addRow(QLabel("<b>Type of Medical</b>"))
        self.medical_type = {}
        medical_types = [
            ("Pre-employment", "medical_type_pre_employment"),
            ("Baseline", "medical_type_baseline"),
            ("Periodical", "medical_type_periodical"),
            ("Exit", "medical_type_exit")
        ]
        
        for label, key in medical_types:
            checkbox = QCheckBox(label)
            self.medical_type[key] = checkbox
            form_layout.addRow(checkbox)

        # Outcome of Medical Examination
        form_layout.addRow(QLabel("<b>Outcome of Medical Examination</b>"))
        self.outcome_group = QButtonGroup()
        self.outcome_buttons = {}
        outcomes = [
            "Fit for duty",
            "Fit for duty, with conditions",
            "Fit for duty, with restrictions",
            "Not fit for duty, requires referral and follow-up"
        ]
        
        for outcome in outcomes:
            radio = QRadioButton(outcome)
            self.outcome_group.addButton(radio)
            self.outcome_buttons[outcome] = radio
            form_layout.addRow(radio)

        self.outcome_comments = QTextEdit()
        self.outcome_comments.setMaximumHeight(80)
        form_layout.addRow("Comments:", self.outcome_comments)

        # Tests Conducted
        form_layout.addRow(QLabel("<b>Tests Conducted</b>"))
        self.tests = {}
        test_list = [
            ("Physical examination", "test_physical_examination"),
            ("Blood Pressure", "test_blood_pressure"),
            ("Glucose Test", "test_glucose"),
            ("Urine screening", "test_urine_screening"),
            ("Audiometry", "test_audiometry"),
            ("Lung Function", "test_lung_function"),
            ("BMI (Height & Weight)", "test_bmi"),
            ("Drug Test", "test_drug_test"),
            ("Vision screening", "test_vision_screening"),
            ("HIV Test", "test_hiv"),
            ("Cholesterol", "test_cholesterol"),
            ("Other", "test_other")
        ]
        
        for label, key in test_list:
            checkbox = QCheckBox(label)
            self.tests[key] = checkbox
            form_layout.addRow(checkbox)

        self.tests_comments = QTextEdit()
        self.tests_comments.setMaximumHeight(80)
        form_layout.addRow("Test Comments:", self.tests_comments)

        # Additional Questionnaires
        form_layout.addRow(QLabel("<b>Additional Questionnaires Completed</b>"))
        self.questionnaires = {}
        questionnaire_list = [
            ("Working at heights", "q_working_at_heights"),
            ("Shift work", "q_shift_work"),
            ("Psycho-social", "q_psycho_social"),
            ("General health", "q_general_health"),
            ("Other", "q_other")
        ]
        
        for label, key in questionnaire_list:
            checkbox = QCheckBox(label)
            self.questionnaires[key] = checkbox
            form_layout.addRow(checkbox)

        # Practitioner Details
        form_layout.addRow(QLabel("<b>Occupational Health Medical Practitioner</b>"))
        self.practitioner_name = QLineEdit()
        self.practitioner_reg_numbers = QLineEdit()
        # Register practitioner fields for autofill
        self.fields["practitioner_name"]   = self.practitioner_name
        self.fields["practitioner_reg_no"] = self.practitioner_reg_numbers
        self.practitioner_date = QDateEdit()
        self.practitioner_date.setDate(QDate.currentDate())
        self.practitioner_address = QLineEdit()

        form_layout.addRow("Practitioner Name:", self.practitioner_name)
        form_layout.addRow("HPCSA/SANC/PR Number:", self.practitioner_reg_numbers)
        form_layout.addRow("Date:", self.practitioner_date)
        form_layout.addRow("Practice Address:", self.practitioner_address)

        # Practitioner Signature
        form_layout.addRow(QLabel("<b>Practitioner Signature</b>"))
        self.signature_pad = SignaturePad()
        form_layout.addRow("Digital Signature:", self.signature_pad)
        
        clear_sig_btn = QPushButton("Clear Signature")
        clear_sig_btn.clicked.connect(self.signature_pad.clear)
        form_layout.addRow(clear_sig_btn)

        # Action Buttons
        btn_layout = QHBoxLayout()
        
        approve_btn = QPushButton("✅ Approve")
        approve_btn.setStyleSheet("background-color: #1abc9c; color: white; padding: 10px 20px; font-weight: bold; border-radius: 5px;")
        approve_btn.clicked.connect(lambda: self.submit_form(status="approved"))
        btn_layout.addWidget(approve_btn)
        
        pending_btn = QPushButton("⏳ Needs Doctor Approval")
        pending_btn.setStyleSheet("background-color: #f39c12; color: white; padding: 10px 20px; font-weight: bold; border-radius: 5px;")
        pending_btn.clicked.connect(lambda: self.submit_form(status="pending"))
        btn_layout.addWidget(pending_btn)
        
        form_layout.addRow(btn_layout)

        # Back Button
        back_btn = QPushButton("Back to Home")
        back_btn.clicked.connect(lambda: self.main_window.go_to_home())
        form_layout.addRow(back_btn)

        # Wrap layout
        container.setLayout(form_layout)
        scroll.setWidget(container)
        layout = QVBoxLayout()
        layout.addWidget(scroll)
        self.setLayout(layout)

    def submit_form(self, status="approved"):
        # Collect widget values
        medical_type_data = {k: "1" if cb.isChecked() else "" for k, cb in self.medical_type.items()}
        outcome = next((t for t, r in self.outcome_buttons.items() if r.isChecked()), "")
        tests_data = {k: "1" if cb.isChecked() else "" for k, cb in self.tests.items()}
        questionnaires_data = {k: "1" if cb.isChecked() else "" for k, cb in self.questionnaires.items()}

        signature_path = "temp_signature.png"
        self.signature_pad.get_signature_image().save(signature_path)
        try:
            with open(signature_path, "rb") as f:
                signature_base64 = base64.b64encode(f.read()).decode("utf-8")
            if os.path.exists(signature_path):
                os.remove(signature_path)
        except Exception as e:
            print(f"Error encoding signature: {e}")
            signature_base64 = ""

        data = {
            "first_name": self.first_name.text(),
            "surname": self.surname.text(),
            "id_pp_number": self.id_pp_number.text(),
            "company": self.company.text(),
            "occupation": self.occupation.text(),
            "date_of_examination": self.date_of_examination.date().toString("yyyy-MM-dd"),
            "date_of_expiry": self.date_of_expiry.date().toString("yyyy-MM-dd"),
            **medical_type_data,
            "outcome": outcome,
            "outcome_comments": self.outcome_comments.toPlainText(),
            **tests_data,
            "tests_comments": self.tests_comments.toPlainText(),
            **questionnaires_data,
            "practitioner_name": self.practitioner_name.text(),
            "practitioner_reg_numbers": self.practitioner_reg_numbers.text(),
            "practitioner_date": self.practitioner_date.date().toString("yyyy-MM-dd"),
            "practitioner_address": self.practitioner_address.text(),
            "practitioner_signature_base64": signature_base64,
            "name": self.first_name.text(),
            "id_number": self.id_pp_number.text()
        }

        user_session = self.main_window.fetch_session()
        user_id = user_session.get("id") if user_session else None
        company = getattr(self.main_window, 'selected_company', None) or {}
        emp_data = getattr(self.main_window, 'selected_employee', None)

        result = process_submission(
            employee_id=emp_data.get("id", "") if emp_data else "",
            company_id=company.get("id", ""),
            data=data, status=status, employee_data=emp_data, user_id=user_id,
        )

        if result["success"]:
            status_msg = "approved" if status == "approved" else "sent for doctor approval"
            msg = f"Form saved successfully ({status_msg})!"
            msg += "\nPDF generated in employee folder." if result["pdf_path"] else "\n(PDF generation failed)"
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.critical(self, "Error", f"Failed to save form: {result['error']}")

