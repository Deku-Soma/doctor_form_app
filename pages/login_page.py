import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLineEdit, QLabel, QPushButton,
    QVBoxLayout, QStackedWidget, QMessageBox, QHBoxLayout, QFormLayout,QSizePolicy
)
from PyQt5.QtCore import Qt
import db
import os 
import json 
import time


class LoginPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Login")
        self.init_ui()

    def init_ui(self):
        self.login_widget = self.create_login_ui()
        
        layout = QVBoxLayout()
        layout.addWidget(self.login_widget)
        self.setLayout(layout)

        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
            }
            QLabel {
                font-size: 18px;
                color: #ffffff;
                background: transparent;
            }
            QLineEdit {
                padding: 8px;
                border-radius: 6px;
                border: 1px solid #4d4d4d;
                min-width: 500px;
                background-color: #3d3d3d;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 2px solid #163b4d;
            }
            QPushButton {
                font-size: 18px;
                background-color: #163b4d;
                color: white;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #685070;
            }
        """)

    def create_login_ui(self):
        # === Main outer widget ===
        widget = QWidget()

        # === Form layout ===
        form_layout = QFormLayout()
        self.login_email = QLineEdit()
        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.Password)

        login_button = QPushButton("Login")
        login_button.clicked.connect(self.login)
        # removed switch button

        form_layout.addRow("Email:", self.login_email)
        form_layout.addRow("Password:", self.login_password)
        form_layout.addRow(login_button)

        # === Container widget for the form (for centering) ===
        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        form_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        # === Vertical centering layout ===
        vbox = QVBoxLayout()
        vbox.addStretch(1)               # push from top
        vbox.addWidget(form_widget, alignment=Qt.AlignCenter)
        vbox.addStretch(1)               # push from bottom

        # === Horizontal centering layout ===
        hbox = QHBoxLayout()
        hbox.addStretch(1)               # push from left
        hbox.addLayout(vbox)
        hbox.addStretch(1)               # push from right

        widget.setLayout(hbox)
        return widget

    def login(self):
        email = self.login_email.text()
        password = self.login_password.text()

        if not email or not password:
            QMessageBox.warning(self, "Validation Error", "Please enter both email and password.")
            return
            
        result = db.validate_login(email=email, password=password)
        
        if result['success']:
            mode = result.get('mode', 'unknown')
            msg = f"Logged in successfully via {mode.upper()} mode."
            if mode == 'offline':
                msg += "\n(Using locally cached credentials)"
            
            QMessageBox.information(self, "Login Success", msg)
            self.session_creation(result['user'])
            self.main_window.go_to_home()
        else:
            QMessageBox.warning(self, "Login Failed", f"Error: {result.get('message', 'Unknown error')}")

    def session_creation(self, user_data):
        user = user_data
        cwd =  os.getcwd()
        file_path = os.path.join(cwd,'Sessions')
        # Ensure directory exists just in case
        os.makedirs(file_path, exist_ok=True)
        
        file_name = os.path.join(file_path,'session.json')
        # Wrap in a standard structure expected by main.py
        data = {'user': user} 
        
        with open(file_name,'w') as f:
            json.dump(data, f, indent=4)





