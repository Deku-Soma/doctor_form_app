# pages/formA_page.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from Utility.form_factory import FormFactory
from forms.schemas import FormA_schema
# from pages.template_generator import generate_html_pdf  # only if you want to override per-form

class FormAPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        # Build the form from the schema (optionally pass a custom PDF generator)
        self.form = FormFactory.build(
            main_window=main_window,
            schema=FormA_schema,
            # pdf_generator=generate_html_pdf,  # optional override
        )

        layout = QVBoxLayout()
        layout.addWidget(self.form)
        self.setLayout(layout)