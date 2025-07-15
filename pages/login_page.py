import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLineEdit, QLabel, QPushButton,
    QVBoxLayout, QStackedWidget, QMessageBox, QHBoxLayout, QFormLayout,QSizePolicy
)
from PyQt5.QtCore import Qt
import db


class LoginPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Login / Sign Up")
        self.init_ui()

    def init_ui(self):
        self.stacked = QStackedWidget()
        self.login_widget = self.create_login_ui()
        self.signup_widget = self.create_signup_ui()

        self.stacked.addWidget(self.login_widget)
        self.stacked.addWidget(self.signup_widget)

        layout = QVBoxLayout()
        layout.addWidget(self.stacked)
        self.setLayout(layout)

        self.setStyleSheet("""
            QLabel {
                font-size: 18px;
            }
            QLineEdit {
                padding: 8px;
                border-radius: 6px;
                border: 1px solid #ccc;
                min-width: 500px;
            }
            QPushButton {
                font-size: 18px;
                background-color: #4295f5;
                color: white;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #43818c;
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
        switch_button = QPushButton("Switch to Sign Up")
        login_button.clicked.connect(self.login)
        switch_button.clicked.connect(self.show_signup)

        form_layout.addRow("Email:", self.login_email)
        form_layout.addRow("Password:", self.login_password)
        form_layout.addRow(login_button)
        form_layout.addRow(switch_button)

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


    def create_signup_ui(self):

        # === Outer widget ===
        widget = QWidget()

        # === Form layout ===
        form_layout = QFormLayout()
        self.signup_username = QLineEdit()
        self.signup_email = QLineEdit()
        self.signup_password = QLineEdit()
        self.signup_password.setEchoMode(QLineEdit.Password)

        signup_button = QPushButton("Sign Up")
        switch_button = QPushButton("Switch to Login")
        signup_button.clicked.connect(self.sign_up)
        switch_button.clicked.connect(self.show_login)

        form_layout.addRow("Username:", self.signup_username)
        form_layout.addRow("Email:", self.signup_email)
        form_layout.addRow("Password:", self.signup_password)
        form_layout.addRow(signup_button)
        form_layout.addRow(switch_button)

        # === Wrap form in a widget so we can size-control it ===
        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        form_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        # === Vertical centering ===
        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addWidget(form_widget, alignment=Qt.AlignCenter)
        vbox.addStretch(1)

        # === Horizontal centering ===
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addLayout(vbox)
        hbox.addStretch(1)

        widget.setLayout(hbox)
        return widget


    def show_login(self):
        self.stacked.setCurrentWidget(self.login_widget)

    def show_signup(self):
        self.stacked.setCurrentWidget(self.signup_widget)

    def login(self):
        email = self.login_email.text()
        password = self.login_password.text()

        if not email or not password:
            QMessageBox.warning(self, "Validation Error", "Please enter both email and password.")
            return
        result = db.validate_login(email=email,password=password)
        if result['success']:
            QMessageBox.information(self, "Login", f"Logged in with email: {email}")
            self.main_window.go_to_home(result)

        else:
            QMessageBox.information(self, "Login", f"Failed to Login.\n Password or email is incorrect")

    def sign_up(self):
        username = self.signup_username.text()
        email = self.signup_email.text()
        password = self.signup_password.text()

        if not username or not email or not password:
            QMessageBox.warning(self, "Validation Error", "Please fill in all fields.")
            return

        db.create_user(email=email, password=password,username=username) ## create the user
        #TODO: how to handel errors  
        QMessageBox.information(self, "Sign Up", f"Account created for {username}!")
        self.show_login()


