# form_card.py
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class FormCard(QFrame):
    """
    A modern card widget for displaying form options.
    Uses QFrame for better stylesheet control.
    Features: icon, title, description, hover effects
    """
    clicked = pyqtSignal()
    
    def __init__(self, icon, title, description="", parent=None):
        super().__init__(parent)
        self.icon = icon
        self.title = title
        self.description = description
        self.init_ui()
        
    def init_ui(self):
        # Set object name for styling
        self.setObjectName("FormCard")
        
        # Set frame style for a visible card effect
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        
        # Apply teal background directly
        self._apply_default_style()
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Icon label (emoji)
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet("color: white; background-color: transparent; border: none;")
        icon_font = QFont()
        icon_font.setPointSize(32)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignCenter)
        
        # Title label
        title_label = QLabel(self.title)
        title_label.setStyleSheet("color: white; background-color: transparent; border: none;")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        
        # Description label (optional)
        if self.description:
            desc_label = QLabel(self.description)
            desc_label.setStyleSheet("color: #e0e0e0; background-color: transparent; border: none;")
            desc_font = QFont()
            desc_font.setPointSize(9)
            desc_label.setFont(desc_font)
            desc_label.setAlignment(Qt.AlignCenter)
            desc_label.setWordWrap(True)
        
        # Add widgets to layout
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        if self.description:
            layout.addWidget(desc_label)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Set fixed height for consistency
        self.setMinimumHeight(140)
        self.setMaximumHeight(160)
        
        # Enable mouse tracking for hover effects
        self.setCursor(Qt.PointingHandCursor)
    
    def _apply_default_style(self):
        """Apply teal background"""
        self.setStyleSheet("""
            QFrame#FormCard {
                background-color: #163b4d;
                border: 2px solid #163b4d;
                border-radius: 12px;
            }
        """)
    
    def _apply_hover_style(self):
        """Apply purple hover background"""
        self.setStyleSheet("""
            QFrame#FormCard {
                background-color: #685070;
                border: 2px solid #685070;
                border-radius: 12px;
            }
        """)
        
    def mousePressEvent(self, event):
        """Handle click events"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
        
    def enterEvent(self, event):
        """Add hover effect - change to purple"""
        self._apply_hover_style()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Remove hover effect - back to teal"""
        self._apply_default_style()
        super().leaveEvent(event)
