# company_page.py
"""
Company Management Page - Register, edit, and delete companies.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QDialog, QFormLayout,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from Utility.local_db import local_db
from pages.company_template_dialog import CompanyTemplateDialog


class AddCompanyDialog(QDialog):
    """Dialog for adding or editing a company."""
    def __init__(self, parent=None, company=None):
        super().__init__(parent)
        self.company = company  # If editing, this contains existing data
        self.setWindowTitle("Edit Company" if company else "Add New Company")
        self.setMinimumWidth(400)
        self.init_ui()
        
    def init_ui(self):
        layout = QFormLayout()
        layout.setSpacing(15)
        
        # Company Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter company name")
        if self.company:
            self.name_input.setText(self.company.get('name', ''))
        layout.addRow("Company Name *:", self.name_input)
        
        # Contact Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("contact@company.com")
        if self.company:
            self.email_input.setText(self.company.get('contact_email', '') or '')
        layout.addRow("Contact Email:", self.email_input)
        
        # Contact Phone
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+27 XX XXX XXXX")
        if self.company:
            self.phone_input.setText(self.company.get('contact_phone', '') or '')
        layout.addRow("Contact Phone:", self.phone_input)
        
        # Address
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Company address")
        if self.company:
            self.address_input.setText(self.company.get('address', '') or '')
        layout.addRow("Address:", self.address_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save" if self.company else "Add Company")
        save_btn.setStyleSheet("background-color: #1abc9c; color: white; font-weight: bold;")
        save_btn.clicked.connect(self.save_company)
        btn_layout.addWidget(save_btn)
        
        layout.addRow(btn_layout)
        self.setLayout(layout)
    
    def save_company(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Company name is required.")
            return
        
        email = self.email_input.text().strip() or None
        phone = self.phone_input.text().strip() or None
        address = self.address_input.text().strip() or None
        
        try:
            if self.company:
                # Update existing
                local_db.update_company(
                    self.company['id'],
                    name=name,
                    contact_email=email,
                    contact_phone=phone,
                    address=address
                )
            else:
                # Create new
                local_db.create_company(name, email, phone, address)
            
            self.accept()
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                QMessageBox.warning(self, "Error", "A company with this name already exists.")
            else:
                QMessageBox.critical(self, "Error", f"Failed to save company: {e}")


class CompanyPage(QWidget):
    """Page for managing companies."""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Company Management")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Back button
        back_btn = QPushButton("← Back to Home")
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
        
        # Add Company button
        add_btn = QPushButton("+ Add New Company")
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
        add_btn.clicked.connect(self.add_company)
        add_layout = QHBoxLayout()
        add_layout.addWidget(add_btn)
        add_layout.addStretch()
        main_layout.addLayout(add_layout)
        
        # Companies Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Name", "Email", "Phone", "Address", "Edit", "Delete", "Employees", "Templates"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setDefaultSectionSize(50)
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
        self.load_companies()
    
    def load_companies(self):
        """Load all companies into the table."""
        companies = local_db.get_all_companies()
        self.table.setRowCount(len(companies))
        
        for row, company in enumerate(companies):
            self.table.setItem(row, 0, QTableWidgetItem(company['name']))
            self.table.setItem(row, 1, QTableWidgetItem(company.get('contact_email') or '-'))
            self.table.setItem(row, 2, QTableWidgetItem(company.get('contact_phone') or '-'))
            self.table.setItem(row, 3, QTableWidgetItem(company.get('address') or '-'))
            
            # Edit button
            edit_widget = QWidget()
            edit_layout = QHBoxLayout()
            edit_layout.setContentsMargins(5, 5, 5, 5)
            edit_btn = QPushButton("Edit")
            edit_btn.setMinimumHeight(35)
            edit_btn.setStyleSheet("background-color: #3498db; color: white; padding: 5px 10px; border-radius: 3px;")
            edit_btn.clicked.connect(lambda checked, c=company: self.edit_company(c))
            edit_layout.addWidget(edit_btn)
            edit_widget.setLayout(edit_layout)
            self.table.setCellWidget(row, 4, edit_widget)
            
            # Delete button
            delete_widget = QWidget()
            delete_layout = QHBoxLayout()
            delete_layout.setContentsMargins(5, 5, 5, 5)
            delete_btn = QPushButton("Delete")
            delete_btn.setMinimumHeight(35)
            delete_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px 10px; border-radius: 3px;")
            delete_btn.clicked.connect(lambda checked, c=company: self.delete_company(c))
            delete_layout.addWidget(delete_btn)
            delete_widget.setLayout(delete_layout)
            self.table.setCellWidget(row, 5, delete_widget)
            
            # Employees button
            employees_widget = QWidget()
            employees_layout = QHBoxLayout()
            employees_layout.setContentsMargins(5, 5, 5, 5)
            employees_btn = QPushButton("Employees")
            employees_btn.setMinimumHeight(35)
            employees_btn.setStyleSheet("background-color: #9b59b6; color: white; padding: 5px 10px; border-radius: 3px;")
            employees_btn.clicked.connect(lambda checked, c=company: self.view_employees(c))
            employees_layout.addWidget(employees_btn)
            employees_widget.setLayout(employees_layout)
            self.table.setCellWidget(row, 6, employees_widget)

            # Form Templates button
            templates_widget = QWidget()
            templates_layout = QHBoxLayout()
            templates_layout.setContentsMargins(5, 5, 5, 5)
            templates_btn = QPushButton("Templates")
            templates_btn.setMinimumHeight(35)
            templates_btn.setStyleSheet("background-color: #1D9E75; color: white; padding: 5px 10px; border-radius: 3px;")
            templates_btn.clicked.connect(lambda checked, c=company: self.open_templates(c))
            templates_layout.addWidget(templates_btn)
            templates_widget.setLayout(templates_layout)
            self.table.setCellWidget(row, 7, templates_widget)
    
    def add_company(self):
        """Open dialog to add new company."""
        dialog = AddCompanyDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_companies()
    
    def edit_company(self, company):
        """Open dialog to edit company."""
        dialog = AddCompanyDialog(self, company)
        if dialog.exec_() == QDialog.Accepted:
            self.load_companies()
    
    def delete_company(self, company):
        """Delete a company after confirmation."""
        reply = QMessageBox.question(
            self, 
            "Confirm Delete",
            f"Are you sure you want to delete '{company['name']}'?\n\nNote: Companies with employees cannot be deleted.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if local_db.delete_company(company['id']):
                self.load_companies()
            else:
                QMessageBox.warning(
                    self, 
                    "Cannot Delete",
                    "This company has employees. Remove all employees first."
                )
    
    def view_employees(self, company):
        """Navigate to employee page filtered by this company."""
        # Store selected company for employee page
        self.main_window.selected_company = company
        self.main_window.show_page("employees")

    def open_templates(self, company):
        """Open the Form Templates dialog for this company."""
        dialog = CompanyTemplateDialog(
            company_id=company['id'],
            company_name=company['name'],
            parent=self
        )
        dialog.exec_()

    def go_back(self):
        """Return to home page."""
        self.main_window.show_page("home")
