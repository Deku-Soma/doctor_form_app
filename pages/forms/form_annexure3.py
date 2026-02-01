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
import db
import threading


class FormAnnexure3(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def showEvent(self, event):
        """Pre-fill employee details if selected."""
        super().showEvent(event)
        if hasattr(self.main_window, 'selected_employee') and self.main_window.selected_employee:
            emp = self.main_window.selected_employee
            self.company.setText(emp.get('company_name', ''))
            self.employee_name.setText(emp.get('full_name', ''))
            self.id_pp_number.setText(emp.get('id_number', ''))
            self.occupation.setText(emp.get('job_title', ''))

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
        self.company = QLineEdit()
        self.employee_name = QLineEdit()
        self.id_pp_number = QLineEdit()
        self.co_number = QLineEdit()

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
        self.practitioner_name = QLineEdit()
        self.practice_number = QLineEdit()
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
            
            sync_thread = threading.Thread(target=db.sync_to_cloud)
            sync_thread.start()
            
            # Generate PDF
            try:
                from pages.template_generator import generate_pdf_for_form
                # Pass employee data for file organization
                emp_data = getattr(self.main_window, 'selected_employee', None)
                generate_pdf_for_form("annexure3_cwb", data, employee_data=emp_data)
                
                QMessageBox.information(self, "Success", "Annexure 3 saved successfully!\nPDF generated in employee folder.")
            except Exception as pdf_error:
                print(f"PDF generation failed: {pdf_error}")
                import traceback
                traceback.print_exc()
                QMessageBox.information(self, "Success", "Annexure 3 saved successfully!\n(PDF generation failed - check logs)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save form: {e}")
