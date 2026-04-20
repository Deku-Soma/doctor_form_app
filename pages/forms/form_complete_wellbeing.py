# form_complete_wellbeing.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QFormLayout, QScrollArea, QDateEdit, QMessageBox, QTextEdit, QHBoxLayout
)
from PyQt5.QtCore import QDate
from pages.signiture import SignaturePad
import base64
from Utility.local_db import local_db
import db
import threading
import os


class FormCompleteWellbeing(QWidget):
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
        title = QLabel("Complete Wellbeing - Medical Test Results")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")
        form_layout.addRow(title)

        # Patient Details
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

        # Test Results
        form_layout.addRow(QLabel("<b>Tests Conducted</b>"))
        self.glucose = QLineEdit()
        self.cholesterol = QLineEdit()
        self.blood_pressure = QLineEdit()
        self.weight = QLineEdit()
        self.height = QLineEdit()
        self.audiometry = QLineEdit()
        self.urine_analysis = QLineEdit()
        self.lung_function = QLineEdit()
        self.vision = QLineEdit()
        self.working_at_heights = QLineEdit()
        self.environment_questionnaire = QLineEdit()
        self.psychosocial_questionnaire = QLineEdit()
        self.musculoskeletal_questionnaire = QLineEdit()

        form_layout.addRow("Glucose:", self.glucose)
        form_layout.addRow("Cholesterol:", self.cholesterol)
        form_layout.addRow("Blood Pressure:", self.blood_pressure)
        form_layout.addRow("Weight:", self.weight)
        form_layout.addRow("Height:", self.height)
        form_layout.addRow("Audiometry:", self.audiometry)
        form_layout.addRow("Urine Analysis:", self.urine_analysis)
        form_layout.addRow("Lung Function:", self.lung_function)
        form_layout.addRow("Vision:", self.vision)
        form_layout.addRow("Working at Heights:", self.working_at_heights)
        form_layout.addRow("Hot/Cold Environments:", self.environment_questionnaire)
        form_layout.addRow("Psycho-social:", self.psychosocial_questionnaire)
        form_layout.addRow("Musculoskeletal:", self.musculoskeletal_questionnaire)

        # Comments
        form_layout.addRow(QLabel("<b>Comments/Notes</b>"))
        self.comments = QTextEdit()
        self.comments.setMaximumHeight(80)
        form_layout.addRow(self.comments)

        # Employee Signature
        form_layout.addRow(QLabel("<b>Employee Signature</b>"))
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
            "employer": self.employer.text(),
            "job_title": self.job_title.text(),
            "exam_date": self.exam_date.date().toString("yyyy-MM-dd"),
            "glucose": self.glucose.text(),
            "cholesterol": self.cholesterol.text(),
            "blood_pressure": self.blood_pressure.text(),
            "weight": self.weight.text(),
            "height": self.height.text(),
            "audiometry": self.audiometry.text(),
            "urine_analysis": self.urine_analysis.text(),
            "lung_function": self.lung_function.text(),
            "vision": self.vision.text(),
            "working_at_heights": self.working_at_heights.text(),
            "environment_questionnaire": self.environment_questionnaire.text(),
            "psychosocial_questionnaire": self.psychosocial_questionnaire.text(),
            "musculoskeletal_questionnaire": self.musculoskeletal_questionnaire.text(),
            "comments": self.comments.toPlainText(),
            "signature_base64": sig_base64
        }

        # Save to database
        try:
            user_session = self.main_window.fetch_session()
            user_id = user_session.get("id") if user_session else None
            
            sub_id = local_db.save_submission("complete_wellbeing", data, user_id=user_id)
            print(f"Saved locally with ID: {sub_id}")
            
            sync_thread = threading.Thread(target=db.sync_to_cloud)
            sync_thread.start()
            
            # Generate PDF
            try:
                from pages.template_generator import generate_pdf_for_form
                # Pass employee data for file organization
                emp_data = getattr(self.main_window, 'selected_employee', None)
                generate_pdf_for_form("complete_wellbeing", data, employee_data=emp_data, status=status)
                
                status_msg = "approved" if status == "approved" else "sent for doctor approval"
                QMessageBox.information(self, "Success", f"Complete Wellbeing form saved successfully ({status_msg})!\nPDF generated in employee folder.")
            except Exception as pdf_error:
                print(f"PDF generation failed: {pdf_error}")
                QMessageBox.information(self, "Success", "Complete Wellbeing form saved successfully!\n(PDF generation failed - check logs)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save form: {e}")
