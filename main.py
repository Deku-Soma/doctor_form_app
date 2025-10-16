# main.py
from PyQt5.QtWidgets import QApplication, QStackedWidget
import sys
import os
import json
from typing import Optional
# themes 
from themes.themes import apply_theme

# Keep your existing pages
from pages.login_page import LoginPage
from pages.home_page import HomePage

# New factory + schemas
from Utility.form_factory import FormFactory
from pages.forms.schemas import FormA_schema  # rename or add more as needed
# from forms.schemas import PreEmployment_schema as FormB_schema  # example

# Optional: if some forms need a special PDF generator, import and map it here
# from pages.template_generator import generate_html_pdf

# Central place to register every form your app can show.
# Key = route/name; value = dict(schema=..., pdf_generator=...)
FORM_REGISTRY = {
    "FormA": {
        "schema": FormA_schema,
        # "pdf_generator": generate_html_pdf,  # omit to use default from FormWidget
    },
    # "FormB": {"schema": FormB_schema},
}


class MainApp(QStackedWidget):
    def __init__(self):
        super().__init__()

        # Core pages
        self.login_page = LoginPage(self)
        self.home_page = HomePage(self)

        # Add core pages to stack
        self.addWidget(self.login_page)
        self.addWidget(self.home_page)

        # Cache for built forms so each is created once
        self._form_widgets = {}  # dict[str, QWidget]

        # Choose your startup page
        # self.setCurrentWidget(self.login_page)
        self.setCurrentWidget(self.home_page)

    # -------- Navigation helpers --------
    def go_to_home(self):
        # Let HomePage refresh itself if it needs session info
        if hasattr(self.home_page, "set_user"):
            self.home_page.set_user()
        self.setCurrentWidget(self.home_page)


    def go_to_form(self, form_key: str, initial_data: Optional[dict] = None):
        if form_key not in FORM_REGISTRY:
            print(f"[MainApp] Unknown form key: {form_key}")
            return

        if form_key not in self._form_widgets:
            cfg = FORM_REGISTRY[form_key]
            schema = cfg["schema"]
            pdf_gen = cfg.get("pdf_generator")

            form_widget = FormFactory.build(self, schema, pdf_gen, initial_data=initial_data)  # <--
            self.addWidget(form_widget)
            self._form_widgets[form_key] = form_widget
        else:
            # If it already exists, you can still apply new data:
            if initial_data:
                self._form_widgets[form_key].set_data(initial_data)

        self.setCurrentWidget(self._form_widgets[form_key])


    # Backwards-compat for your existing code (optional)
    def go_to_page(self, page_name: str):
        """
        Legacy router: keeps older calls working.
        """
        if page_name == "Home":
            self.go_to_home()
        elif page_name in FORM_REGISTRY:
            self.go_to_form(page_name)
        else:
            print(f"[MainApp] Unknown page '{page_name}'. Try a registered form key or 'Home'.")

    # -------- Session helper (unchanged) --------
    def fetch_session(self):
        cwd = os.getcwd()
        path = os.path.join(cwd, 'Sessions')
        file = os.path.join(path, 'session.json')
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                return data.get('user')
        except (FileNotFoundError, json.JSONDecodeError):
            return None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_theme(app)
    window = MainApp()
    window.showMaximized()
    sys.exit(app.exec_())
