# form_annexure3.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QFormLayout, QScrollArea, QDateEdit, QMessageBox,
    QTextEdit, QRadioButton, QButtonGroup, QHBoxLayout
)
from PyQt5.QtCore import QDate
from pages.signiture import SignaturePad
import base64
from Utility.local_db import local_db
from Utility.autofill import build_autofill_context, apply_autofill_to_form
from Utility.template_fields import COMPANY_TEMPLATE_FIELDS, UNIVERSAL_TEMPLATE_FIELDS
from db import sync_company_templates_to_cloud
import db
import threading
import os


def _capture_company_template_if_first(company_id, form_type, data):
    if not company_id: return
    if local_db.get_company_template(company_id, form_type): return
    capturable_keys = list(set(COMPANY_TEMPLATE_FIELDS.get(form_type, []) + UNIVERSAL_TEMPLATE_FIELDS))
    def _get(d, key):
        if key in d: return d[key]
        for v in d.values():
            if isinstance(v, dict) and key in v: return v[key]
        return None
    fields_to_save = {k: {"value": _get(data, k), "label": k.replace("_", " ").title(), "is_locked": False} for k in capturable_keys if _get(data, k)}
    if fields_to_save:
        local_db.save_company_template(company_id, form_type, fields_to_save)
        threading.Thread(target=sync_company_templates_to_cloud, args=(company_id,), daemon=True).start()



class FormAnnexure3(QWidget):
    FORM_TYPE = "annexure3_cwb"

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
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        form_layout = QFormLayout()

        # Title
        title = QLabel("Construction Annexure 3 - Medical Certificate of Fitness")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")
        form_layout.addRow(title)

        # Basic Details
        self.company       = QLineEdit()
        self.employee_name = QLineEdit()
        self.id_pp_number  = QLineEdit()
        self.co_number     = QLineEdit()
        # Register for autofill
        self.fields["employee_name"] = self.employee_name
        self.fields["id_pp_number"]  = self.id_pp_number
        self.fields["id_number"]     = self.id_pp_number  # alias

        form_layout.addRow("Company:", self.company)
        form_layout.addRow("Employee Name & Surname:", self.employee_name)
        form_layout.addRow("ID/PP Number:", self.id_pp_number)
        form_layout.addRow("Co. Number:", self.co_number)

        # Matrix Details
        form_layout.addRow(QLabel("<b>Matrix Details</b>"))
        self.occupation = QTextEdit()
        self.occupation.setMaximumHeight(80)
        self.possible_exposures = QTextEdit()
        self.possible_exposures.setMaximumHeight(80)
        self.job_requirements = QTextEdit()
        self.job_requirements.setMaximumHeight(80)
        self.protective_equipment = QTextEdit()
        self.protective_equipment.setMaximumHeight(80)

        form_layout.addRow("Occupation:", self.occupation)
        form_layout.addRow("Possible Exposures:", self.possible_exposures)
        form_layout.addRow("Job Specific Requirements:", self.job_requirements)
        form_layout.addRow("Protective Equipment:", self.protective_equipment)

        # Fitness Status
        form_layout.addRow(QLabel("<b>Declaration by Medical Examiner</b>"))
        form_layout.addRow(QLabel("<i>Employee is Fit/Unfit to perform duties</i>"))
        
        self.fitness_group = QButtonGroup()
        fit_radio = QRadioButton("Fit")
        unfit_radio = QRadioButton("Unfit")
        self.fitness_group.addButton(fit_radio)
        self.fitness_group.addButton(unfit_radio)
        self.fitness_status = {"fit": fit_radio, "unfit": unfit_radio}
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(fit_radio)
        h_layout.addWidget(unfit_radio)
        h_layout.addStretch()
        form_layout.addRow("Fitness Status:", h_layout)

        # Practitioner Details
        form_layout.addRow(QLabel("<b>Practitioner Details</b>"))
        self.practitioner_name  = QLineEdit()
        self.practice_number    = QLineEdit()
        # Register practitioner for autofill
        self.fields["practitioner_name"]   = self.practitioner_name
        self.fields["practitioner_reg_no"] = self.practice_number
        self.exam_date = QDateEdit()
        self.exam_date.setDate(QDate.currentDate())
        self.practice_address = QLineEdit()

        form_layout.addRow("Practitioner Name:", self.practitioner_name)
        form_layout.addRow("Practice Number:", self.practice_number)
        form_layout.addRow("Date:", self.exam_date)
        form_layout.addRow("Practice Address:", self.practice_address)

        # Signature
        form_layout.addRow(QLabel("<b>Practitioner Signature</b>"))
        self.signature_pad = SignaturePad()
        form_layout.addRow("Signature:", self.signature_pad)
        
        clear_btn = QPushButton("Clear Signature")
        clear_btn.clicked.connect(self.signature_pad.clear)
        form_layout.addRow(clear_btn)

        # Buttons
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

        back_btn = QPushButton("Back to Home")
        back_btn.clicked.connect(lambda: self.main_window.go_to_home())
        form_layout.addRow(back_btn)

        container.setLayout(form_layout)
        scroll.setWidget(container)
        layout = QVBoxLayout()
        layout.addWidget(scroll)
        self.setLayout(layout)

    def submit_form(self, status="approved"):
        # Get fitness status
        fitness = ""
        if self.fitness_status["fit"].isChecked():
            fitness = "Fit"
        elif self.fitness_status["unfit"].isChecked():
            fitness = "Unfit"

        # Save signature
        sig_path = "temp_signature.png"
        self.signature_pad.get_signature_image().save(sig_path)

        try:
            with open(sig_path, "rb") as f:
                sig_base64 = base64.b64encode(f.read()).decode("utf-8")
            
            # Cleanup temp file
            if os.path.exists(sig_path):
                os.remove(sig_path)

        except Exception as e:
            print(f"Error encoding signature: {e}")
            sig_base64 = ""

        # Prepare data
        data = {
            "company": self.company.text(),
            "employee_name": self.employee_name.text(),
            "id_pp_number": self.id_pp_number.text(),
            "co_number": self.co_number.text(),
            "occupation": self.occupation.toPlainText(),
            "possible_exposures": self.possible_exposures.toPlainText(),
            "job_requirements": self.job_requirements.toPlainText(),
            "protective_equipment": self.protective_equipment.toPlainText(),
            "fitness_status": fitness,
            "practitioner_name": self.practitioner_name.text(),
            "practice_number": self.practice_number.text(),
            "exam_date": self.exam_date.date().toString("yyyy-MM-dd"),
            "practice_address": self.practice_address.text(),
            "practitioner_signature": sig_base64,
            # For database searchability
            "name": self.employee_name.text().split()[0] if self.employee_name.text() else "",
            "surname": " ".join(self.employee_name.text().split()[1:]) if len(self.employee_name.text().split()) > 1 else "",
            "id_number": self.id_pp_number.text()
        }

        # Save to database
        try:
            user_session = self.main_window.fetch_session()
            user_id = user_session.get("id") if user_session else None
            
            sub_id = local_db.save_submission("annexure3_cwb", data, user_id=user_id)
            print(f"Saved locally with ID: {sub_id}")

            company = getattr(self.main_window, 'selected_company', None) or {}
            _capture_company_template_if_first(company.get('id', ''), self.FORM_TYPE, data)

            sync_thread = threading.Thread(target=db.sync_to_cloud)
            sync_thread.start()
            
            # Generate PDF
            try:
                from pages.template_generator import generate_pdf_for_form
                # Pass employee data for file organization
                emp_data = getattr(self.main_window, 'selected_employee', None)
                generate_pdf_for_form("annexure3_cwb", data, employee_data=emp_data, status=status)
                
                status_msg = "approved" if status == "approved" else "sent for doctor approval"
                QMessageBox.information(self, "Success", f"Annexure 3 saved successfully ({status_msg})!\nPDF generated in employee folder.")
            except Exception as pdf_error:
                print(f"PDF generation failed: {pdf_error}")
                import traceback
                traceback.print_exc()
                QMessageBox.information(self, "Success", "Annexure 3 saved successfully!\n(PDF generation failed - check logs)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save form: {e}")
