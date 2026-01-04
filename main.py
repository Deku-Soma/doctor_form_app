# TODO: 
'''
Merge the changes from sub branch factory  into main
get colour pallat from tash 
get all the documents we need 
ammend the document styles
'''
from PyQt5.QtWidgets import QApplication, QStackedWidget
from pages.login_page import LoginPage
from pages.home_page import HomePage
from pages.formA import FormA
from pages.formB import FormB
import sys
import os 
import json

class MainApp(QStackedWidget):
    def __init__(self):
        super().__init__()

        self.login_page = LoginPage(self)
        self.home_page = HomePage(self)
        self.formA = FormA(self)
        self.formB = FormB(self)

        self.addWidget(self.login_page)
        self.addWidget(self.home_page)
        self.addWidget(self.formA)
        self.addWidget(self.formB)

        self.setCurrentWidget(self.formA)

    def go_to_home(self):
        self.home_page.set_user()
        self.setCurrentWidget(self.home_page)

    def go_to_page(self, page_name):
        if page_name == "FormA":
            self.setCurrentWidget(self.formA)
        elif page_name == "FormB":
            self.setCurrentWidget(self.formB)
    
    def fetch_session(self):
        cwd = os.getcwd()
        path = os.path.join(cwd,'Sessions')
        file = os.path.join(path,'session.json')
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                return data['user']
        except (FileNotFoundError, json.JSONDecodeError):
            return None





if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.showMaximized()
    sys.exit(app.exec_())
