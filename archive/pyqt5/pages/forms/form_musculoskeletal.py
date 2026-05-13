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
from Utility.autofill import build_autofill_context, apply_autofill_to_form
from Utility.template_fields import COMPANY_TEMPLATE_FIELDS, UNIVERSAL_TEMPLATE_FIELDS
from db import sync_company_templates_to_cloud
import db
import threading
import os


def _capture_company_template_if_first(company_id, form_type, data):
    if not company_id: return
    if local_db.get_company_template(company_id, form_type): return
    capturable_keys = list(set(COMPANY_TEMPLATE_FIELDS.get(form_type, []) + UNIVERSAL_TEMPLATE_FIELDS))
    def _get(d, key):
        if key in d: return d[key]
        for v in d.values():
            if isinstance(v, dict) and key in v: return v[key]
        return None
    fields_to_save = {k: {"value": _get(data, k), "label": k.replace("_", " ").title(), "is_locked": False} for k in capturable_keys if _get(data, k)}
    if fields_to_save:
        local_db.save_company_template(company_id, form_type, fields_to_save)
        threading.Thread(target=sync_company_templates_to_cloud, args=(company_id,), daemon=True).start()



def process_submission(employee_id: str, company_id: str, data: dict, status: str = "approved", employee_data: dict = None, user_id: str = None) -> dict:
    """
    UI-agnostic form processing for musculoskeletal_questionnaire.
    Returns {'success': bool, 'pdf_path': str | None, 'submission_id': str | None, 'error': str | None}
    """
    import traceback
    from pages.template_generator import generate_pdf_for_form
    try:
        sub_id = local_db.save_submission("musculoskeletal_questionnaire", data, user_id=user_id)
        _capture_company_template_if_first(company_id, "musculoskeletal_questionnaire", data)
        threading.Thread(target=db.sync_to_cloud, daemon=True).start()
        pdf_path = None
        try:
            pdf_path = generate_pdf_for_form("musculoskeletal_questionnaire", data, employee_data=employee_data, status=status)
        except Exception as pdf_err:
            print(f"[musculoskeletal] PDF generation failed: {pdf_err}")
            traceback.print_exc()
        return {"success": True, "pdf_path": pdf_path, "submission_id": sub_id, "error": None}
    except Exception as e:
        return {"success": False, "pdf_path": None, "submission_id": None, "error": str(e)}


class FormMusculoskeletal(QWidget):
    FORM_TYPE = "musculoskeletal_questionnaire"

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.fields = {}
        self.init_ui()

    def showEvent(self, event):
        """Pre-fill employee and company template data."""
        super().showEvent(event)
        employee = getattr(self.main_window, 'selected_employee', None) or {}
        company  = getattr(self.main_window, 'selected_company', None) or {}
        context  = build_autofill_context(company.get('id', ''), employee, self.FORM_TYPE)
        apply_autofill_to_form(self, context)

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
        self.full_name  = QLineEdit()
        self.id_number  = QLineEdit()
        self.occupation = QLineEdit()
        self.department = QLineEdit()
        # Register for autofill
        self.fields["full_name"]  = self.full_name
        self.fields["id_number"]  = self.id_number
        self.fields["occupation"] = self.occupation
        self.fields["job_title"]  = self.occupation  # alias

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
        grid = {}
        for body_part, symptoms in self.grid_data.items():
            grid[body_part] = {}
            for symptom, combo in symptoms.items():
                grid[body_part][symptom] = combo.currentText()

        emp_sig_path = "temp_employee_signature.png"
        ohnp_sig_path = "temp_ohnp_signature.png"
        self.employee_signature_pad.get_signature_image().save(emp_sig_path)
        self.ohnp_signature_pad.get_signature_image().save(ohnp_sig_path)
        try:
            with open(emp_sig_path, "rb") as f:
                emp_sig_base64 = base64.b64encode(f.read()).decode("utf-8")
            with open(ohnp_sig_path, "rb") as f:
                ohnp_sig_base64 = base64.b64encode(f.read()).decode("utf-8")
            if os.path.exists(emp_sig_path): os.remove(emp_sig_path)
            if os.path.exists(ohnp_sig_path): os.remove(ohnp_sig_path)
        except Exception as e:
            print(f"Error encoding signatures: {e}")
            emp_sig_base64 = ""
            ohnp_sig_base64 = ""

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
                "employee_signature": emp_sig_base64,
                "employee_signature_base64": f"data:image/png;base64,{emp_sig_base64}" if emp_sig_base64 else "",
                "employee_date": self.employee_date.date().toString("yyyy-MM-dd"),
                "ohnp_signature": ohnp_sig_base64,
                "ohnp_signature_base64": f"data:image/png;base64,{ohnp_sig_base64}" if ohnp_sig_base64 else "",
                "ohnp_date": self.ohnp_date.date().toString("yyyy-MM-dd")
            },
            "name": self.full_name.text().split()[0] if self.full_name.text() else "",
            "surname": " ".join(self.full_name.text().split()[1:]) if len(self.full_name.text().split()) > 1 else "",
            "id_number": self.id_number.text()
        }

        user_session = self.main_window.fetch_session()
        user_id = user_session.get("id") if user_session else None
        company = getattr(self.main_window, 'selected_company', None) or {}
        emp_data = getattr(self.main_window, 'selected_employee', None)

        result = process_submission(
            employee_id=emp_data.get("id", "") if emp_data else "",
            company_id=company.get("id", ""),
            data=data, status=status, employee_data=emp_data, user_id=user_id,
        )
        if result["success"]:
            status_msg = "approved" if status == "approved" else "sent for doctor approval"
            msg = f"Form saved successfully ({status_msg})!"
            msg += "\nPDF generated in employee folder." if result["pdf_path"] else "\n(PDF generation failed)"
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.critical(self, "Error", f"Failed to save form: {result['error']}")
