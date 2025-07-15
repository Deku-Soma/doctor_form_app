# main.py
from PyQt5.QtWidgets import QApplication, QStackedWidget
from pages.login_page import LoginPage
from pages.home_page import HomePage
from pages.formA import FormA
from pages.formB import FormB
import sys

class MainApp(QStackedWidget):
    def __init__(self):
        super().__init__()

        self.login_page = LoginPage(self)
        self.home_page = HomePage(self)
        self.feature_page1 = FormA(self)
        self.feature_page2 = FormB(self)

        self.addWidget(self.login_page)
        self.addWidget(self.home_page)
        self.addWidget(self.feature_page1)
        self.addWidget(self.feature_page2)

        self.setCurrentWidget(self.login_page)

    def go_to_home(self, user_data=None):
        self.home_page.set_user(user_data)
        self.setCurrentWidget(self.home_page)

    def go_to_page(self, page_name,user_details):
        if page_name == "feature1":
            self.setCurrentWidget(self.feature_page1)
        elif page_name == "feature2":
            self.setCurrentWidget(self.feature_page2)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.showMaximized()
    sys.exit(app.exec_())
