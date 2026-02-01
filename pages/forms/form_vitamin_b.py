# form_vitamin_b.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QFormLayout, QScrollArea, QDateEdit, QMessageBox, QTextEdit
)
from PyQt5.QtCore import QDate
from pages.signiture import SignaturePad
from pages.template_generator import generate_html_pdf
import base64
from Utility.local_db import local_db
import db
import threading


class FormVitaminB(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def showEvent(self, event):
        """Pre-fill employee details if selected."""
        super().showEvent(event)
        if hasattr(self.main_window, 'selected_employee') and self.main_window.selected_employee:
            emp = self.main_window.selected_employee
            self.name_surname.setText(emp.get('full_name', ''))
            self.id_number.setText(emp.get('id_number', ''))
            self.company.setText(emp.get('company_name', ''))

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
        self.id_number = QLineEdit()

        form_layout.addRow("Name & Surname:", self.name_surname)
        form_layout.addRow("ID Number:", self.id_number)

        # Signature
        form_layout.addRow(QLabel("<b>Signature</b>"))
        self.signature_pad = SignaturePad()
        form_layout.addRow("Digital Signature:", self.signature_pad)
        
        clear_sig_btn = QPushButton("Clear Signature")
        clear_sig_btn.clicked.connect(self.signature_pad.clear)
        form_layout.addRow(clear_sig_btn)

        # Submit Button
        submit_btn = QPushButton("Submit & Save")
        submit_btn.clicked.connect(self.submit_form)
        form_layout.addRow(submit_btn)

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

    def submit_form(self):
        # Save signature
        signature_path = "temp_signature.png"
        self.signature_pad.get_signature_image().save(signature_path)
        
        # Encode signature to base64
        try:
            with open(signature_path, "rb") as f:
                signature_base64 = base64.b64encode(f.read()).decode("utf-8")
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
            
            # Trigger sync in background
            sync_thread = threading.Thread(target=db.sync_to_cloud)
            sync_thread.start()
            
            # Generate PDF
            pdf_success = False
            try:
                from pages.template_generator import generate_pdf_for_form
                # Pass employee data for file organization
                emp_data = getattr(self.main_window, 'selected_employee', None)
                generate_pdf_for_form("vitamin_b_consent", data, employee_data=emp_data)
                
                pdf_success = True
                QMessageBox.information(self, "Success", "Vitamin B Consent saved successfully!\nPDF generated in employee folder.")
            except Exception as pdf_error:
                print(f"PDF generation failed: {pdf_error}")
                QMessageBox.information(self, "Success", "Vitamin B Consent saved successfully!\n(PDF generation failed - check logs)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save form: {e}")
