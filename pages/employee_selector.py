# employee_selector.py
"""
Employee Selector Dialog - Select company and employee before opening a form.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from Utility.local_db import local_db


class EmployeeSelectorDialog(QDialog):
    """
    Dialog for selecting a company and employee before opening a form.
    Returns the selected employee data on success.
    """
    def __init__(self, parent=None, form_title=""):
        super().__init__(parent)
        self.selected_employee = None
        self.form_title = form_title
        self.setWindowTitle("Select Employee")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel(f"Select Employee for:\n{self.form_title}")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1abc9c; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Info text
        info = QLabel("Please select the company and employee for this form.")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #888; margin-bottom: 20px;")
        layout.addWidget(info)
        
        # Selection frame
        selection_frame = QFrame()
        selection_frame.setStyleSheet("""
            QFrame {
                background-color: #3d3d3d;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        selection_layout = QVBoxLayout()
        selection_layout.setSpacing(15)
        
        # Company selection
        company_row = QHBoxLayout()
        company_label = QLabel("Company:")
        company_label.setStyleSheet("color: white; font-weight: bold; min-width: 80px;")
        company_row.addWidget(company_label)
        
        self.company_combo = QComboBox()
        self.company_combo.setMinimumWidth(300)
        self.company_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: white;
                padding: 10px;
                border: 1px solid #555;
                border-radius: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: white;
                selection-background-color: #1abc9c;
            }
        """)
        self.company_combo.currentIndexChanged.connect(self.on_company_changed)
        company_row.addWidget(self.company_combo)
        selection_layout.addLayout(company_row)
        
        # Employee selection
        employee_row = QHBoxLayout()
        employee_label = QLabel("Employee:")
        employee_label.setStyleSheet("color: white; font-weight: bold; min-width: 80px;")
        employee_row.addWidget(employee_label)
        
        self.employee_combo = QComboBox()
        self.employee_combo.setMinimumWidth(300)
        self.employee_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: white;
                padding: 10px;
                border: 1px solid #555;
                border-radius: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: white;
                selection-background-color: #1abc9c;
            }
        """)
        employee_row.addWidget(self.employee_combo)
        selection_layout.addLayout(employee_row)
        
        selection_frame.setLayout(selection_layout)
        layout.addWidget(selection_frame)
        
        # Add new company/employee links
        links_layout = QHBoxLayout()
        links_layout.addStretch()
        
        add_company_btn = QPushButton("+ Add New Company")
        add_company_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #3498db;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #5dade2;
            }
        """)
        add_company_btn.clicked.connect(self.open_add_company)
        links_layout.addWidget(add_company_btn)
        
        add_employee_btn = QPushButton("+ Add New Employee")
        add_employee_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #3498db;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #5dade2;
            }
        """)
        add_employee_btn.clicked.connect(self.open_add_employee)
        links_layout.addWidget(add_employee_btn)
        links_layout.addStretch()
        layout.addLayout(links_layout)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumWidth(120)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                padding: 12px 25px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        btn_layout.addStretch()
        
        proceed_btn = QPushButton("Proceed to Form →")
        proceed_btn.setMinimumWidth(180)
        proceed_btn.setStyleSheet("""
            QPushButton {
                background-color: #1abc9c;
                color: white;
                padding: 12px 25px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #16a085;
            }
        """)
        proceed_btn.clicked.connect(self.proceed)
        btn_layout.addWidget(proceed_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.setStyleSheet("background-color: #2d2d2d;")
        
        # Load initial data
        self.load_companies()
    
    def load_companies(self):
        """Load companies into dropdown."""
        self.company_combo.clear()
        self.company_combo.addItem("-- Select Company --", None)
        
        companies = local_db.get_all_companies()
        for company in companies:
            self.company_combo.addItem(company['name'], company['id'])
        
        if len(companies) == 0:
            self.company_combo.addItem("No companies registered", None)
    
    def on_company_changed(self):
        """Load employees for selected company."""
        self.employee_combo.clear()
        
        company_id = self.company_combo.currentData()
        if not company_id:
            self.employee_combo.addItem("-- Select Employee --", None)
            return
        
        employees = local_db.get_employees_by_company(company_id)
        
        if employees:
            self.employee_combo.addItem("-- Select Employee --", None)
            for emp in employees:
                display = f"{emp['full_name']} ({emp['id_number']})"
                self.employee_combo.addItem(display, emp['id'])
        else:
            self.employee_combo.addItem("No employees for this company", None)
    
    def open_add_company(self):
        """Open dialog to add new company."""
        from pages.company_page import AddCompanyDialog
        dialog = AddCompanyDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_companies()
    
    def open_add_employee(self):
        """Open dialog to add new employee."""
        from pages.employee_page import AddEmployeeDialog
        company_id = self.company_combo.currentData()
        dialog = AddEmployeeDialog(self, preselect_company_id=company_id)
        if dialog.exec_() == QDialog.Accepted:
            # Reload and select the new employee
            self.on_company_changed()
    
    def proceed(self):
        """Validate selection and proceed."""
        company_id = self.company_combo.currentData()
        employee_id = self.employee_combo.currentData()
        
        if not company_id:
            QMessageBox.warning(self, "Selection Required", "Please select a company.")
            return
        
        if not employee_id:
            QMessageBox.warning(self, "Selection Required", "Please select an employee.")
            return
        
        # Get full employee data
        self.selected_employee = local_db.get_employee(employee_id)
        self.accept()
    
    def get_selected_employee(self):
        """Return the selected employee data."""
        return self.selected_employee
