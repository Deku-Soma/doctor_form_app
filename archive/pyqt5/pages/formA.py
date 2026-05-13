# form_a.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
    QVBoxLayout, QFormLayout, QScrollArea, QDateEdit,QMessageBox
)
from PyQt5.QtCore import QDate
from pages.signiture import SignaturePad
from pages.template_generator import generate_html_pdf
import base64



    # ... (Keep imports, but add local_db and db)
from Utility.local_db import local_db
import db
import threading

class FormA(QWidget):
    # ... (init and setup remains same)
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        # ... (Same UI code)
        # Scroll area in case form is long
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        form_layout = QFormLayout()

        # Basic details
        self.name = QLineEdit()
        self.surname = QLineEdit()
        self.id_number = QLineEdit()
        self.employer = QLineEdit()
        self.job_title = QLineEdit()
        self.exam_date = QDateEdit()
        self.exam_date.setDate(QDate.currentDate())

        form_layout.addRow("Name:", self.name)
        form_layout.addRow("Surname:", self.surname)
        form_layout.addRow("ID Number:", self.id_number)
        form_layout.addRow("Employer:", self.employer)
        form_layout.addRow("Job Title:", self.job_title)
        form_layout.addRow("Examination Date:", self.exam_date)

        # Medical tests
        self.tests = {}
        test_fields = [
            "Glucose", "Cholesterol", "Blood Pressure", "Weight", "Height",
            "Audiometry", "Urine Analysis", "Lung Function", "Vision",
            "Working at heights", "Hot/Cold Environments Questionnaire",
            "Psycho-social Questionnaire", "Musculoskeletal Questionnaire"
        ]

        for test in test_fields:
            self.tests[test] = QLineEdit()
            form_layout.addRow(f"{test}:", self.tests[test])

        # Comments
        self.comments = QTextEdit()
        form_layout.addRow("Comments / Notes:", self.comments)
                # Inside init_ui() in FormA
        self.signature_pad = SignaturePad()
        form_layout.addRow("Digital Signature:", self.signature_pad)

        # Optional: add a clear button
        clear_sig_btn = QPushButton("Clear Signature")
        clear_sig_btn.clicked.connect(self.signature_pad.clear)
        form_layout.addRow(clear_sig_btn)

        # Submit
        submit_btn = QPushButton("Submit & Save")
        submit_btn.clicked.connect(self.submit_form)
        form_layout.addRow(submit_btn)

        # PDF generate 
        generate_pdf_btn = QPushButton("Generate PDF Only")
        generate_pdf_btn.clicked.connect(self.generate_pdf_form)
        form_layout.addRow(generate_pdf_btn)

        #home buttons 
        back_to_home_btn = QPushButton("Back")
        back_to_home_btn.clicked.connect(lambda: self.main_window.go_to_home())
        form_layout.addRow(back_to_home_btn)

        # Wrap layout
        container.setLayout(form_layout)
        scroll.setWidget(container)
        layout = QVBoxLayout()
        layout.addWidget(scroll)
        self.setLayout(layout)

    def submit_form(self):
        # Gather data 
        data = {
            "name": self.name.text(),
            "surname": self.surname.text(),
            "id_number": self.id_number.text(),
            "employer": self.employer.text(),
            "job_title": self.job_title.text(),
            "exam_date": self.exam_date.date().toString("yyyy-MM-dd"),
            "comments": self.comments.toPlainText()
        }
        for test, widget in self.tests.items():
            data[test] = widget.text()

        # Handle Signature
        signature_path = "temp_signature.png"
        self.signature_pad.get_signature_image().save(signature_path)
        
        # Encode signature to base64
        try:
            with open(signature_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                data["signature_base64"] = encoded_string
        except Exception as e:
            print(f"Error encoding signature: {e}")

        # 1. Save Locally
        try:
            # Get user from session if available? For now pass None or fetch from main_window if stored
            # Assuming main_window has session data (we saw fetch_session in main.py)
            user_session = self.main_window.fetch_session()
            user_id = user_session.get("id") if user_session else None
            
            sub_id = local_db.save_submission("medical_assessment_a", data, user_id=user_id)
            print(f"Saved locally with ID: {sub_id}")
            
            # 2. Trigger Sync in Background
            sync_thread = threading.Thread(target=db.sync_to_cloud)
            sync_thread.start()
            
            QMessageBox.information(self, "Success", "Form saved locally! Syncing in background...")
            
            # 3. Generate PDF (Optional req? Keeping it as per original flow)
            generate_html_pdf(data, signature_path, '1')
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save form: {e}")


    def generate_pdf_form(self):
        # ... logic to just gen PDF
        self.submit_form() # Reuse submit for now or separate if needed

