from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
    QVBoxLayout, QFormLayout, QScrollArea, QDateEdit, QMessageBox
)
from PyQt5.QtCore import QDate
from typing import Callable, Dict, Any, Optional, List
import tempfile, os
from pages.signiture import SignaturePad
from pages.template_generator import generate_html_pdf


class FormWidget(QWidget):
    """
    Generic form widget built from a schema. 
    Exposes: get_data(), validate(), and plumbing for Submit/Generate PDF/Back.
    """
    def __init__(
        self,
        main_window,
        schema: Dict[str, Any],
        pdf_generator: Optional[Callable[[Dict[str, Any], Optional[str], str], None]] = None
    ):
        super().__init__()
        self.main_window = main_window
        self.schema = schema
        self.pdf_generator = pdf_generator or generate_html_pdf

        self.widgets: Dict[str, QWidget] = {}
        self.signature_names: List[str] = []  # track signature fields
        self._build_ui()

    # ---------- UI BUILD ----------
    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.form_layout = QFormLayout()

        # Optional title
        title = self.schema.get("title")
        if title:
            title_label = QLabel(f"<h2 style='margin-bottom:6px'>{title}</h2>")
            self.form_layout.addRow(title_label)

        # Optional description
        desc = self.schema.get("description")
        if desc:
            desc_label = QLabel(desc)
            desc_label.setWordWrap(True)
            self.form_layout.addRow(desc_label)

        # Fields
        for field in self.schema.get("fields", []):
            self._add_field(field)

        # Actions (buttons)
        actions = self.schema.get("actions", ["submit", "generate_pdf", "back"])
        button_row = QWidget()
        button_row_layout = QVBoxLayout()
        button_row_layout.setContentsMargins(0, 12, 0, 0)

        if "submit" in actions:
            submit_btn = QPushButton(self.schema.get("submit_text", "Submit"))
            submit_btn.clicked.connect(self.on_submit)
            button_row_layout.addWidget(submit_btn)

        if "generate_pdf" in actions:
            pdf_btn = QPushButton(self.schema.get("pdf_text", "Generate PDF"))
            pdf_btn.clicked.connect(self.on_generate_pdf)
            button_row_layout.addWidget(pdf_btn)

        if "back" in actions:
            back_btn = QPushButton(self.schema.get("back_text", "Back"))
            back_btn.clicked.connect(self.on_back)
            button_row_layout.addWidget(back_btn)

        button_row.setLayout(button_row_layout)
        self.form_layout.addRow(button_row)

        # Wrap
        container.setLayout(self.form_layout)
        scroll.setWidget(container)
        layout = QVBoxLayout()
        layout.addWidget(scroll)
        self.setLayout(layout)

    def _add_field(self, field: Dict[str, Any]):
        """
        field keys:
          - name (str, required)
          - label (str)
          - type ('text'|'textarea'|'date'|'signature')
          - required (bool)
          - default (str|date|'today')
          - placeholder (str)
        """
        f_type = field.get("type", "text")
        name = field["name"]
        label = field.get("label", name)

        if f_type == "text":
            w = QLineEdit()
            if "placeholder" in field:
                w.setPlaceholderText(field["placeholder"])
            if "default" in field and isinstance(field["default"], str):
                w.setText(field["default"])
            self.widgets[name] = w
            self.form_layout.addRow(label + ":", w)

        elif f_type == "textarea":
            w = QTextEdit()
            if "default" in field and isinstance(field["default"], str):
                w.setPlainText(field["default"])
            self.widgets[name] = w
            self.form_layout.addRow(label + ":", w)

        elif f_type == "date":
            w = QDateEdit()
            w.setCalendarPopup(True)
            default = field.get("default", "today")
            if default == "today":
                w.setDate(QDate.currentDate())
            elif isinstance(default, str):
                # Expect 'yyyy-MM-dd' if string provided
                qd = QDate.fromString(default, "yyyy-MM-dd")
                w.setDate(qd if qd.isValid() else QDate.currentDate())
            self.widgets[name] = w
            self.form_layout.addRow(label + ":", w)

        elif f_type == "signature":
            pad = SignaturePad()
            self.widgets[name] = pad
            self.signature_names.append(name)
            self.form_layout.addRow(label + ":", pad)

            # Optional clear button just for signatures
            clear_sig_btn = QPushButton(f"Clear {label}")
            clear_sig_btn.clicked.connect(pad.clear)
            self.form_layout.addRow(clear_sig_btn)

        else:
            # Unknown type -> text fallback
            w = QLineEdit()
            self.widgets[name] = w
            self.form_layout.addRow(label + ":", w)

    # ---------- DATA / VALIDATION ----------
    def get_data(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for field in self.schema.get("fields", []):
            name = field["name"]
            w = self.widgets[name]

            f_type = field.get("type", "text")
            if f_type == "text":
                data[name] = w.text()
            elif f_type == "textarea":
                data[name] = w.toPlainText()
            elif f_type == "date":
                data[name] = w.date().toString("yyyy-MM-dd")
            elif f_type == "signature":
                # handled separately by save_signature_images()
                data[name] = "<signature>"
            else:
                data[name] = getattr(w, "text", lambda: "")()
        return data

    def validate(self) -> bool:
        missing_labels = []
        for field in self.schema.get("fields", []):
            if not field.get("required"):
                continue
            name = field["name"]
            label = field.get("label", name)
            w = self.widgets[name]
            f_type = field.get("type", "text")

            if f_type in ("text",):
                if not w.text().strip():
                    missing_labels.append(label)
            elif f_type == "textarea":
                if not w.toPlainText().strip():
                    missing_labels.append(label)
            elif f_type == "date":
                if not w.date().isValid():
                    missing_labels.append(label)
            elif f_type == "signature":
                # very light check: does it have any strokes? (depends on your SignaturePad impl)
                # If not available, skip or implement a `has_content()` method in SignaturePad.
                if hasattr(w, "isEmpty") and w.isEmpty():
                    missing_labels.append(label)

        if missing_labels:
            QMessageBox.warning(self, "Missing required fields",
                                "Please fill: " + ", ".join(missing_labels))
            return False
        return True

    def _save_signature_images(self) -> Dict[str, str]:
        """
        Save all signature widgets to temp files; returns map name -> path
        """
        result: Dict[str, str] = {}
        for name in self.signature_names:
            pad: SignaturePad = self.widgets[name]  # type: ignore
            img = pad.get_signature_image()
            tmp = tempfile.NamedTemporaryFile(prefix=f"{name}_", suffix=".png", delete=False)
            tmp_path = tmp.name
            tmp.close()
            img.save(tmp_path)
            result[name] = tmp_path
        return result

    # ---------- ACTION HANDLERS ----------
    def on_submit(self):
        if not self.validate():
            return
        data = self.get_data()
        sig_map = self._save_signature_images()

        # Pick a template id if present; else default to 'default'
        template_id = str(self.schema.get("template_id", "default"))
        # Choose which signature to send to your generator (if you only accept one)
        primary_sig_path = None
        if sig_map:
            # choose first signature field as primary for PDF, you can customize this
            primary_sig_path = next(iter(sig_map.values()))

        # Call injected or default pdf generator
        self.pdf_generator(data, primary_sig_path, template_id)

        # optional cleanup of temp signature files
        for p in sig_map.values():
            try:
                os.remove(p)
            except OSError:
                pass

        QMessageBox.information(self, "Submitted", "PDF Generated!")

    def on_generate_pdf(self):
        if not self.validate():
            return
        data = self.get_data()
        sig_map = self._save_signature_images()
        template_id = str(self.schema.get("template_id", "default"))
        primary_sig_path = next(iter(sig_map.values())) if sig_map else None

        self.pdf_generator(data, primary_sig_path, template_id)
        QMessageBox.information(self, "PDF", "PDF Generated!")

        for p in sig_map.values():
            try:
                os.remove(p)
            except OSError:
                pass

    def on_back(self):
        if self.main_window and hasattr(self.main_window, "go_to_home"):
            self.main_window.go_to_home()


class FormFactory:
    """
    Turn a schema into a FormWidget. You can also register common field presets if you like.
    """
    @staticmethod
    def build(main_window, schema: Dict[str, Any],
              pdf_generator: Optional[Callable[[Dict[str, Any], Optional[str], str], None]] = None) -> QWidget:
        return FormWidget(main_window, schema, pdf_generator)
