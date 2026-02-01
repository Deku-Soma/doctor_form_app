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
from pages.forms.form_drug_testing import FormDrugTesting
from pages.forms.form_vitamin_b import FormVitaminB
from pages.forms.form_certificate_fitness import FormCertificateFitness
from pages.forms.form_heights_questionnaire import FormHeightsQuestionnaire
from pages.forms.form_hot_cold_exposure import FormHotColdExposure
from pages.forms.form_confined_spaces import FormConfinedSpaces
from pages.forms.form_musculoskeletal import FormMusculoskeletal
from pages.forms.form_psychology import FormPsychology
from pages.forms.form_cwb_referral import FormCWBReferral
from pages.forms.form_complete_wellbeing import FormCompleteWellbeing
from pages.forms.form_annexure3 import FormAnnexure3
from pages.company_page import CompanyPage
from pages.employee_page import EmployeePage
import sys
import os 
import json
import logging
from Utility.app_context import get_resource_path

# Setup logging (if not already setup in db.py, but safe to call again)
log_path = os.path.join(os.getcwd(), 'app_debug.log')
logging.basicConfig(filename=log_path, level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class MainApp(QStackedWidget):
    def __init__(self):
        super().__init__()
        
        # Load Stylesheet
        self.load_stylesheet()

        self.login_page = LoginPage(self)
        self.home_page = HomePage(self)
        self.formA = FormA(self)
        self.formB = FormB(self)
        
        # New forms
        self.formDrugTesting = FormDrugTesting(self)
        self.formVitaminB = FormVitaminB(self)
        self.formCertificateFitness = FormCertificateFitness(self)
        self.formHeightsQuestionnaire = FormHeightsQuestionnaire(self)
        self.formHotColdExposure = FormHotColdExposure(self)
        self.formConfinedSpaces = FormConfinedSpaces(self)
        self.formMusculoskeletal = FormMusculoskeletal(self)
        self.formPsychology = FormPsychology(self)
        self.formCWBReferral = FormCWBReferral(self)
        self.formCompleteWellbeing = FormCompleteWellbeing(self)
        self.formAnnexure3 = FormAnnexure3(self)
        
        # Management pages
        self.companyPage = CompanyPage(self)
        self.employeePage = EmployeePage(self)
        
        # For passing selected company to employee page
        self.selected_company = None
        # For passing selected employee to forms
        self.selected_employee = None

        self.addWidget(self.login_page)
        self.addWidget(self.home_page)
        self.addWidget(self.formA)
        self.addWidget(self.formB)
        self.addWidget(self.formDrugTesting)
        self.addWidget(self.formVitaminB)
        self.addWidget(self.formCertificateFitness)
        self.addWidget(self.formHeightsQuestionnaire)
        self.addWidget(self.formHotColdExposure)
        self.addWidget(self.formConfinedSpaces)
        self.addWidget(self.formMusculoskeletal)
        self.addWidget(self.formPsychology)
        self.addWidget(self.formCWBReferral)
        self.addWidget(self.formCompleteWellbeing)
        self.addWidget(self.formAnnexure3)
        self.addWidget(self.companyPage)
        self.addWidget(self.employeePage)

        self.setCurrentWidget(self.login_page)

    def go_to_home(self):
        self.home_page.set_user()
        self.setCurrentWidget(self.home_page)

    def go_to_page(self, page_name):
        if page_name == "FormA":
            self.setCurrentWidget(self.formA)
        elif page_name == "FormB":
            self.setCurrentWidget(self.formB)
        elif page_name == "FormDrugTesting":
            self.setCurrentWidget(self.formDrugTesting)
        elif page_name == "FormVitaminB":
            self.setCurrentWidget(self.formVitaminB)
        elif page_name == "FormCertificateFitness":
            self.setCurrentWidget(self.formCertificateFitness)
        elif page_name == "FormHeightsQuestionnaire":
            self.setCurrentWidget(self.formHeightsQuestionnaire)
        elif page_name == "FormHotColdExposure":
            self.setCurrentWidget(self.formHotColdExposure)
        elif page_name == "FormConfinedSpaces":
            self.setCurrentWidget(self.formConfinedSpaces)
        elif page_name == "FormMusculoskeletal":
            self.setCurrentWidget(self.formMusculoskeletal)
        elif page_name == "FormPsychology":
            self.setCurrentWidget(self.formPsychology)
        elif page_name == "FormCWBReferral":
            self.setCurrentWidget(self.formCWBReferral)
        elif page_name == "FormCompleteWellbeing":
            self.setCurrentWidget(self.formCompleteWellbeing)
        elif page_name == "FormAnnexure3":
            self.setCurrentWidget(self.formAnnexure3)

    def go_to_login(self):
        self.setCurrentWidget(self.login_page)
    
    def show_page(self, page_name):
        """Navigate to management pages."""
        if page_name == "home":
            self.setCurrentWidget(self.home_page)
        elif page_name == "companies":
            self.setCurrentWidget(self.companyPage)
        elif page_name == "employees":
            self.setCurrentWidget(self.employeePage)
    
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

    def load_stylesheet(self):
        try:
            # Use get_resource_path to find the theme in the package
            qss_path = get_resource_path(os.path.join("themes", "modern.qss"))
            
            logging.info(f"Loading stylesheet from: {qss_path}")
            
            if not os.path.exists(qss_path):
                logging.error(f"Stylesheet not found at {qss_path}")
                return
            
            with open(qss_path, "r") as f:
                style = f.read()
                self.setStyleSheet(style)
                logging.info("Stylesheet loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load stylesheet: {e}")
            print(f"Failed to load stylesheet: {e}")





if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.showMaximized()
    sys.exit(app.exec_())
