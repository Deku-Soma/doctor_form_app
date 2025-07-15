# pages/feature_page1.py
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton

class FormA (QWidget):
    def __init__(self, main_window,user_details):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout()
        layout.addWidget(QLabel("This is Feature Page 1"))
        back_button = QPushButton("Back to Home")
        back_button.clicked.connect(lambda: self.main_window.go_to_home(user_details))
        layout.addWidget(back_button)
        self.setLayout(layout)
