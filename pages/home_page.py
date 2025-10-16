# home_page.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QSizePolicy
)
from PyQt5.QtCore import Qt


class HomePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.user = None
        self.init_ui()

    def init_ui(self):
        # === Main horizontal layout ===
        main_layout = QHBoxLayout()

        # === Main content area (center-left) ===
        content_layout = QVBoxLayout()
        self.welcome_label = QLabel("Welcome!")
        self.welcome_label.setStyleSheet("font-size: 24px;")
        self.welcome_label.setAlignment(Qt.AlignTop)
        content_layout.addWidget(self.welcome_label)
        content_layout.addStretch(1)

        # === Right-side menu bar ===
        menu_layout = QVBoxLayout()
        menu_layout.setAlignment(Qt.AlignLeft)

        btn_form_a = QPushButton("Form A")
        btn_form_b = QPushButton("Form B")
        btn_logout = QPushButton("Logout")

        btn_form_a.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_form_b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_logout.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        btn_form_a.clicked.connect(lambda: self.main_window.go_to_form("FormA"))
        btn_form_b.clicked.connect(lambda: self.main_window.go_to_form("FormB"))
        btn_logout.clicked.connect(self.logout)

        menu_layout.addWidget(btn_form_a)
        menu_layout.addWidget(btn_form_b)
        menu_layout.addStretch()
        menu_layout.addWidget(btn_logout)

        # === Add layouts to main layout ===
        main_layout.addLayout(content_layout, stretch=3)
        main_layout.addLayout(menu_layout, stretch=1)

        self.setLayout(main_layout)

    def set_user(self):
        self.user = self.main_window.fetch_session()
        if self.user:
            self.welcome_label.setText(f"Welcome, {self.user['user_name']}!")
        else:
            self.welcome_label.setText("No user found.")

    def logout(self):
        self.main_window.go_to_login()
