# theme.py
from PyQt5.QtWidgets import QApplication

BASE_QSS = """
/* ---------- Global ---------- */
* {
  font-family: "Inter", "Segoe UI", "Arial";
  font-size: 14px;
}
QWidget#AppRoot {
  background: #0B0C0F; /* page bg */
  color: #91beeb;
}

/* ---------- Form container ---------- */
QWidget#FormRoot {
  background: #bde0f2;
  border: 1px solid #262B36;
  border-radius: 14px;
}

/* ---------- Labels ---------- */
QLabel[role="title"] {
  font-size: 80px;
  font-weight: 1000;
  margin: 8px 0 2px 0;
}
QLabel[role="description"] {
  color: #080d14;
  line-height: 1.3;
  margin-bottom: 8px;
}
QLabel[role="field-label"] {
  color: #C9D1E0;
  margin: 6px 0 2px 0;
}

/* ---------- Inputs ---------- */
QLineEdit, QTextEdit, QDateEdit {
  background: #dde1ed;
  border: 1px solid #b3c4e6;
  border-radius: 10px;
  padding: 8px 10px;
}
QTextEdit { padding: 10px; min-height: 90px; }
QLineEdit:focus, QTextEdit:focus, QDateEdit:focus {
  border: 1px solid #080d14;
  outline: none;
}
QLineEdit[state="error"], QTextEdit[state="error"], QDateEdit[state="error"] {
  border: 1px solid #FF5C7A;
  background: #1A0E12;
}

/* ---------- Buttons ---------- */
QPushButton {
  border-radius: 12px;
  padding: 10px 14px;
  font-weight: 600;
  border: 1px solid transparent;
}
QPushButton[variant="primary"] {
  background: #4F8BFF;
  color: #0B0C0F;
}
QPushButton[variant="primary"]:hover { background: #6CA0FF; }

QPushButton[variant="secondary"] {
  background: #151A22;
  color: #D6DBE6;
  border: 1px solid #2B3140;
}
QPushButton[variant="secondary"]:hover { background: #1B212C; }

QPushButton[variant="danger"] {
  background: #FF5C7A;
  color: #0B0C0F;
}

/* ---------- SignaturePad (if it’s a QWidget) ---------- */
QWidget[role="signature"] {
  background: #0D0F14;
  border: 1px dashed #3A4252;
  border-radius: 10px;
  min-height: 140px;
}

/* ---------- ScrollArea polish ---------- */
QScrollArea { border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }
"""

def apply_theme(app: QApplication, extra_qss: str = ""):
    app.setStyleSheet(BASE_QSS + "\n" + (extra_qss or ""))
