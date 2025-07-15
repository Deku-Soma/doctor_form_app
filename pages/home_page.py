# home_page.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

class HomePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.user = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.welcome_label = QLabel("Welcome!")
        layout.addWidget(self.welcome_label)

        feature1_btn = QPushButton("Go to Feature 1")
        feature2_btn = QPushButton("Go to Feature 2")

        feature1_btn.clicked.connect(lambda: self.main_window.go_to_page("feature1",))
        feature2_btn.clicked.connect(lambda: self.main_window.go_to_page("feature2"))

        layout.addWidget(feature1_btn)
        layout.addWidget(feature2_btn)

        self.setLayout(layout)

    def set_user(self, user_data):
        self.user = user_data
        self.welcome_label.setText(f"Welcome, {self.user['user']['user_email']}!")
