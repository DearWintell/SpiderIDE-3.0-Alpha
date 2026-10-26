import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLabel, QFrame, QHBoxLayout
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon

from spider_ide.ui.style_kit import DARK_THEME, mono, outline_button, logo_label


class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("WELCOME")
        self.setFixedSize(520, 520)
        
        icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'little_logo.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {DARK_THEME['bg']};
                border: 1px solid {DARK_THEME['border']};
            }}
        """)
        
        self.setup_ui()
        self.animate_appearance()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(logo_label(DARK_THEME, size=13, spacing=2))
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        title_label = QLabel("WELCOME TO\nSPIDER IDE")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(mono(28, bold=True, spacing=4))
        title_label.setStyleSheet(f"color: {DARK_THEME['text']}; background: transparent;")
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("A MODERN IDE FOR SPIDER SCRIPT")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setFont(mono(10, spacing=2))
        subtitle_label.setStyleSheet(f"color: {DARK_THEME['text_secondary']}; background: transparent;")
        layout.addWidget(subtitle_label)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {DARK_THEME['border']}; max-height: 1px;")
        layout.addWidget(separator)
        
        self.open_file_btn = outline_button("OPEN FILE", DARK_THEME)
        self.open_file_btn.setFixedHeight(44)
        self.open_file_btn.clicked.connect(self.on_open_file)
        layout.addWidget(self.open_file_btn)
        
        self.open_project_btn = outline_button("OPEN PROJECT", DARK_THEME)
        self.open_project_btn.setFixedHeight(44)
        self.open_project_btn.clicked.connect(self.on_open_project)
        layout.addWidget(self.open_project_btn)
        
        self.new_project_btn = outline_button("CREATE NEW PROJECT", DARK_THEME)
        self.new_project_btn.setFixedHeight(44)
        self.new_project_btn.clicked.connect(self.on_new_project)
        layout.addWidget(self.new_project_btn)
        
        self.new_file_btn = outline_button("CREATE NEW FILE", DARK_THEME)
        self.new_file_btn.setFixedHeight(44)
        self.new_file_btn.clicked.connect(self.on_new_file)
        layout.addWidget(self.new_file_btn)
        
        self.guide_btn = QPushButton("GUIDE")
        self.guide_btn.setFont(mono(10, bold=True, spacing=1))
        self.guide_btn.setFixedHeight(44)
        self.guide_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DARK_THEME['accent']};
                color: {DARK_THEME['bg']};
                border: 1px solid {DARK_THEME['accent']};
                border-radius: 0px;
            }}
            QPushButton:hover {{
                background-color: {DARK_THEME['accent_hover']};
                border-color: {DARK_THEME['accent_hover']};
            }}
            QPushButton:pressed {{
                background-color: #999999;
            }}
        """)
        self.guide_btn.clicked.connect(self.on_guide)
        layout.addWidget(self.guide_btn)
        
        version_label = QLabel("SPIDER IDE v1.3 // PROJECT.EXE x SPIDER SCRIPT")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setFont(mono(9, spacing=1))
        version_label.setStyleSheet(f"color: {DARK_THEME['text_secondary']}; background: transparent;")
        layout.addWidget(version_label)
    
    def animate_appearance(self):
        self.setWindowOpacity(0.0)
        
        animation = QPropertyAnimation(self, b"windowOpacity")
        animation.setDuration(250)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()
        
        self._animation = animation
    
    def on_open_file(self):
        self.setResult(1)
        self.accept()
    
    def on_open_project(self):
        self.setResult(2)
        self.accept()
    
    def on_new_project(self):
        self.setResult(3)
        self.accept()
    
    def on_new_file(self):
        self.setResult(4)
        self.accept()
    
    def on_guide(self):
        from spider_ide.ui.help_dialog import HelpDialog
        dialog = HelpDialog(self)
        dialog.exec() 