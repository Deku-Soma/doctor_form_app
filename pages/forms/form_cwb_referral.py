# form_cwb_referral.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QFormLayout, QScrollArea, QDateEdit, QMessageBox, QTextEdit
)
from PyQt5.QtCore import QDate
from pages.signiture import SignaturePad
import base64
from Utility.local_db import local_db
import db
import threading
import os


class FormCWBReferral(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def showEvent(self, event):
        """Pre-fill employee details if selected."""
        super().showEvent(event)
        if hasattr(self.main_window, 'selected_employee') and self.main_window.selected_employee:
            emp = self.main_window.selected_employee
            self.name.setText(emp.get('full_name', '').split()[0])
            self.surname.setText(" ".join(emp.get('full_name', '').split()[1:]))
            self.id_number.setText(emp.get('id_number', ''))
            self.employer.setText(emp.get('company_name', ''))
            self.job_title.setText(emp.get('job_title', ''))

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
        self.name = QLineEdit()
        self.surname = QLineEdit()
        self.id_number = QLineEdit()
        self.job_title = QLineEdit()
        self.employer = QLineEdit()
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

        # Buttons
        submit_btn = QPushButton("Submit & Save")
        submit_btn.clicked.connect(self.submit_form)
        form_layout.addRow(submit_btn)

        back_btn = QPushButton("Back to Home")
        back_btn.clicked.connect(lambda: self.main_window.go_to_home())
        form_layout.addRow(back_btn)

        container.setLayout(form_layout)
        scroll.setWidget(container)
        layout = QVBoxLayout()
        layout.addWidget(scroll)
        self.setLayout(layout)

    def submit_form(self):
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
            
            sync_thread = threading.Thread(target=db.sync_to_cloud)
            sync_thread.start()
            
            # Generate PDF
            try:
                from pages.template_generator import generate_pdf_for_form
                # Pass employee data for file organization
                emp_data = getattr(self.main_window, 'selected_employee', None)
                generate_pdf_for_form("cwb_medical_referral", data, employee_data=emp_data)
                
                QMessageBox.information(self, "Success", "CWB Medical Referral saved successfully!\nPDF generated in employee folder.")
            except Exception as pdf_error:
                print(f"PDF generation failed: {pdf_error}")
                import traceback
                traceback.print_exc()
                QMessageBox.information(self, "Success", "CWB Medical Referral saved successfully!\n(PDF generation failed - check logs)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save form: {e}")
