# pages/company_template_dialog.py
"""
Dialog for viewing and editing company-level form field templates.
Opened from the Company Management page via the "Form Templates" button.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QFormLayout,
    QLineEdit, QCheckBox, QPushButton, QLabel, QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QFont
from Utility.local_db import local_db
import db
import threading


class CompanyTemplateDialog(QDialog):
    """
    Shows one tab per form type that has a saved template for this company.
    Each tab lists field label / current default value / lock toggle.
    Changes are saved back via local_db.save_company_template().
    """

    def __init__(self, company_id: str, company_name: str, parent=None):
        super().__init__(parent)
        self.company_id = company_id
        self.setWindowTitle(f"Form Templates — {company_name}")
        self.setMinimumSize(750, 520)
        # {form_type: {field_key: {"value_edit": QLineEdit, "lock_cb": QCheckBox}}}
        self._widgets = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Title
        title = QLabel("Manage company-wide default values for each form type.")
        title.setStyleSheet("color: #aaaaaa; font-size: 13px;")
        layout.addWidget(title)

        form_types = local_db.list_company_templates(self.company_id)

        if not form_types:
            empty = QLabel(
                "No templates saved yet.\n\n"
                "Templates are captured automatically after the first form submission for each company."
            )
            empty.setStyleSheet("color: #888888; font-size: 14px; padding: 20px;")
            empty.setWordWrap(True)
            layout.addWidget(empty)
            return

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #4d4d4d; background: #3d3d3d; }
            QTabBar::tab { background: #2d2d2d; color: #cccccc; padding: 8px 16px; }
            QTabBar::tab:selected { background: #1abc9c; color: white; font-weight: bold; }
        """)

        for form_type in form_types:
            tab, tab_widgets = self._build_tab(form_type)
            display_name = form_type.replace("_", " ").title()
            self.tabs.addTab(tab, display_name)
            self._widgets[form_type] = tab_widgets

        layout.addWidget(self.tabs)

        # Footer buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        save_btn = QPushButton("💾  Save All Changes")
        save_btn.setMinimumHeight(40)
        save_btn.setStyleSheet(
            "background-color: #1abc9c; color: white; font-weight: bold; "
            "padding: 8px 20px; border-radius: 5px;"
        )
        save_btn.clicked.connect(self._save_all)
        btn_row.addWidget(save_btn)

        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(40)
        close_btn.setStyleSheet("padding: 8px 20px; border-radius: 5px;")
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)
        self.setStyleSheet("background-color: #2d2d2d; color: white;")

    def _build_tab(self, form_type: str):
        """
        Returns (QWidget tab, {field_key: {"value_edit": QLineEdit, "lock_cb": QCheckBox}})
        """
        template = local_db.get_company_template(self.company_id, form_type)
        tab = QWidget()
        tab.setStyleSheet("background-color: #3d3d3d;")
        form = QFormLayout(tab)
        form.setSpacing(10)
        form.setContentsMargins(16, 16, 16, 16)
        tab_widgets = {}

        for field_key, meta in template.items():
            row = QHBoxLayout()

            value_edit = QLineEdit(str(meta["value"]))
            value_edit.setMinimumHeight(34)
            value_edit.setStyleSheet(
                "background-color: #4d4d4d; color: white; "
                "border: 1px solid #5d5d5d; border-radius: 4px; padding: 4px 8px;"
            )
            row.addWidget(value_edit, stretch=4)

            lock_cb = QCheckBox("Locked")
            lock_cb.setChecked(meta.get("is_locked", False))
            lock_cb.setToolTip(
                "If checked, this field will be visually highlighted as a company default "
                "and marked read-only when the form opens."
            )
            lock_cb.setStyleSheet("color: #cccccc;")
            row.addWidget(lock_cb, stretch=1)

            label_text = meta.get("label", field_key.replace("_", " ").title())
            label = QLabel(label_text + ":")
            label.setStyleSheet("color: #dddddd;")
            form.addRow(label, row)

            tab_widgets[field_key] = {"value_edit": value_edit, "lock_cb": lock_cb}

        return tab, tab_widgets

    def _save_all(self):
        """Read current widget values and persist to local_db, then trigger cloud sync."""
        for form_type, fields in self._widgets.items():
            updated = {
                field_key: {
                    "value":     w["value_edit"].text(),
                    "label":     field_key.replace("_", " ").title(),
                    "is_locked": w["lock_cb"].isChecked()
                }
                for field_key, w in fields.items()
            }
            local_db.save_company_template(self.company_id, form_type, updated)
            threading.Thread(
                target=db.sync_company_templates_to_cloud,
                args=(self.company_id,),
                daemon=True
            ).start()

        QMessageBox.information(self, "Saved", "All template changes saved successfully.")
