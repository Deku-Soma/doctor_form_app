# form_cwb_referral.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QFormLayout, QScrollArea, QDateEdit, QMessageBox, QTextEdit, QHBoxLayout
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



class FormCWBReferral(QWidget):
    FORM_TYPE = "cwb_medical_referral"

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
        title = QLabel("Complete Wellbeing - Referral Form")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")
        form_layout.addRow(title)

        # Patient Details
        self.name      = QLineEdit()
        self.surname   = QLineEdit()
        self.id_number = QLineEdit()
        self.job_title = QLineEdit()
        self.employer  = QLineEdit()
        # Register for autofill
        self.fields["first_name"] = self.name
        self.fields["surname"]    = self.surname
        self.fields["id_number"]  = self.id_number
        self.fields["job_title"]  = self.job_title
        self.examination_date = QDateEdit()
        self.examination_date.setDate(QDate.currentDate())

        form_layout.addRow("Name:", self.name)
        form_layout.addRow("Surname:", self.surname)
        form_layout.addRow("ID Number:", self.id_number)
        form_layout.addRow("Job Title:", self.job_title)
        form_layout.addRow("Employer:", self.employer)
        form_layout.addRow("Examination Date:", self.examination_date)

        # Referral Details
        form_layout.addRow(QLabel("<b>Referral for the following by OHMP/OHNP</b>"))
        self.referral_to = QLineEdit()
        self.referral_details = QTextEdit()
        self.referral_details.setMaximumHeight(100)

        form_layout.addRow("Referral To:", self.referral_to)
        form_layout.addRow("Details:", self.referral_details)

        # Practitioner Signature
        form_layout.addRow(QLabel("<b>Treating Practitioner</b>"))
        self.practitioner_date = QDateEdit()
        self.practitioner_date.setDate(QDate.currentDate())
        form_layout.addRow("Date:", self.practitioner_date)
        
        self.signature_pad = SignaturePad()
        form_layout.addRow("Signature:", self.signature_pad)
        
        clear_btn = QPushButton("Clear Signature")
        clear_btn.clicked.connect(self.signature_pad.clear)
        form_layout.addRow(clear_btn)

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

        back_btn = QPushButton("Back to Home")
        back_btn.clicked.connect(lambda: self.main_window.go_to_home())
        form_layout.addRow(back_btn)

        container.setLayout(form_layout)
        scroll.setWidget(container)
        layout = QVBoxLayout()
        layout.addWidget(scroll)
        self.setLayout(layout)

    def submit_form(self, status="approved"):
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
            "name": self.name.text(),
            "surname": self.surname.text(),
            "id_number": self.id_number.text(),
            "job_title": self.job_title.text(),
            "employer": self.employer.text(),
            "examination_date": self.examination_date.date().toString("yyyy-MM-dd"),
            "referral_to": self.referral_to.text(),
            "referral_details": self.referral_details.toPlainText(),
            "practitioner_signature": sig_base64,
            "practitioner_date": self.practitioner_date.date().toString("yyyy-MM-dd")
        }

        # Save to database
        try:
            user_session = self.main_window.fetch_session()
            user_id = user_session.get("id") if user_session else None
            
            sub_id = local_db.save_submission("cwb_medical_referral", data, user_id=user_id)
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
                generate_pdf_for_form("cwb_medical_referral", data, employee_data=emp_data, status=status)
                
                status_msg = "approved" if status == "approved" else "sent for doctor approval"
                QMessageBox.information(self, "Success", f"CWB Medical Referral saved successfully ({status_msg})!\nPDF generated in employee folder.")
            except Exception as pdf_error:
                print(f"PDF generation failed: {pdf_error}")
                import traceback
                traceback.print_exc()
                QMessageBox.information(self, "Success", "CWB Medical Referral saved successfully!\n(PDF generation failed - check logs)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save form: {e}")
