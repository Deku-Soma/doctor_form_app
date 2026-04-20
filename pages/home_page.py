from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QLineEdit, QScrollArea, QFrame, QDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QPalette
import os
from pages.form_card import FormCard
from pages.employee_selector import EmployeeSelectorDialog


class HeaderSection(QFrame):
    """Header section with logo background"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HeaderSection")
        
        # Load background image
        logo_path = os.path.join(os.getcwd(), "themes", "Logo.png")
        self.background_pixmap = QPixmap(logo_path) if os.path.exists(logo_path) else None
        
        # Set fixed height for header
        self.setMinimumHeight(120)
        self.setMaximumHeight(150)
        
    def paintEvent(self, event):
        """Draw logo as background"""
        painter = QPainter(self)
        
        # Fill with a base color first
        painter.fillRect(self.rect(), QColor("#163b4d"))
        
        if self.background_pixmap:
            # Scale to fit width, maintaining aspect ratio
            scaled = self.background_pixmap.scaledToHeight(
                self.height(), 
                Qt.SmoothTransformation
            )
            # Center horizontally
            x = (self.width() - scaled.width()) // 2
            painter.drawPixmap(x, 0, scaled)
        
        super().paintEvent(event)


class FormsSection(QFrame):
    """Forms section with dark grey background"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FormsSection")
        self.setStyleSheet("""
            QFrame#FormsSection {
                background-color: #2d2d2d;
                border: none;
            }
        """)


class HomePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.user = None
        self.all_cards = []  # Store all cards for search functionality
        self.init_ui()

    def init_ui(self):
        # Main layout - no margins, sections fill the space
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === HEADER SECTION (Logo Background) ===
        self.header_section = HeaderSection()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 20, 20, 20)
        
        # Welcome label
        self.welcome_label = QLabel("Welcome!")
        welcome_font = QFont()
        welcome_font.setPointSize(24)
        welcome_font.setBold(True)
        self.welcome_label.setFont(welcome_font)
        self.welcome_label.setStyleSheet("color: #ffffff; background: transparent;")
        
        header_layout.addWidget(self.welcome_label)
        header_layout.addStretch()
        
        # Management buttons
        companies_btn = QPushButton("🏢 Companies")
        companies_btn.setStyleSheet("""
            QPushButton {
                background-color: #1abc9c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #16a085;
            }
        """)
        companies_btn.clicked.connect(lambda: self.main_window.show_page("companies"))
        header_layout.addWidget(companies_btn)
        
        employees_btn = QPushButton("👥 Employees")
        employees_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        employees_btn.clicked.connect(lambda: self.main_window.show_page("employees"))
        header_layout.addWidget(employees_btn)
        
        # Pending Review button
        pending_btn = QPushButton("📋 Pending Review")
        pending_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        pending_btn.clicked.connect(lambda: self.main_window.show_page("pending_review"))
        header_layout.addWidget(pending_btn)
        
        # Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.setMaximumWidth(100)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #163b4d;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        logout_btn.clicked.connect(self.logout)
        header_layout.addWidget(logout_btn)
        
        self.header_section.setLayout(header_layout)
        main_layout.addWidget(self.header_section)

        # === FORMS SECTION (Dark Grey Background) ===
        self.forms_section = FormsSection()
        forms_layout = QVBoxLayout()
        forms_layout.setContentsMargins(20, 20, 20, 20)
        forms_layout.setSpacing(20)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search forms...")
        self.search_input.textChanged.connect(self.filter_cards)
        self.search_input.setMaximumWidth(400)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #3d3d3d;
                border: 1px solid #4d4d4d;
                border-radius: 6px;
                padding: 10px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 2px solid #163b4d;
            }
        """)
        search_layout.addWidget(self.search_input)
        search_layout.addStretch()
        forms_layout.addLayout(search_layout)
        
        # Scrollable content for cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("background: transparent; border: none;")
        
        # Content widget for cards
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout()
        content_layout.setSpacing(30)
        
        # Add form categories
        content_layout.addLayout(self.create_consent_forms_section())
        content_layout.addLayout(self.create_questionnaires_section())
        content_layout.addLayout(self.create_certificates_section())
        content_layout.addStretch()
        
        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        
        forms_layout.addWidget(scroll_area)
        self.forms_section.setLayout(forms_layout)
        main_layout.addWidget(self.forms_section, 1)  # Take remaining space
        
        self.setLayout(main_layout)

    def create_consent_forms_section(self):
        """Create Consent Forms category"""
        section_layout = QVBoxLayout()
        section_layout.setSpacing(15)
        
        # Category header
        header = QLabel("🩺 Consent Forms")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setStyleSheet("color: #ffffff; background: transparent;")
        section_layout.addWidget(header)
        
        # Grid for cards
        grid = QGridLayout()
        grid.setSpacing(20)
        
        # Define forms
        forms = [
            ("💉", "Drug Testing", "Workplace drug testing consent", "FormDrugTesting"),
            ("💊", "Vitamin B", "Vitamin B consent form", "FormVitaminB"),
            ("📋", "Complete Wellbeing", "Complete wellbeing assessment", "FormCompleteWellbeing"),
        ]
        
        # Add cards to grid (3 per row)
        for idx, (icon, title, desc, page_name) in enumerate(forms):
            card = FormCard(icon, title, desc)
            card.clicked.connect(lambda pn=page_name, t=title: self.open_form_with_selector(pn, t))
            self.all_cards.append((card, title.lower()))
            
            row = idx // 3
            col = idx % 3
            grid.addWidget(card, row, col)
        
        section_layout.addLayout(grid)
        return section_layout

    def create_questionnaires_section(self):
        """Create Health Questionnaires category"""
        section_layout = QVBoxLayout()
        section_layout.setSpacing(15)
        
        # Category header
        header = QLabel("📝 Health Questionnaires")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setStyleSheet("color: #ffffff; background: transparent;")
        section_layout.addWidget(header)
        
        # Grid for cards
        grid = QGridLayout()
        grid.setSpacing(20)
        
        # Define forms
        forms = [
            ("🏔️", "Heights", "Heights questionnaire", "FormHeightsQuestionnaire"),
            ("🌡️", "Hot/Cold Exposure", "Temperature exposure assessment", "FormHotColdExposure"),
            ("🏗️", "Confined Spaces", "Confined spaces questionnaire", "FormConfinedSpaces"),
            ("🦴", "Musculoskeletal", "Musculoskeletal assessment", "FormMusculoskeletal"),
            ("🧠", "Psychology (K10)", "Psychological assessment", "FormPsychology"),
        ]
        
        # Add cards to grid (3 per row)
        for idx, (icon, title, desc, page_name) in enumerate(forms):
            card = FormCard(icon, title, desc)
            card.clicked.connect(lambda pn=page_name, t=title: self.open_form_with_selector(pn, t))
            self.all_cards.append((card, title.lower()))
            
            row = idx // 3
            col = idx % 3
            grid.addWidget(card, row, col)
        
        section_layout.addLayout(grid)
        return section_layout

    def create_certificates_section(self):
        """Create Certificates & Referrals category"""
        section_layout = QVBoxLayout()
        section_layout.setSpacing(15)
        
        # Category header
        header = QLabel("📜 Certificates & Referrals")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setStyleSheet("color: #ffffff; background: transparent;")
        section_layout.addWidget(header)
        
        # Grid for cards
        grid = QGridLayout()
        grid.setSpacing(20)
        
        # Define forms
        forms = [
            ("📄", "Certificate of Fitness", "Medical fitness certificate", "FormCertificateFitness"),
            ("🏥", "CWB Medical Referral", "CWB referral form", "FormCWBReferral"),
            ("📋", "Annexure 3", "Construction certificate", "FormAnnexure3"),
        ]
        
        # Add cards to grid (3 per row)
        for idx, (icon, title, desc, page_name) in enumerate(forms):
            card = FormCard(icon, title, desc)
            card.clicked.connect(lambda pn=page_name, t=title: self.open_form_with_selector(pn, t))
            self.all_cards.append((card, title.lower()))
            
            row = idx // 3
            col = idx % 3
            grid.addWidget(card, row, col)
        
        section_layout.addLayout(grid)
        return section_layout

    def filter_cards(self, search_text):
        """Filter cards based on search text"""
        search_text = search_text.lower()
        
        for card, card_title in self.all_cards:
            if search_text in card_title:
                card.show()
            else:
                card.hide()

    def set_user(self):
        """Update welcome message with user info"""
        self.user = self.main_window.fetch_session()
        if self.user:
            user_name = self.user.get('user_name', 'User')
            self.welcome_label.setText(f"Welcome, {user_name}!")
        else:
            self.welcome_label.setText("Welcome!")

    def logout(self):
        """Handle logout"""
        self.main_window.go_to_login()
    
    def open_form_with_selector(self, page_name, form_title):
        """Show employee selector then open form with employee data."""
        dialog = EmployeeSelectorDialog(self, form_title)
        if dialog.exec_() == QDialog.Accepted:
            employee = dialog.get_selected_employee()
            if employee:
                # Store selected employee for the form to use
                self.main_window.selected_employee = employee
                self.main_window.go_to_page(page_name)
