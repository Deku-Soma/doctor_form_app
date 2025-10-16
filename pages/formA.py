# form_a.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
    QVBoxLayout, QFormLayout, QScrollArea, QDateEdit,QMessageBox
)
from PyQt5.QtCore import QDate
from pages.signiture import SignaturePad
from pages.template_generator import generate_html_pdf
import base64



class FormA(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
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
        submit_btn = QPushButton("Submit")
        submit_btn.clicked.connect(self.submit_form)
        form_layout.addRow(submit_btn)

        # PDF generate 
        generate_pdf_btn = QPushButton("Generate PDF")
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
        # Gather data (can be used for saving to DB or generating PDF)
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

            # Save the signature temporarily
        signature_path = "temp_signature.png"
        self.signature_pad.get_signature_image().save(signature_path)

        # Generate PDF
        generate_html_pdf(data, signature_path,'1')

        QMessageBox.information(self, "Submited", "PDF Generated !")

        
    def generate_pdf_form(self):
            print("PDF Generated")
