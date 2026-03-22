# form_confined_spaces.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QFormLayout, QScrollArea, QDateEdit, QMessageBox,
    QRadioButton, QButtonGroup, QHBoxLayout, QTextEdit
)
from PyQt5.QtCore import QDate
from pages.signiture import SignaturePad
import base64
from Utility.local_db import local_db
import db
import threading
import os


class FormConfinedSpaces(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def showEvent(self, event):
        """Pre-fill employee details if selected."""
        super().showEvent(event)
        if hasattr(self.main_window, 'selected_employee') and self.main_window.selected_employee:
            emp = self.main_window.selected_employee
            self.full_name_surname.setText(emp.get('full_name', ''))
            self.id_number.setText(emp.get('id_number', ''))
            self.company.setText(emp.get('company_name', ''))
            self.occupation.setText(emp.get('job_title', ''))

    def init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        form_layout = QFormLayout()

        # Title
        title = QLabel("Confined Spaces Questionnaire for Employees")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")
        form_layout.addRow(title)

        # Employee Details
        self.full_name_surname = QLineEdit()
        self.id_number = QLineEdit()
        self.company = QLineEdit()
        self.site_store = QLineEdit()
        self.occupation = QLineEdit()
        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())

        form_layout.addRow("Full Name & Surname:", self.full_name_surname)
        form_layout.addRow("ID Number:", self.id_number)
        form_layout.addRow("Company:", self.company)
        form_layout.addRow("Site/Store:", self.site_store)
        form_layout.addRow("Occupation:", self.occupation)
        form_layout.addRow("Date:", self.date)

        # Questions organized by section
        self.questions = {}
        
        # Section 1: Awareness
        form_layout.addRow(QLabel("<b>1. Awareness of Confined Spaces</b>"))
        section1 = [
            ("q1_confined_space_definition", "Do you know what qualifies as a confined space?"),
            ("q1_assigned_before", "Have you ever been assigned to work in a confined space?"),
            ("q1_understand_hazards", "Do you understand the potential hazards?"),
            ("q1_trained_safety_procedures", "Have you been trained in safety procedures?")
        ]
        
        for key, question in section1:
            self.questions[key] = self._create_yes_no_question(question, form_layout)

        # Section 2: Understanding Hazards
        form_layout.addRow(QLabel("<b>2. Understanding of Confined Space Hazards</b>"))
        section2 = [
            ("q2_oxygen_deficiency", "Oxygen deficiency"),
            ("q2_flammable_explosive", "Flammable or explosive atmosphere"),
            ("q2_toxic_gases", "Toxic or hazardous gases"),
            ("q2_physical_hazards", "Physical hazards (machinery, electrical)"),
            ("q2_water_flooding", "Water accumulation or flooding"),
            ("q2_temperature_extremes", "Temperature extremes"),
            ("q2_limited_egress", "Limited access or egress")
        ]
        
        for key, hazard in section2:
            self.questions[key] = self._create_yes_no_question(hazard, form_layout)

        self.q2_other_specify = QLineEdit()
        form_layout.addRow("Other hazard (specify):", self.q2_other_specify)

        # Section 3: Safety Measures
        form_layout.addRow(QLabel("<b>3. Safety Measures and Procedures</b>"))
        section3 = [
            ("q3_emergency_evac_procedures", "Familiar with emergency evacuation procedures?"),
            ("q3_entry_permit_location_sign", "Know location of entry permit?"),
            ("q3_operate_ppe", "Know how to operate PPE?"),
            ("q3_rescue_training", "Received rescue training?"),
            ("q3_procedure_if_hazard", "Know procedure if hazard encountered?")
        ]
        
        for key, question in section3:
            self.questions[key] = self._create_yes_no_question(question, form_layout)

        # Section 4: PPE and Monitoring
        form_layout.addRow(QLabel("<b>4. PPE and Monitoring</b>"))
        section4 = [
            ("q4_air_monitoring_importance", "Aware of air monitoring importance?"),
            ("q4_trained_gas_detection", "Trained to use gas detection equipment?"),
            ("q4_wear_appropriate_ppe", "Wear appropriate PPE?")
        ]
        
        for key, question in section4:
            self.questions[key] = self._create_yes_no_question(question, form_layout)

        # Section 5: Personal Health
        form_layout.addRow(QLabel("<b>5. Personal Health and Fitness</b>"))
        section5 = [
            ("q5_medical_conditions_affect", "Any medical conditions affecting ability?"),
            ("q5_health_monitoring_awareness", "Aware of health monitoring procedures?"),
            ("q5_feel_fit", "Feel physically fit for confined spaces?")
        ]
        
        for key, question in section5:
            self.questions[key] = self._create_yes_no_question(question, form_layout)

        self.q5_medical_conditions_specify = QLineEdit()
        form_layout.addRow("If yes, specify conditions:", self.q5_medical_conditions_specify)

        # Section 6: Employee Acknowledgment
        form_layout.addRow(QLabel("<b>6. Employee Acknowledgment</b>"))
        section6 = [
            ("q6_understand_risks", "Understand risks and importance of safety procedures?"),
            ("q6_comfortable_asking", "Comfortable asking for assistance?"),
            ("q6_ack_follow_procedures", "Acknowledge must follow safety procedures?")
        ]
        
        for key, question in section6:
            self.questions[key] = self._create_yes_no_question(question, form_layout)

        # Section 7: Additional Comments
        form_layout.addRow(QLabel("<b>7. Additional Comments</b>"))
        self.additional_comments = QTextEdit()
        self.additional_comments.setMaximumHeight(100)
        form_layout.addRow("Comments:", self.additional_comments)

        # Signature
        form_layout.addRow(QLabel("<b>Signature</b>"))
        self.signature_date = QDateEdit()
        self.signature_date.setDate(QDate.currentDate())
        form_layout.addRow("Date:", self.signature_date)
        
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

    def _create_yes_no_question(self, question_text, form_layout):
        """Helper to create Yes/No radio button pair"""
        group = QButtonGroup()
        yes_radio = QRadioButton("Yes")
        no_radio = QRadioButton("No")
        group.addButton(yes_radio)
        group.addButton(no_radio)
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(yes_radio)
        h_layout.addWidget(no_radio)
        h_layout.addStretch()
        
        form_layout.addRow(question_text, h_layout)
        
        return {"group": group, "yes": yes_radio, "no": no_radio}

    def submit_form(self):
        # Gather responses
        responses = {}
        for key, widgets in self.questions.items():
            if widgets["yes"].isChecked():
                responses[key] = "Yes"
            elif widgets["no"].isChecked():
                responses[key] = "No"
            else:
                responses[key] = ""

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
            "full_name_surname": self.full_name_surname.text(),
            "id_number": self.id_number.text(),
            "company": self.company.text(),
            "site_store": self.site_store.text(),
            "occupation": self.occupation.text(),
            "date": self.date.date().toString("yyyy-MM-dd"),
            **responses,
            "q2_other_specify": self.q2_other_specify.text(),
            "q5_medical_conditions_specify": self.q5_medical_conditions_specify.text(),
            "additional_comments": self.additional_comments.toPlainText(),
            "signature_date": self.signature_date.date().toString("yyyy-MM-dd"),
            "signature_data": sig_base64,
            # For database searchability
            "name": self.full_name_surname.text().split()[0] if self.full_name_surname.text() else "",
            "surname": " ".join(self.full_name_surname.text().split()[1:]) if len(self.full_name_surname.text().split()) > 1 else ""
        }

        # Save to database
        try:
            user_session = self.main_window.fetch_session()
            user_id = user_session.get("id") if user_session else None
            
            sub_id = local_db.save_submission("confined_spaces_questionnaire", data, user_id=user_id)
            print(f"Saved locally with ID: {sub_id}")
            
            sync_thread = threading.Thread(target=db.sync_to_cloud)
            sync_thread.start()
            

            # Generate PDF
            try:
                from pages.template_generator import generate_pdf_for_form
                # Pass employee data for file organization
                emp_data = getattr(self.main_window, 'selected_employee', None)
                generate_pdf_for_form("confined_spaces_questionnaire", data, employee_data=emp_data)
                
                QMessageBox.information(self, "Success", "Form saved successfully!\nPDF generated in employee folder.")
            except Exception as pdf_error:
                print(f"PDF generation failed: {pdf_error}")
                import traceback
                traceback.print_exc()
                QMessageBox.information(self, "Success", "Form saved!\n(PDF generation failed)")
           
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save form: {e}")
