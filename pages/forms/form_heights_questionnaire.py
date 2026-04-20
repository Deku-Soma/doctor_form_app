# form_heights_questionnaire.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QFormLayout, QScrollArea, QDateEdit, QMessageBox,
    QRadioButton, QButtonGroup, QHBoxLayout
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



class FormHeightsQuestionnaire(QWidget):
    FORM_TYPE = "heights_questionnaire"

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
        title = QLabel("Working at Heights / General Health Questionnaire")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")
        form_layout.addRow(title)

        # Employee Details
        self.full_name_surname = QLineEdit()
        self.fields["full_name_surname"] = self.full_name_surname
        form_layout.addRow("Full Name & Surname:", self.full_name_surname)

        # Questions
        form_layout.addRow(QLabel("<b>Do you currently have or previously had:</b>"))
        
        self.questions = {}
        questions_list = [
            ("q01_neuro_epilepsy_convulsions", "1. Diagnosed with neurological conditions, epilepsy, convulsions"),
            ("q02_frequent_headaches", "2. Frequent headaches"),
            ("q03_head_injury", "3. Head injury"),
            ("q04_meds_depression_anxiety_mental", "4. On medication for depression, anxiety, mental conditions"),
            ("q05_previous_suicide_attempts", "5. Previous suicide attempts"),
            ("q06_sleep_disorders", "6. Sleep disorders or struggle to sleep at night"),
            ("q07_depression", "7. Depression"),
            ("q08_dizziness_fainting", "8. Dizziness or fainting spells"),
            ("q09_epilepsy", "9. Epilepsy"),
            ("q10_hearing_problems", "10. Hearing problems"),
            ("q11_ear_ringing_discharges_infections", "11. Problems with ears/ringing/discharges/infections"),
            ("q12_vision_eye_glasses", "12. Vision/eye problems/need glasses"),
            ("q13_heart_problems", "13. Heart problems"),
            ("q14_high_blood_pressure", "14. High blood pressure"),
            ("q15_lung_problems_asthma", "15. Lung problems/asthma"),
            ("q16_diabetes_blood_sugar", "16. Diabetes (high or low blood sugar)"),
            ("q17_taking_any_medication", "17. Taking any medication"),
            ("q18_advised_not_exercise", "18. Advised by doctor not to do exercise"),
            ("q19_kidney_problems", "19. Kidney problems"),
            ("q20_back_muscle_joint_pain", "20. Back or muscle problems/joint pains"),
            ("q21_pins_needles_numbness", "21. Feeling of needles and pins or numbness"),
            ("q22_fear_heights_small_spaces", "22. Suffer from fear of heights, small spaces"),
            ("q23_meds_dizzy_drowsy", "23. Taking medication that makes you dizzy/drowsy")
        ]

        for key, question_text in questions_list:
            group = QButtonGroup()
            yes_radio = QRadioButton("Yes")
            no_radio = QRadioButton("No")
            group.addButton(yes_radio)
            group.addButton(no_radio)
            
            self.questions[key] = {"group": group, "yes": yes_radio, "no": no_radio}
            
            h_layout = QHBoxLayout()
            h_layout.addWidget(yes_radio)
            h_layout.addWidget(no_radio)
            h_layout.addStretch()
            
            form_layout.addRow(question_text, h_layout)

        # Employee Signature
        form_layout.addRow(QLabel("<b>Employee Declaration</b>"))
        self.employee_signature_date = QDateEdit()
        self.employee_signature_date.setDate(QDate.currentDate())
        form_layout.addRow("Date:", self.employee_signature_date)
        
        self.employee_signature_pad = SignaturePad()
        form_layout.addRow("Employee Signature:", self.employee_signature_pad)
        
        clear_emp_btn = QPushButton("Clear Employee Signature")
        clear_emp_btn.clicked.connect(self.employee_signature_pad.clear)
        form_layout.addRow(clear_emp_btn)

        # Examiner Signature
        form_layout.addRow(QLabel("<b>Examiner Declaration</b>"))
        self.examiner_signature_date = QDateEdit()
        self.examiner_signature_date.setDate(QDate.currentDate())
        form_layout.addRow("Date:", self.examiner_signature_date)
        
        self.examiner_signature_pad = SignaturePad()
        form_layout.addRow("Examiner Signature:", self.examiner_signature_pad)
        
        clear_exam_btn = QPushButton("Clear Examiner Signature")
        clear_exam_btn.clicked.connect(self.examiner_signature_pad.clear)
        form_layout.addRow(clear_exam_btn)

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
        # Gather question responses
        responses = {}
        for key, widgets in self.questions.items():
            if widgets["yes"].isChecked():
                responses[key] = "Y"
            elif widgets["no"].isChecked():
                responses[key] = "N"
            else:
                responses[key] = ""

        # Save signatures
        emp_sig_path = "temp_employee_signature.png"
        exam_sig_path = "temp_examiner_signature.png"
        self.employee_signature_pad.get_signature_image().save(emp_sig_path)
        self.examiner_signature_pad.get_signature_image().save(exam_sig_path)

        # Encode signatures
        try:
            with open(emp_sig_path, "rb") as f:
                emp_sig_base64 = base64.b64encode(f.read()).decode("utf-8")
            with open(exam_sig_path, "rb") as f:
                exam_sig_base64 = base64.b64encode(f.read()).decode("utf-8")
            
            # Cleanup temp files
            if os.path.exists(emp_sig_path):
                os.remove(emp_sig_path)
            if os.path.exists(exam_sig_path):
                os.remove(exam_sig_path)

        except Exception as e:
            print(f"Error encoding signatures: {e}")
            emp_sig_base64 = ""
            exam_sig_base64 = ""

        # Prepare data
        data = {
            "full_name_surname": self.full_name_surname.text(),
            **responses,
            "employee_signature_date": self.employee_signature_date.date().toString("yyyy-MM-dd"),
            "employee_signature_data": emp_sig_base64,
            "examiner_signature_date": self.examiner_signature_date.date().toString("yyyy-MM-dd"),
            "examiner_signature_data": exam_sig_base64,
            # For database searchability
            "name": self.full_name_surname.text().split()[0] if self.full_name_surname.text() else "",
            "surname": " ".join(self.full_name_surname.text().split()[1:]) if len(self.full_name_surname.text().split()) > 1 else ""
        }

        # Save to database
        try:
            user_session = self.main_window.fetch_session()
            user_id = user_session.get("id") if user_session else None
            
            sub_id = local_db.save_submission("heights_questionnaire", data, user_id=user_id)
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
                generate_pdf_for_form("heights_questionnaire", data, employee_data=emp_data, status=status)
                
                status_msg = "approved" if status == "approved" else "sent for doctor approval"
                QMessageBox.information(self, "Success", f"Form saved successfully ({status_msg})!\nPDF generated in employee folder.")
            except Exception as pdf_error:
                print(f"PDF generation failed: {pdf_error}")
                import traceback
                traceback.print_exc()
                QMessageBox.information(self, "Success", "Form saved!\n(PDF generation failed)")
         
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save form: {e}")
