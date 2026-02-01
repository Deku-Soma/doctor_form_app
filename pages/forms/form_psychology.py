# form_psychology.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QFormLayout, QScrollArea, QDateEdit, QMessageBox,
    QRadioButton, QButtonGroup, QHBoxLayout
)
from PyQt5.QtCore import QDate
from pages.signiture import SignaturePad
import base64
from Utility.local_db import local_db
import db
import threading


class FormPsychology(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def showEvent(self, event):
        """Pre-fill employee details if selected."""
        super().showEvent(event)
        if hasattr(self.main_window, 'selected_employee') and self.main_window.selected_employee:
            emp = self.main_window.selected_employee
            self.full_name.setText(emp.get('full_name', ''))
            self.id_number.setText(emp.get('id_number', ''))
            self.occupation.setText(emp.get('job_title', ''))
            self.department.setText(emp.get('department', ''))

    def init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        form_layout = QFormLayout()

        # Title
        title = QLabel("Psychosocial Questionnaire (Kessler K10)")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")
        form_layout.addRow(title)

        # Employee Details
        self.full_name = QLineEdit()
        self.id_number = QLineEdit()
        self.occupation = QLineEdit()
        self.department = QLineEdit()

        form_layout.addRow("Name and Surname:", self.full_name)
        form_layout.addRow("ID Number:", self.id_number)
        form_layout.addRow("Occupation:", self.occupation)
        form_layout.addRow("Department:", self.department)

        # K10 Questions
        form_layout.addRow(QLabel("<b>In the past 4 weeks, how often did you feel:</b>"))
        form_layout.addRow(QLabel("<i>1=None of the time, 2=Little, 3=Some, 4=Most, 5=All the time</i>"))

        self.responses = {}
        questions = [
            ("q1", "1. Tired out for no good reason?"),
            ("q2", "2. Nervous?"),
            ("q3", "3. So nervous that nothing could calm you down?"),
            ("q4", "4. Hopeless?"),
            ("q5", "5. Restless or fidgety?"),
            ("q6", "6. So restless you could not sit still?"),
            ("q7", "7. Depressed?"),
            ("q8", "8. That everything was an effort?"),
            ("q9", "9. So sad that nothing could cheer you up?"),
            ("q10", "10. Worthless?")
        ]

        for key, question in questions:
            group = QButtonGroup()
            h_layout = QHBoxLayout()
            
            for value in ["1", "2", "3", "4", "5"]:
                radio = QRadioButton(value)
                group.addButton(radio)
                h_layout.addWidget(radio)
                if value == "1":
                    self.responses[key] = {"group": group, "1": radio}
                else:
                    self.responses[key][value] = radio
            
            h_layout.addStretch()
            form_layout.addRow(question, h_layout)

        # Score display (calculated)
        self.score_label = QLabel("Score will be calculated automatically")
        self.score_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        form_layout.addRow("Total Score:", self.score_label)

        # Employee Signature
        form_layout.addRow(QLabel("<b>Employee Signature</b>"))
        self.employee_date = QDateEdit()
        self.employee_date.setDate(QDate.currentDate())
        form_layout.addRow("Date:", self.employee_date)
        
        self.employee_signature_pad = SignaturePad()
        form_layout.addRow("Signature:", self.employee_signature_pad)
        
        clear_emp_btn = QPushButton("Clear Employee Signature")
        clear_emp_btn.clicked.connect(self.employee_signature_pad.clear)
        form_layout.addRow(clear_emp_btn)

        # OHNP Signature
        form_layout.addRow(QLabel("<b>OHNP Signature</b>"))
        self.ohnp_date = QDateEdit()
        self.ohnp_date.setDate(QDate.currentDate())
        form_layout.addRow("Date:", self.ohnp_date)
        
        self.ohnp_signature_pad = SignaturePad()
        form_layout.addRow("Signature:", self.ohnp_signature_pad)
        
        clear_ohnp_btn = QPushButton("Clear OHNP Signature")
        clear_ohnp_btn.clicked.connect(self.ohnp_signature_pad.clear)
        form_layout.addRow(clear_ohnp_btn)

        # Info
        info = QLabel(
            "<i>Scoring: <10-19=Well, 20-24=Mild, 25-29=Moderate, 30+=Severe</i>"
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; font-size: 11px;")
        form_layout.addRow(info)

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
        # Gather responses and calculate score
        responses_data = {}
        score = 0
        for key, widgets in self.responses.items():
            for value in ["1", "2", "3", "4", "5"]:
                if widgets[value].isChecked():
                    responses_data[key] = value
                    score += int(value)
                    break
            if key not in responses_data:
                responses_data[key] = ""

        # Save signatures
        emp_sig_path = "temp_employee_signature.png"
        ohnp_sig_path = "temp_ohnp_signature.png"
        self.employee_signature_pad.get_signature_image().save(emp_sig_path)
        self.ohnp_signature_pad.get_signature_image().save(ohnp_sig_path)

        try:
            with open(emp_sig_path, "rb") as f:
                emp_sig_base64 = base64.b64encode(f.read()).decode("utf-8")
            with open(ohnp_sig_path, "rb") as f:
                ohnp_sig_base64 = base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            print(f"Error encoding signatures: {e}")
            emp_sig_base64 = ""
            ohnp_sig_base64 = ""

        # Prepare data
        data = {
            "employee": {
                "full_name": self.full_name.text(),
                "id_number": self.id_number.text(),
                "occupation": self.occupation.text(),
                "department": self.department.text()
            },
            "responses": responses_data,
            "score": score,
            "score": score,
            "sign": {
                # Template expects _base64 suffix and full Data URI
                "employee_signature": emp_sig_base64,
                "employee_signature_base64": f"data:image/png;base64,{emp_sig_base64}" if emp_sig_base64 else "",
                "employee_date": self.employee_date.date().toString("yyyy-MM-dd"),
                "ohnp_signature": ohnp_sig_base64,
                "ohnp_signature_base64": f"data:image/png;base64,{ohnp_sig_base64}" if ohnp_sig_base64 else "",
                "ohnp_date": self.ohnp_date.date().toString("yyyy-MM-dd")
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
            
            sub_id = local_db.save_submission("psychology_questionnaire", data, user_id=user_id)
            print(f"Saved locally with ID: {sub_id}")
            
            sync_thread = threading.Thread(target=db.sync_to_cloud)
            sync_thread.start()
            

            # Generate PDF
            try:
                from pages.template_generator import generate_pdf_for_form
                # Pass employee data for file organization
                emp_data = getattr(self.main_window, 'selected_employee', None)
                generate_pdf_for_form("psychology_questionnaire", data, employee_data=emp_data)
                
                QMessageBox.information(self, "Success", "Form saved successfully!\nPDF generated in employee folder.")
            except Exception as pdf_error:
                print(f"PDF generation failed: {pdf_error}")
                import traceback
                traceback.print_exc()
                QMessageBox.information(self, "Success", "Form saved!\n(PDF generation failed)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save form: {e}")
