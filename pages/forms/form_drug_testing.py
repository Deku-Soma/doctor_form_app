# form_drug_testing.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
    QVBoxLayout, QFormLayout, QScrollArea, QDateEdit, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QHBoxLayout
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
        return  # Already captured

    capturable_keys = list(set(
        COMPANY_TEMPLATE_FIELDS.get(form_type, []) + UNIVERSAL_TEMPLATE_FIELDS
    ))

    def _get(d, key):
        if key in d:
            return d[key]
        for v in d.values():
            if isinstance(v, dict) and key in v:
                return v[key]
        return None

    fields_to_save = {
        key: {"value": _get(data, key), "label": key.replace("_", " ").title(), "is_locked": False}
        for key in capturable_keys if _get(data, key)
    }
    if fields_to_save:
        local_db.save_company_template(company_id, form_type, fields_to_save)
        threading.Thread(
            target=sync_company_templates_to_cloud, args=(company_id,), daemon=True
        ).start()


class FormDrugTesting(QWidget):
    FORM_TYPE = "workplace_drug_testing"

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.fields = {}   # field_key -> QWidget for autofill
        self.init_ui()

    def showEvent(self, event):
        """Pre-fill employee and company template data."""
        super().showEvent(event)
        employee = getattr(self.main_window, 'selected_employee', None) or {}
        company  = getattr(self.main_window, 'selected_company', None) or {}
        context  = build_autofill_context(company.get('id', ''), employee, self.FORM_TYPE)
        apply_autofill_to_form(self, context)

    def init_ui(self):
        # Scroll area for long form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        form_layout = QFormLayout()

        # Title
        title = QLabel("Workplace Drug Testing Consent Form")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        form_layout.addRow(title)

        # Employee Details
        form_layout.addRow(QLabel("<b>Employee Details</b>"))
        self.full_name = QLineEdit()
        self.id_number = QLineEdit()
        self.employer  = QLineEdit()
        self.job_title = QLineEdit()
        # Register for autofill
        self.fields["full_name"] = self.full_name
        self.fields["id_number"] = self.id_number
        self.fields["job_title"] = self.job_title

        form_layout.addRow("Full Name:", self.full_name)
        form_layout.addRow("ID Number:", self.id_number)
        form_layout.addRow("Employer:", self.employer)
        form_layout.addRow("Job Title:", self.job_title)

        # Medication Table
        form_layout.addRow(QLabel("<b>Medication/Supplements/Drugs taken in the past week:</b>"))
        self.medication_table = QTableWidget(5, 3)
        self.medication_table.setHorizontalHeaderLabels(["Name of Medication", "Date Last Taken", "Reason for Treatment"])
        self.medication_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        form_layout.addRow(self.medication_table)

        # Test Results
        form_layout.addRow(QLabel("<b>Test Results</b>"))
        self.results = {}
        drugs = [
            ("Cocaine - COC", "cocaine"),
            ("Amphetamine - AMP", "amphetamine"),
            ("Cannabis - THC", "cannabis"),
            ("Opiates/Morphine/Heroin - MOP", "opiates"),
            ("Methamphetamine/Tik/Crystal - MET", "methamphetamine"),
            ("Benzodiazepine/Valium/Sedatives - BZO", "benzodiazepine")
        ]

        for drug_label, drug_key in drugs:
            combo = QComboBox()
            combo.addItems(["", "Negative", "Positive"])
            self.results[drug_key] = combo
            form_layout.addRow(f"{drug_label}:", combo)

        # Test Metadata
        form_layout.addRow(QLabel("<b>Test Metadata</b>"))
        self.lot_number = QLineEdit()
        self.expiry_date = QDateEdit()
        self.expiry_date.setDate(QDate.currentDate().addYears(1))
        self.date_tested = QDateEdit()
        self.date_tested.setDate(QDate.currentDate())

        form_layout.addRow("Lot Number:", self.lot_number)
        form_layout.addRow("Expiry Date:", self.expiry_date)
        form_layout.addRow("Date Tested:", self.date_tested)

        # Employee Signature
        form_layout.addRow(QLabel("<b>Employee Signature</b>"))
        self.employee_signature_pad = SignaturePad()
        form_layout.addRow("Employee Signature:", self.employee_signature_pad)
        
        clear_emp_sig_btn = QPushButton("Clear Employee Signature")
        clear_emp_sig_btn.clicked.connect(self.employee_signature_pad.clear)
        form_layout.addRow(clear_emp_sig_btn)

        # OHN/OHP Signature
        form_layout.addRow(QLabel("<b>OHN/OHP Signature</b>"))
        self.ohn_signature_pad = SignaturePad()
        form_layout.addRow("OHN/OHP Signature:", self.ohn_signature_pad)
        
        clear_ohn_sig_btn = QPushButton("Clear OHN/OHP Signature")
        clear_ohn_sig_btn.clicked.connect(self.ohn_signature_pad.clear)
        form_layout.addRow(clear_ohn_sig_btn)

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
        # Gather medication data
        meds = []
        for row in range(self.medication_table.rowCount()):
            name_item = self.medication_table.item(row, 0)
            date_item = self.medication_table.item(row, 1)
            reason_item = self.medication_table.item(row, 2)
            
            name = name_item.text() if name_item else ""
            date = date_item.text() if date_item else ""
            reason = reason_item.text() if reason_item else ""
            
            if name or date or reason:  # Only add if at least one field is filled
                meds.append({
                    "name": name,
                    "date_last_taken": date,
                    "reason": reason
                })

        # Gather test results
        results_data = {}
        for drug_key, combo in self.results.items():
            results_data[drug_key] = combo.currentText()

        # Save employee signature
        employee_sig_path = "temp_employee_signature.png"
        self.employee_signature_pad.get_signature_image().save(employee_sig_path)
        
        # Save OHN signature
        ohn_sig_path = "temp_ohn_signature.png"
        self.ohn_signature_pad.get_signature_image().save(ohn_sig_path)

        # Encode signatures to base64
        try:
            with open(employee_sig_path, "rb") as f:
                employee_sig_base64 = base64.b64encode(f.read()).decode("utf-8")
            with open(ohn_sig_path, "rb") as f:
                ohn_sig_base64 = base64.b64encode(f.read()).decode("utf-8")

            # Cleanup temp files
            if os.path.exists(employee_sig_path):
                os.remove(employee_sig_path)
            if os.path.exists(ohn_sig_path):
                os.remove(ohn_sig_path)

        except Exception as e:
            print(f"Error encoding signatures: {e}")
            employee_sig_base64 = ""
            ohn_sig_base64 = ""

        # Prepare data structure
        data = {
            "employee": {
                "full_name": self.full_name.text(),
                "id_number": self.id_number.text(),
                "employer": self.employer.text(),
                "job_title": self.job_title.text()
            },
            "meds": meds,
            "results": results_data,
            "meta": {
                "lot_number": self.lot_number.text(),
                "expiry_date": self.expiry_date.date().toString("yyyy-MM-dd"),
                "date_tested": self.date_tested.date().toString("yyyy-MM-dd")
            },
            "sign": {
                "employee_signature_text": self.full_name.text(),
                "employee_signature_img": employee_sig_base64,
                "ohn_signature_text": "",
                "ohn_signature_img": ohn_sig_base64
            },
            # For database searchability
            "name": self.full_name.text().split()[0] if self.full_name.text() else "",
            "surname": " ".join(self.full_name.text().split()[1:]) if len(self.full_name.text().split()) > 1 else "",
            "id_number": self.id_number.text()
        }

        # Save to database
        try:
            user_session = self.main_window.fetch_session()
            user_id = user_session.get("id") if user_session else None
            
            sub_id = local_db.save_submission("workplace_drug_testing", data, user_id=user_id)
            print(f"Saved locally with ID: {sub_id}")

            # Capture company template on first submission for this company
            company = getattr(self.main_window, 'selected_company', None) or {}
            _capture_company_template_if_first(company.get('id', ''), self.FORM_TYPE, data)

            # Trigger sync in background
            sync_thread = threading.Thread(target=db.sync_to_cloud)
            sync_thread.start()
            
            # Generate PDF
            try:
                from pages.template_generator import generate_pdf_for_form
                # Pass employee data for file organization
                emp_data = getattr(self.main_window, 'selected_employee', None)
                generate_pdf_for_form("workplace_drug_testing", data, employee_data=emp_data, status=status)
                
                status_msg = "approved" if status == "approved" else "sent for doctor approval"
                QMessageBox.information(self, "Success", f"Drug Testing Form saved successfully ({status_msg})!\nPDF generated in employee folder.")
            except Exception as pdf_error:
                print(f"PDF generation failed: {pdf_error}")
                import traceback
                traceback.print_exc()
                QMessageBox.information(self, "Success", "Drug Testing Form saved successfully!\n(PDF generation failed - check logs)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save form: {e}")
