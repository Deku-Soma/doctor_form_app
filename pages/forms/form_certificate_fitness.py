# form_certificate_fitness.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
    QVBoxLayout, QFormLayout, QScrollArea, QDateEdit, QMessageBox,
    QCheckBox, QRadioButton, QButtonGroup, QGroupBox
)
from PyQt5.QtCore import QDate
from pages.signiture import SignaturePad
from pages.template_generator import generate_html_pdf
import base64
from Utility.local_db import local_db
import db
import threading


class FormCertificateFitness(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def showEvent(self, event):
        """Pre-fill employee details if selected."""
        super().showEvent(event)
        if hasattr(self.main_window, 'selected_employee') and self.main_window.selected_employee:
            emp = self.main_window.selected_employee
            self.first_name.setText(emp.get('full_name', '').split()[0])
            self.surname.setText(" ".join(emp.get('full_name', '').split()[1:]))
            self.id_pp_number.setText(emp.get('id_number', ''))
            self.company.setText(emp.get('company_name', ''))
            self.occupation.setText(emp.get('job_title', ''))

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
        # Gather medical type data
        medical_type_data = {}
        for key, checkbox in self.medical_type.items():
            medical_type_data[key] = "1" if checkbox.isChecked() else ""

        # Get selected outcome
        outcome = ""
        for outcome_text, radio in self.outcome_buttons.items():
            if radio.isChecked():
                outcome = outcome_text
                break

        # Gather tests data
        tests_data = {}
        for key, checkbox in self.tests.items():
            tests_data[key] = "1" if checkbox.isChecked() else ""

        # Gather questionnaires data
        questionnaires_data = {}
        for key, checkbox in self.questionnaires.items():
            questionnaires_data[key] = "1" if checkbox.isChecked() else ""

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
            # For database searchability
            "name": self.first_name.text(),
            "id_number": self.id_pp_number.text()
        }

        # Save to database
        try:
            user_session = self.main_window.fetch_session()
            user_id = user_session.get("id") if user_session else None
            
            sub_id = local_db.save_submission("certificate_of_fitness", data, user_id=user_id)
            print(f"Saved locally with ID: {sub_id}")
            
            # Trigger sync in background
            sync_thread = threading.Thread(target=db.sync_to_cloud)
            sync_thread.start()
            

            # Generate PDF
            try:
                from pages.template_generator import generate_pdf_for_form
                # Pass employee data for file organization
                emp_data = getattr(self.main_window, 'selected_employee', None)
                generate_pdf_for_form("certificate_of_fitness", data, employee_data=emp_data)
                
                QMessageBox.information(self, "Success", "Form saved successfully!\nPDF generated in employee folder.")
            except Exception as pdf_error:
                print(f"PDF generation failed: {pdf_error}")
                import traceback
                traceback.print_exc()
                QMessageBox.information(self, "Success", "Form saved!\n(PDF generation failed)")
                            
            # TODO: Generate PDF when template is ready
            # generate_html_pdf(data, signature_path, 'certificate_fitness')
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save form: {e}")
