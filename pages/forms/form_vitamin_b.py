# form_vitamin_b.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QFormLayout, QScrollArea, QDateEdit, QMessageBox, QTextEdit, QHBoxLayout
)
import os
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



class FormVitaminB(QWidget):
    FORM_TYPE = "vitamin_b_consent"

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
        title = QLabel("Vitamin B12 Consent Form")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        form_layout.addRow(title)

        # Date and Company
        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.company = QLineEdit()

        form_layout.addRow("Date:", self.date)
        form_layout.addRow("Company:", self.company)

        # Consent Text (read-only display)
        consent_label = QLabel("<b>Consent Declaration:</b>")
        form_layout.addRow(consent_label)
        
        self.consent_text = QTextEdit()
        self.consent_text.setReadOnly(True)
        self.consent_text.setPlainText(
            "I hereby consent to receive the Vitamin B12 injection. I acknowledge that I have had the opportunity to ask questions or request further information before proceeding.\n\n"
            "I agree that YGAM11 t/a Complete Wellbeing will not be held liable for any adverse effects or complications that may arise as a result of taking the Vitamin B12 injection.\n\n"
            "By signing below, I give my consent to receive this injection as per the above terms."
        )
        self.consent_text.setMaximumHeight(120)
        form_layout.addRow(self.consent_text)

        # Patient Details
        form_layout.addRow(QLabel("<b>Patient Details</b>"))
        self.name_surname = QLineEdit()
        self.id_number    = QLineEdit()
        # Register for autofill
        self.fields["full_name_surname"] = self.name_surname
        self.fields["id_number"]         = self.id_number

        form_layout.addRow("Name & Surname:", self.name_surname)
        form_layout.addRow("ID Number:", self.id_number)

        # Signature
        form_layout.addRow(QLabel("<b>Signature</b>"))
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
        # Save signature
        signature_path = "temp_signature.png"
        self.signature_pad.get_signature_image().save(signature_path)
        
        # Encode signature to base64
        try:
            with open(signature_path, "rb") as f:
                signature_base64 = base64.b64encode(f.read()).decode("utf-8")
            
            # Cleanup temp file
            if os.path.exists(signature_path):
                os.remove(signature_path)
                
        except Exception as e:
            print(f"Error encoding signature: {e}")
            signature_base64 = ""

        # Prepare data structure
        data = {
            "date": self.date.date().toString("dd MMMM yyyy"),
            "company": self.company.text(),
            "consent_text": self.consent_text.toPlainText(),
            "entries": [{
                "no": 1,
                "name_surname": self.name_surname.text(),
                "id_number": self.id_number.text(),
                "signature_text": self.name_surname.text(),
                "signature_img": signature_base64
            }],
            # For database searchability
            "name": self.name_surname.text().split()[0] if self.name_surname.text() else "",
            "surname": " ".join(self.name_surname.text().split()[1:]) if len(self.name_surname.text().split()) > 1 else "",
            "id_number": self.id_number.text(),
            
            # Fields expected by vitamin_b.html template
            "patient_name": self.name_surname.text(),
            "signature_data": signature_base64,
            "signature_date": self.date.date().toString("dd MMMM yyyy")
        }

        # Save to database
        try:
            user_session = self.main_window.fetch_session()
            user_id = user_session.get("id") if user_session else None
            
            sub_id = local_db.save_submission("vitamin_b_consent", data, user_id=user_id)
            print(f"Saved locally with ID: {sub_id}")

            company = getattr(self.main_window, 'selected_company', None) or {}
            _capture_company_template_if_first(company.get('id', ''), self.FORM_TYPE, data)

            # Trigger sync in background
            sync_thread = threading.Thread(target=db.sync_to_cloud)
            sync_thread.start()
            
            # Generate PDF
            pdf_success = False
            try:
                from pages.template_generator import generate_pdf_for_form
                # Pass employee data for file organization
                emp_data = getattr(self.main_window, 'selected_employee', None)
                generate_pdf_for_form("vitamin_b_consent", data, employee_data=emp_data, status=status)
                
                pdf_success = True
                status_msg = "approved" if status == "approved" else "sent for doctor approval"
                QMessageBox.information(self, "Success", f"Vitamin B Consent saved successfully ({status_msg})!\nPDF generated in employee folder.")
            except Exception as pdf_error:
                print(f"PDF generation failed: {pdf_error}")
                QMessageBox.information(self, "Success", "Vitamin B Consent saved successfully!\n(PDF generation failed - check logs)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save form: {e}")
