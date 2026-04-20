# form_hot_cold_exposure.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QFormLayout, QScrollArea, QDateEdit, QMessageBox,
    QCheckBox, QRadioButton, QButtonGroup, QHBoxLayout
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



class FormHotColdExposure(QWidget):
    FORM_TYPE = "hot_cold_exposure"

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
        title = QLabel("Hot/Cold Exposure Medical Surveillance Survey")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")
        form_layout.addRow(title)

        # Part A: Employee Information
        form_layout.addRow(QLabel("<b>Part A: EMPLOYEE INFORMATION</b>"))
        self.first_name = QLineEdit()
        self.last_name  = QLineEdit()
        self.id_number  = QLineEdit()
        self.telephone  = QLineEdit()
        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.job_title = QLineEdit()
        # Register for autofill
        self.fields["first_name"] = self.first_name
        self.fields["surname"]    = self.last_name
        self.fields["id_number"]  = self.id_number
        self.fields["job_title"]  = self.job_title

        form_layout.addRow("First Name:", self.first_name)
        form_layout.addRow("Last Name:", self.last_name)
        form_layout.addRow("ID Number:", self.id_number)
        form_layout.addRow("Telephone:", self.telephone)
        form_layout.addRow("Date:", self.date)
        form_layout.addRow("Job Title:", self.job_title)

        # Part B: Conditions
        form_layout.addRow(QLabel("<b>Part B: CONDITIONS PERTAINING TO HEAT OR COLD STRESS</b>"))
        self.partB = {}
        partB_conditions = [
            ("humidity_over_30c", "Indoor/Outdoor Humidity > 30°C"),
            ("hot_indoor_over_30min", "Continuous work >30 min in hot indoor areas"),
            ("cold_below_minus15_or_windchill_minus25", "Continuous work >30 min in temp <-15°C or windchill <-25°C")
        ]
        
        for key, label in partB_conditions:
            checkbox = QCheckBox(label)
            self.partB[key] = checkbox
            form_layout.addRow(checkbox)

        self.partB_other_text = QLineEdit()
        form_layout.addRow("Other:", self.partB_other_text)

        # Part C: Worker Health Conditions
        form_layout.addRow(QLabel("<b>Part C: WORKER HEALTH CONDITIONS</b>"))
        
        # Hot Environment
        form_layout.addRow(QLabel("<b>Hot Environment - Do you have any of these conditions?</b>"))
        self.hot_group = QButtonGroup()
        hot_yes = QRadioButton("Yes")
        hot_no = QRadioButton("No")
        self.hot_group.addButton(hot_yes)
        self.hot_group.addButton(hot_no)
        self.partC_hot = {"yes": hot_yes, "no": hot_no}
        
        h_layout1 = QHBoxLayout()
        h_layout1.addWidget(hot_yes)
        h_layout1.addWidget(hot_no)
        h_layout1.addStretch()
        form_layout.addRow(h_layout1)

        hot_conditions = QLabel(
            "Shortness of breath, Breathing difficulties, Chronic Bronchitis, Emphysema, "
            "Lung Disease, Severe Allergies, Heart Problems, Chest pain on exertion, "
            "Cardiovascular disease, Diabetes, Fainting spells, Seizures, Asthma, "
            "Pacemaker, Skin conditions, Peripheral Vascular Disease, Anhidrosis"
        )
        hot_conditions.setWordWrap(True)
        hot_conditions.setStyleSheet("font-size: 11px; color: #555; margin: 5px 0;")
        form_layout.addRow(hot_conditions)

        # Cold Environment
        form_layout.addRow(QLabel("<b>Cold Environment - Do you have any of these conditions?</b>"))
        self.cold_group = QButtonGroup()
        cold_yes = QRadioButton("Yes")
        cold_no = QRadioButton("No")
        self.cold_group.addButton(cold_yes)
        self.cold_group.addButton(cold_no)
        self.partC_cold = {"yes": cold_yes, "no": cold_no}
        
        h_layout2 = QHBoxLayout()
        h_layout2.addWidget(cold_yes)
        h_layout2.addWidget(cold_no)
        h_layout2.addStretch()
        form_layout.addRow(h_layout2)

        cold_conditions = QLabel(
            "Shortness of breath, Breathing difficulties, Chronic Bronchitis, Emphysema, "
            "Lung Disease, Heart Problems, Chest pain on exertion, Hypertension, Diabetes, "
            "Fainting spells, Seizures, Panic attacks, Asthma, Pacemaker, COPD, "
            "Cystic Fibrosis, Cold Agglutinins Disease, Raynaud's Disease, "
            "Rheumatic Disease (SLE, RA, SA)"
        )
        cold_conditions.setWordWrap(True)
        cold_conditions.setStyleSheet("font-size: 11px; color: #555; margin: 5px 0;")
        form_layout.addRow(cold_conditions)

        # Other Conditions
        form_layout.addRow(QLabel("<b>Other conditions affecting ability to work in hot/cold environments?</b>"))
        self.other_group = QButtonGroup()
        other_yes = QRadioButton("Yes")
        other_no = QRadioButton("No")
        self.other_group.addButton(other_yes)
        self.other_group.addButton(other_no)
        self.partC_other = {"yes": other_yes, "no": other_no}
        
        h_layout3 = QHBoxLayout()
        h_layout3.addWidget(other_yes)
        h_layout3.addWidget(other_no)
        h_layout3.addStretch()
        form_layout.addRow(h_layout3)

        self.other_conditions_text = QLineEdit()
        form_layout.addRow("Specify:", self.other_conditions_text)

        # Signature
        form_layout.addRow(QLabel("<b>Employee Signature</b>"))
        self.signature_date = QDateEdit()
        self.signature_date.setDate(QDate.currentDate())
        form_layout.addRow("Date:", self.signature_date)
        
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
        # Gather Part B data
        partB_data = {}
        for key, checkbox in self.partB.items():
            partB_data[key] = checkbox.isChecked()
        partB_data["other_text"] = self.partB_other_text.text()

        # Gather Part C data
        partC_data = {
            "hot_any_conditions": "Yes" if self.partC_hot["yes"].isChecked() else "No" if self.partC_hot["no"].isChecked() else "",
            "cold_any_conditions": "Yes" if self.partC_cold["yes"].isChecked() else "No" if self.partC_cold["no"].isChecked() else "",
            "other_conditions_yes": "Yes" if self.partC_other["yes"].isChecked() else "No" if self.partC_other["no"].isChecked() else "",
            "other_conditions_text": self.other_conditions_text.text()
        }

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
            "employee": {
                "first_name": self.first_name.text(),
                "last_name": self.last_name.text(),
                "id_number": self.id_number.text(),
                "telephone": self.telephone.text(),
                "date": self.date.date().toString("yyyy-MM-dd"),
                "job_title": self.job_title.text()
            },
            "partB": partB_data,
            "partC": partC_data,
            "sign": {
                "employee_signature_date": self.signature_date.date().toString("yyyy-MM-dd"),
                "employee_signature_data": sig_base64
            },
            # For database searchability
            "name": self.first_name.text(),
            "surname": self.last_name.text(),
            "id_number": self.id_number.text()
        }

        # Save to database
        try:
            user_session = self.main_window.fetch_session()
            user_id = user_session.get("id") if user_session else None
            
            sub_id = local_db.save_submission("hot_cold_exposure", data, user_id=user_id)
            print(f"Saved locally with ID: {sub_id}")

            company = getattr(self.main_window, 'selected_company', None) or {}
            _capture_company_template_if_first(company.get('id', ''), self.FORM_TYPE, data)

            sync_thread = threading.Thread(target=db.sync_to_cloud)
            sync_thread.start()
            

            # Generate PDF
            try:
                from pages.template_generator import generate_pdf_for_form
                # Pass employee data for file organization
                emp_data = getattr(self.main_window, 'selected_employee', None)
                generate_pdf_for_form("hot_cold_exposure", data, employee_data=emp_data, status=status)
                
                status_msg = "approved" if status == "approved" else "sent for doctor approval"
                QMessageBox.information(self, "Success", f"Form saved successfully ({status_msg})!\nPDF generated in employee folder.")
            except Exception as pdf_error:
                print(f"PDF generation failed: {pdf_error}")
                import traceback
                traceback.print_exc()
                QMessageBox.information(self, "Success", "Form saved!\n(PDF generation failed)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save form: {e}")
