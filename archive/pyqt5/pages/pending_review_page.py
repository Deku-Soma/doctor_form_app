# pending_review_page.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from Utility.local_db import local_db
from datetime import datetime, timezone


class PendingReviewPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def showEvent(self, event):
        """Refresh data every time the page is shown."""
        super().showEvent(event)
        self.refresh_table()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📋 Pending Review")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #ecf0f1;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_table)
        header_layout.addWidget(refresh_btn)
        
        # Back button
        back_btn = QPushButton("🏠 Back to Home")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        back_btn.clicked.connect(lambda: self.main_window.go_to_home())
        header_layout.addWidget(back_btn)
        
        layout.addLayout(header_layout)

        # Status summary
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #bdc3c7; font-size: 14px;")
        layout.addWidget(self.status_label)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Employee", "Company", "Form Type", "Submitted", "Days Pending", "Approve", "Reject"
        ])
        
        # Style
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.table)
        self.setLayout(layout)

    def refresh_table(self):
        """Refresh the pending documents table."""
        # Auto-reject expired documents first
        expired_count = local_db.auto_reject_expired()
        if expired_count > 0:
            print(f"Auto-rejected {expired_count} expired documents")
        
        # Get pending documents
        pending = local_db.get_pending_documents()
        
        self.table.setRowCount(len(pending))
        self.status_label.setText(f"Showing {len(pending)} pending document(s)")
        
        for row, doc in enumerate(pending):
            # Employee name
            emp_name = doc.get('employee_name', 'Unknown')
            name_item = QTableWidgetItem(emp_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            
            # Company
            company = doc.get('company_name', 'N/A')
            company_item = QTableWidgetItem(company)
            company_item.setFlags(company_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, company_item)
            
            # Form type (make readable)
            form_type = doc.get('form_type', '').replace('_', ' ').title()
            type_item = QTableWidgetItem(form_type)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, type_item)
            
            # Submitted date
            created_at = doc.get('status_created_at', '')
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at)
                    display_date = dt.strftime('%Y-%m-%d %H:%M')
                except Exception:
                    display_date = created_at[:16] if len(created_at) > 16 else created_at
            else:
                display_date = 'N/A'
            date_item = QTableWidgetItem(display_date)
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 3, date_item)
            
            # Days pending
            days_pending = 0
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at)
                    days_pending = (datetime.now(timezone.utc) - dt).days
                except Exception:
                    pass
            
            days_item = QTableWidgetItem(str(days_pending))
            days_item.setFlags(days_item.flags() & ~Qt.ItemIsEditable)
            days_item.setTextAlignment(Qt.AlignCenter)
            
            # Color code: yellow for pending, red for near-expiry
            if days_pending >= 25:
                days_item.setBackground(QColor("#e74c3c"))
                days_item.setForeground(QColor("#ffffff"))
            elif days_pending >= 15:
                days_item.setBackground(QColor("#f39c12"))
                days_item.setForeground(QColor("#ffffff"))
            
            self.table.setItem(row, 4, days_item)
            
            # Approve button
            approve_btn = QPushButton("✅ Approve")
            approve_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1abc9c;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #16a085;
                }
            """)
            doc_id = doc.get('document_id')
            approve_btn.clicked.connect(lambda checked, d=doc_id, n=emp_name: self.approve_document(d, n))
            self.table.setCellWidget(row, 5, approve_btn)
            
            # Reject button
            reject_btn = QPushButton("❌ Reject")
            reject_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            reject_btn.clicked.connect(lambda checked, d=doc_id, n=emp_name: self.reject_document(d, n))
            self.table.setCellWidget(row, 6, reject_btn)

    def approve_document(self, document_id, employee_name):
        """Approve a pending document."""
        reply = QMessageBox.question(
            self, "Confirm Approval",
            f"Approve document for {employee_name}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            local_db.update_document_status(document_id, "approved")
            QMessageBox.information(self, "Success", f"Document for {employee_name} has been approved.")
            self.refresh_table()

    def reject_document(self, document_id, employee_name):
        """Reject a pending document."""
        reply = QMessageBox.question(
            self, "Confirm Rejection",
            f"Reject document for {employee_name}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            local_db.update_document_status(document_id, "rejected")
            QMessageBox.information(self, "Success", f"Document for {employee_name} has been rejected.")
            self.refresh_table()
