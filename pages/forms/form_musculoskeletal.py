# form_musculoskeletal.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QFormLayout, QScrollArea, QDateEdit, QMessageBox,
    QComboBox, QTextEdit, QGridLayout, QHBoxLayout
)
from PyQt5.QtCore import QDate
from pages.signiture import SignaturePad
import base64
from Utility.local_db import local_db
import db
import threading
import os


class FormMusculoskeletal(QWidget):
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
        title = QLabel("Musculoskeletal Questionnaire")
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

        # Symptom Grid
        form_layout.addRow(QLabel("<b>Have you had trouble in the last 12 months with:</b>"))
        form_layout.addRow(QLabel("<i>Mark Yes/No for each body part and symptom</i>"))

        # Create grid for symptoms
        self.grid_data = {}
        body_parts = [
            "Neck", "Shoulder", "Upper body", "Elbows", "Wrist/hands",
            "Lower body", "Hips/thighs", "Knees", "Ankles", "Feet"
        ]
        symptoms = ["Pain", "Aches", "Discomfort", "Numbness", "Stiffness", "Swelling"]

        grid_widget = QWidget()
        grid_layout = QGridLayout()
        
        # Headers
        grid_layout.addWidget(QLabel("<b>Body Part</b>"), 0, 0)
        for col, symptom in enumerate(symptoms, 1):
            grid_layout.addWidget(QLabel(f"<b>{symptom}</b>"), 0, col)

        # Rows for each body part
        for row, body_part in enumerate(body_parts, 1):
            grid_layout.addWidget(QLabel(body_part), row, 0)
            self.grid_data[body_part.lower().replace("/", "_").replace(" ", "_")] = {}
            
            for col, symptom in enumerate(symptoms, 1):
                combo = QComboBox()
                combo.addItems(["", "Yes", "No"])
                combo.setMaximumWidth(80)
                grid_layout.addWidget(combo, row, col)
                self.grid_data[body_part.lower().replace("/", "_").replace(" ", "_")][symptom.lower()] = combo

        grid_widget.setLayout(grid_layout)
        form_layout.addRow(grid_widget)

        # Comments
        form_layout.addRow(QLabel("<b>Comments:</b>"))
        self.comments = QTextEdit()
        self.comments.setMaximumHeight(100)
        form_layout.addRow(self.comments)

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
        # Gather grid data
        grid = {}
        for body_part, symptoms in self.grid_data.items():
            grid[body_part] = {}
            for symptom, combo in symptoms.items():
                grid[body_part][symptom] = combo.currentText()

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
            
            # Cleanup temp files
            if os.path.exists(emp_sig_path):
                os.remove(emp_sig_path)
            if os.path.exists(ohnp_sig_path):
                os.remove(ohnp_sig_path)

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
            "grid": grid,
            "comments": self.comments.toPlainText(),
            "sign": {
                # Template expects _base64 suffix and full Data URI for nested items
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
            
            sub_id = local_db.save_submission("musculoskeletal_questionnaire", data, user_id=user_id)
            print(f"Saved locally with ID: {sub_id}")
            
            sync_thread = threading.Thread(target=db.sync_to_cloud)
            sync_thread.start()
            

            # Generate PDF
            try:
                from pages.template_generator import generate_pdf_for_form
                # Pass employee data for file organization
                emp_data = getattr(self.main_window, 'selected_employee', None)
                generate_pdf_for_form("musculoskeletal_questionnaire", data, employee_data=emp_data, status=status)
                
                status_msg = "approved" if status == "approved" else "sent for doctor approval"
                QMessageBox.information(self, "Success", f"Form saved successfully ({status_msg})!\nPDF generated in employee folder.")
            except Exception as pdf_error:
                print(f"PDF generation failed: {pdf_error}")
                import traceback
                traceback.print_exc()
                QMessageBox.information(self, "Success", "Form saved!\n(PDF generation failed)")
           
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save form: {e}")
