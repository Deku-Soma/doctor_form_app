from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
    QVBoxLayout, QFormLayout, QScrollArea, QDateEdit, QMessageBox
)
from PyQt5.QtCore import QDate, Qt
from typing import Callable, Dict, Any, Optional, List, Tuple
import tempfile, os

from pages.signiture import SignaturePad
from pages.template_generator import generate_html_pdf


class FormFactory(QWidget):
    """
    Generic, style-aware form widget built from a schema.
    Exposes: get_data(), validate(), on_submit(), on_generate_pdf(), on_back()
    """
    def __init__(
        self,
        main_window,
        schema: Dict[str, Any],
        pdf_generator: Optional[Callable[[Dict[str, Any], Optional[str], str], None]] = None
    ):
        super().__init__()
        self.setObjectName("FormRoot")  # QSS target
        if "class" in schema:  # optional per-form class (for QSS varianting)
            self.setProperty("form-class", schema["class"])

        self.main_window = main_window
        self.schema = schema
        self.pdf_generator = pdf_generator or generate_html_pdf

        self.widgets: Dict[str, QWidget] = {}
        self.signature_names: List[str] = []  # track signature fields
        self._build_ui()

        # Optional per-schema subtree QSS override
        extra_qss = self.schema.get("extra_qss")
        if extra_qss:
            self.setStyleSheet(extra_qss)

    # ---------- UI BUILD ----------
    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("FormScroll")

        container = QWidget()
        container.setObjectName("FormContainer")

        self.form_layout = QFormLayout()
        self.form_layout.setVerticalSpacing(8)
        self.form_layout.setHorizontalSpacing(12)
        container.setContentsMargins(16, 16, 16, 16)

        # Optional title
        title = self.schema.get("title")
        if title:
            title_label = QLabel(title)
            title_label.setProperty("role", "title")
            title_label.setTextFormat(Qt.RichText)
            self.form_layout.addRow(title_label)

        # Optional description
        desc = self.schema.get("description")
        if desc:
            desc_label = QLabel(desc)
            desc_label.setWordWrap(True)
            desc_label.setProperty("role", "description")
            self.form_layout.addRow(desc_label)

        # Fields
        for field in self.schema.get("fields", []):
            self._add_field(field)

        # Actions (buttons)
        # Can be ["submit", "generate_pdf", "back"] or list of dicts:
        # {"type": "...", "text": "...", "variant": "primary|secondary|danger"}
        actions = self.schema.get("actions", ["submit", "generate_pdf", "back"])
        btn_container = QWidget()
        btn_container.setObjectName("ActionBar")
        btn_layout = QVBoxLayout()
        btn_layout.setContentsMargins(0, 12, 0, 0)
        btn_layout.setSpacing(8)

        for kind, text, variant in self._normalize_actions(actions):
            btn = QPushButton(text)
            if variant:
                btn.setProperty("variant", variant)
            else:
                # sensible defaults
                if kind == "submit":
                    btn.setProperty("variant", "primary")
                else:
                    btn.setProperty("variant", "secondary")

            if kind == "submit":
                btn.clicked.connect(self.on_submit)
            elif kind == "generate_pdf":
                btn.clicked.connect(self.on_generate_pdf)
            elif kind == "back":
                btn.clicked.connect(self.on_back)
            else:
                continue

            btn_layout.addWidget(btn)

        btn_container.setLayout(btn_layout)
        self.form_layout.addRow(btn_container)

        # Wrap
        container.setLayout(self.form_layout)
        scroll.setWidget(container)

        outer = QVBoxLayout()
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(10)
        outer.addWidget(scroll)
        self.setLayout(outer)

    def _normalize_actions(self, actions: List[Any]) -> List[Tuple[str, str, Optional[str]]]:
        """
        Normalize actions into (kind, text, variant) tuples.
        """
        out: List[Tuple[str, str, Optional[str]]] = []
        for a in actions:
            if isinstance(a, str):
                if a == "submit":
                    out.append(("submit", self.schema.get("submit_text", "Submit"), None))
                elif a == "generate_pdf":
                    out.append(("generate_pdf", self.schema.get("pdf_text", "Generate PDF"), None))
                elif a == "back":
                    out.append(("back", self.schema.get("back_text", "Back"), None))
            elif isinstance(a, dict):
                kind = a.get("type")
                if kind not in {"submit", "generate_pdf", "back"}:
                    continue
                text = a.get("text") or \
                    (self.schema.get("submit_text", "Submit") if kind == "submit" else
                     self.schema.get("pdf_text", "Generate PDF") if kind == "generate_pdf" else
                     self.schema.get("back_text", "Back"))
                out.append((kind, text, a.get("variant")))
        return out

    def _make_field_label(self, text: str, required: bool = False) -> QLabel:
        lbl = QLabel(f"{text}{' *' if required else ''}:")
        lbl.setProperty("role", "field-label")
        return lbl

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
        required = bool(field.get("required"))

        # Build widget
        if f_type == "text":
            w = QLineEdit()
            if "placeholder" in field:
                w.setPlaceholderText(field["placeholder"])
            if "default" in field and isinstance(field["default"], str):
                w.setText(field["default"])

        elif f_type == "textarea":
            w = QTextEdit()
            if "default" in field and isinstance(field["default"], str):
                w.setPlainText(field["default"])

        elif f_type == "date":
            w = QDateEdit()
            w.setCalendarPopup(True)
            default = field.get("default", "today")
            if default == "today":
                w.setDate(QDate.currentDate())
            elif isinstance(default, str):
                qd = QDate.fromString(default, "yyyy-MM-dd")
                w.setDate(qd if qd.isValid() else QDate.currentDate())

        elif f_type == "signature":
            pad = SignaturePad()
            pad.setProperty("role", "signature")
            self.widgets[name] = pad
            self.signature_names.append(name)

            # Label + signature pad
            self.form_layout.addRow(self._make_field_label(label, required), pad)

            # Optional clear button just for signatures
            clear_sig_btn = QPushButton(f"Clear {label}")
            clear_sig_btn.setProperty("variant", "secondary")
            clear_sig_btn.clicked.connect(pad.clear)
            self.form_layout.addRow(clear_sig_btn)
            return  # signature handled, exit early

        else:
            # Unknown type -> text fallback
            w = QLineEdit()

        # Tag input for QSS states
        if isinstance(w, (QLineEdit, QTextEdit, QDateEdit)):
            w.setProperty("state", "")  # default state (no error)

        self.widgets[name] = w
        self.form_layout.addRow(self._make_field_label(label, required), w)

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
                data[name] = "<signature>"
            else:
                data[name] = getattr(w, "text", lambda: "")()
        return data

    def _mark_error(self, widget: QWidget, is_error: bool):
        """
        Toggle an 'error' visual state on inputs via dynamic properties.
        """
        widget.setProperty("state", "error" if is_error else "")
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def validate(self) -> bool:
        missing_labels = []
        # Clear previous error states
        for field in self.schema.get("fields", []):
            name = field["name"]
            w = self.widgets[name]
            if isinstance(w, (QLineEdit, QTextEdit, QDateEdit)):
                self._mark_error(w, False)

        for field in self.schema.get("fields", []):
            if not field.get("required"):
                continue
            name = field["name"]
            label = field.get("label", name)
            w = self.widgets[name]
            f_type = field.get("type", "text")
            is_missing = False

            if f_type in ("text",):
                is_missing = not w.text().strip()
            elif f_type == "textarea":
                is_missing = not w.toPlainText().strip()
            elif f_type == "date":
                is_missing = not w.date().isValid()
            elif f_type == "signature":
                if hasattr(w, "isEmpty"):
                    is_missing = w.isEmpty()

            if is_missing:
                missing_labels.append(label)
                if isinstance(w, (QLineEdit, QTextEdit, QDateEdit)):
                    self._mark_error(w, True)

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

        template_id = str(self.schema.get("template_id", "default"))
        primary_sig_path = next(iter(sig_map.values())) if sig_map else None

        self.pdf_generator(data, primary_sig_path, template_id)

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

    # ---------- COMPAT LAYER ----------
    @staticmethod
    def build(
        main_window,
        schema: Dict[str, Any],
        pdf_generator: Optional[Callable[[Dict[str, Any], Optional[str], str], None]] = None
    ) -> QWidget:
        """
        Compatibility with code that expects FormFactory.build(...).
        Returns a ready-to-use QWidget instance.
        """
        return FormFactory(main_window, schema, pdf_generator)
