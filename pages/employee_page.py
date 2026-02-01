# employee_page.py
"""
Employee Management Page - Register, edit, and delete employees.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QDialog, QFormLayout,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from Utility.local_db import local_db


class AddEmployeeDialog(QDialog):
    """Dialog for adding or editing an employee."""
    def __init__(self, parent=None, employee=None, preselect_company_id=None):
        super().__init__(parent)
        self.employee = employee
        self.preselect_company_id = preselect_company_id
        self.setWindowTitle("Edit Employee" if employee else "Add New Employee")
        self.setMinimumWidth(450)
        self.init_ui()
        
    def init_ui(self):
        layout = QFormLayout()
        layout.setSpacing(15)
        
        # Company dropdown
        self.company_combo = QComboBox()
        self.companies = local_db.get_all_companies()
        for company in self.companies:
            self.company_combo.addItem(company['name'], company['id'])
        
        # Pre-select company if specified
        if self.employee and self.employee.get('company_id'):
            idx = self.company_combo.findData(self.employee['company_id'])
            if idx >= 0:
                self.company_combo.setCurrentIndex(idx)
        elif self.preselect_company_id:
            idx = self.company_combo.findData(self.preselect_company_id)
            if idx >= 0:
                self.company_combo.setCurrentIndex(idx)
        
        layout.addRow("Company *:", self.company_combo)
        
        # Full Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Full name")
        if self.employee:
            self.name_input.setText(self.employee.get('full_name', ''))
        layout.addRow("Full Name *:", self.name_input)
        
        # ID Number
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("SA ID Number or Passport")
        if self.employee:
            self.id_input.setText(self.employee.get('id_number', ''))
        layout.addRow("ID Number *:", self.id_input)
        
        # Job Title
        self.job_input = QLineEdit()
        self.job_input.setPlaceholderText("e.g. Machine Operator")
        if self.employee:
            self.job_input.setText(self.employee.get('job_title', '') or '')
        layout.addRow("Job Title:", self.job_input)
        
        # Department
        self.dept_input = QLineEdit()
        self.dept_input.setPlaceholderText("e.g. Mining Operations")
        if self.employee:
            self.dept_input.setText(self.employee.get('department', '') or '')
        layout.addRow("Department:", self.dept_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save" if self.employee else "Add Employee")
        save_btn.setStyleSheet("background-color: #1abc9c; color: white; font-weight: bold;")
        save_btn.clicked.connect(self.save_employee)
        btn_layout.addWidget(save_btn)
        
        layout.addRow(btn_layout)
        self.setLayout(layout)
    
    def save_employee(self):
        company_id = self.company_combo.currentData()
        name = self.name_input.text().strip()
        id_number = self.id_input.text().strip()
        
        if not company_id:
            QMessageBox.warning(self, "Validation Error", "Please select a company.")
            return
        if not name:
            QMessageBox.warning(self, "Validation Error", "Full name is required.")
            return
        if not id_number:
            QMessageBox.warning(self, "Validation Error", "ID number is required.")
            return
        
        job_title = self.job_input.text().strip() or None
        department = self.dept_input.text().strip() or None
        
        try:
            if self.employee:
                # Update existing
                local_db.update_employee(
                    self.employee['id'],
                    company_id=company_id,
                    full_name=name,
                    id_number=id_number,
                    job_title=job_title,
                    department=department
                )
            else:
                # Create new
                local_db.create_employee(company_id, name, id_number, job_title, department)
            
            self.accept()
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                QMessageBox.warning(self, "Error", "An employee with this ID number already exists.")
            else:
                QMessageBox.critical(self, "Error", f"Failed to save employee: {e}")


class EmployeePage(QWidget):
    """Page for managing employees."""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.filter_company_id = None  # Optional filter by company
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title = QLabel("Employee Management")
        self.title.setFont(QFont("Arial", 24, QFont.Bold))
        self.title.setStyleSheet("color: white;")
        header_layout.addWidget(self.title)
        
        header_layout.addStretch()
        
        # Back button
        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        back_btn.clicked.connect(self.go_back)
        header_layout.addWidget(back_btn)
        
        main_layout.addLayout(header_layout)
        
        # Filter and Add row
        filter_layout = QHBoxLayout()
        
        # Company filter
        filter_label = QLabel("Filter by Company:")
        filter_label.setStyleSheet("color: white;")
        filter_layout.addWidget(filter_label)
        
        self.company_filter = QComboBox()
        self.company_filter.setMinimumWidth(200)
        self.company_filter.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.company_filter)
        
        filter_layout.addStretch()
        
        # Add Employee button
        add_btn = QPushButton("+ Add New Employee")
        add_btn.setStyleSheet("""
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
        add_btn.clicked.connect(self.add_employee)
        filter_layout.addWidget(add_btn)
        
        main_layout.addLayout(filter_layout)
        
        # Employees Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Name", "ID Number", "Company", "Job Title", "Department", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #3d3d3d;
                color: white;
                gridline-color: #4d4d4d;
                border: none;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 10px;
            }
            QTableWidget::item:selected {
                background-color: #1abc9c;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        main_layout.addWidget(self.table)
        
        self.setLayout(main_layout)
        self.setStyleSheet("background-color: #2d2d2d;")
        
    def showEvent(self, event):
        """Refresh data when page is shown."""
        super().showEvent(event)
        self.load_filter_options()
        
        # Check if filtered from company page
        if hasattr(self.main_window, 'selected_company') and self.main_window.selected_company:
            company = self.main_window.selected_company
            self.title.setText(f"Employees - {company['name']}")
            idx = self.company_filter.findData(company['id'])
            if idx >= 0:
                self.company_filter.setCurrentIndex(idx)
            self.main_window.selected_company = None  # Clear selection
        else:
            self.load_employees()
    
    def load_filter_options(self):
        """Load company filter options."""
        self.company_filter.blockSignals(True)
        self.company_filter.clear()
        self.company_filter.addItem("All Companies", None)
        
        companies = local_db.get_all_companies()
        for company in companies:
            self.company_filter.addItem(company['name'], company['id'])
        
        self.company_filter.blockSignals(False)
    
    def on_filter_changed(self):
        """Handle company filter change."""
        self.filter_company_id = self.company_filter.currentData()
        self.load_employees()
    
    def load_employees(self):
        """Load employees into the table."""
        if self.filter_company_id:
            employees = local_db.get_employees_by_company(self.filter_company_id)
            # Add company info to each employee
            company = local_db.get_company(self.filter_company_id)
            for emp in employees:
                emp['company_name'] = company['name'] if company else '-'
        else:
            employees = local_db.get_all_employees()
        
        self.table.setRowCount(len(employees))
        
        for row, emp in enumerate(employees):
            self.table.setItem(row, 0, QTableWidgetItem(emp['full_name']))
            self.table.setItem(row, 1, QTableWidgetItem(emp['id_number']))
            self.table.setItem(row, 2, QTableWidgetItem(emp.get('company_name', '-')))
            self.table.setItem(row, 3, QTableWidgetItem(emp.get('job_title') or '-'))
            self.table.setItem(row, 4, QTableWidgetItem(emp.get('department') or '-'))
            
            # Actions buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_layout.setSpacing(5)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet("background-color: #3498db; color: white; padding: 5px 10px; border-radius: 3px;")
            edit_btn.clicked.connect(lambda checked, e=emp: self.edit_employee(e))
            actions_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px 10px; border-radius: 3px;")
            delete_btn.clicked.connect(lambda checked, e=emp: self.delete_employee(e))
            actions_layout.addWidget(delete_btn)
            
            actions_widget.setLayout(actions_layout)
            self.table.setCellWidget(row, 5, actions_widget)
    
    def add_employee(self):
        """Open dialog to add new employee."""
        preselect = self.filter_company_id
        dialog = AddEmployeeDialog(self, preselect_company_id=preselect)
        if dialog.exec_() == QDialog.Accepted:
            self.load_employees()
    
    def edit_employee(self, employee):
        """Open dialog to edit employee."""
        dialog = AddEmployeeDialog(self, employee)
        if dialog.exec_() == QDialog.Accepted:
            self.load_employees()
    
    def delete_employee(self, employee):
        """Delete an employee after confirmation."""
        reply = QMessageBox.question(
            self, 
            "Confirm Delete",
            f"Are you sure you want to delete '{employee['full_name']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            local_db.delete_employee(employee['id'])
            self.load_employees()
    
    def go_back(self):
        """Return to previous page."""
        self.title.setText("Employee Management")
        self.filter_company_id = None
        if self.company_filter.count() > 0:
            self.company_filter.setCurrentIndex(0)
        self.main_window.show_page("companies")
