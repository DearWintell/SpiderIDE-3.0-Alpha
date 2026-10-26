from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSpinBox, QCheckBox, QPushButton, QFormLayout,
    QLineEdit, QFileDialog, QTabWidget, QWidget, QFrame
)
from PyQt6.QtCore import Qt

from spider_ide.ui.style_kit import mono, outline_button


class SettingsDialog(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.config = main_window.config
        self.theme = main_window.theme
        
        self.setWindowTitle("SETTINGS")
        self.setFixedSize(600, 600)
        
        t = self.theme
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {t['bg']};
                color: {t['text']};
            }}
            QTabWidget::pane {{
                border: none;
                background-color: transparent;
                border-top: 1px solid {t['border']};
            }}
            QTabBar::tab {{
                background-color: transparent;
                color: {t['text_secondary']};
                padding: 12px 24px;
                border: none;
                border-bottom: 1px solid transparent;
                font-family: "Consolas", monospace;
                font-size: 11px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                color: {t['text']};
                border-bottom: 1px solid {t['accent']};
            }}
            QTabBar::tab:hover:!selected {{
                color: {t['text']};
            }}
            QComboBox, QSpinBox, QLineEdit {{
                background-color: {t['surface']};
                color: {t['text']};
                border: 1px solid {t['border']};
                padding: 6px 10px;
                border-radius: 0px;
                font-family: "Consolas", monospace;
                font-size: 12px;
            }}
            QComboBox:hover, QSpinBox:hover, QLineEdit:hover {{
                border: 1px solid {t['accent']};
            }}
            QComboBox:focus, QSpinBox:focus, QLineEdit:focus {{
                border: 1px solid {t['accent']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {t['surface']};
                color: {t['text']};
                border: 1px solid {t['border']};
                selection-background-color: {t['accent']};
                selection-color: {t['bg']};
            }}
            QCheckBox {{
                color: {t['text']};
                spacing: 10px;
                font-family: "Consolas", monospace;
                font-size: 12px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border: 1px solid {t['border']};
                background-color: {t['surface']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {t['accent']};
                border: 1px solid {t['accent']};
            }}
            QCheckBox::indicator:hover {{
                border: 1px solid {t['accent']};
            }}
            QLabel {{
                color: {t['text']};
                font-family: "Consolas", monospace;
                font-size: 12px;
            }}
        """)
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        t = self.theme
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        header_label = QLabel("// SETTINGS")
        header_label.setFont(mono(14, bold=True, spacing=2))
        header_label.setStyleSheet(f"color: {t['text_secondary']}; background: transparent;")
        layout.addWidget(header_label)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {t['border']}; max-height: 1px;")
        layout.addWidget(line)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        self.tabs.addTab(self.create_appearance_tab(), "APPEARANCE")
        self.tabs.addTab(self.create_editor_tab(), "EDITOR")
        self.tabs.addTab(self.create_ide_tab(), "IDE")
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        cancel_btn = outline_button("CANCEL", t, compact=True)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = outline_button("APPLY", t, compact=True)
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        save_btn = outline_button("SAVE && CLOSE", t, compact=True)
        save_btn.clicked.connect(self.save_and_close)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def create_appearance_tab(self):
        t = self.theme
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        theme_group = QWidget()
        theme_layout = QFormLayout(theme_group)
        theme_layout.setSpacing(12)
        
        theme_label = QLabel("COLOR THEME:")
        theme_label.setFont(mono(10, bold=True, spacing=1))
        theme_label.setStyleSheet(f"color: {t['text_secondary']};")
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["BRUTALIST DARK", "BRUTALIST LIGHT"])
        self.theme_combo.setFont(mono(11))
        theme_layout.addRow(theme_label, self.theme_combo)
        
        layout.addWidget(theme_group)
        
        font_group = QWidget()
        font_layout = QFormLayout(font_group)
        font_layout.setSpacing(12)
        
        font_family_label = QLabel("FONT FAMILY:")
        font_family_label.setFont(mono(10, bold=True, spacing=1))
        font_family_label.setStyleSheet(f"color: {t['text_secondary']};")
        
        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems([
            "Consolas", "Courier New", "Monaco", "DejaVu Sans Mono",
            "Fira Code", "JetBrains Mono", "Source Code Pro"
        ])
        self.font_family_combo.setFont(mono(11))
        font_layout.addRow(font_family_label, self.font_family_combo)
        
        font_size_label = QLabel("FONT SIZE:")
        font_size_label.setFont(mono(10, bold=True, spacing=1))
        font_size_label.setStyleSheet(f"color: {t['text_secondary']};")
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 32)
        self.font_size_spin.setSuffix(" PT")
        self.font_size_spin.setFont(mono(11))
        font_layout.addRow(font_size_label, self.font_size_spin)
        
        layout.addWidget(font_group)
        
        layout.addStretch()
        return widget
    
    def create_editor_tab(self):
        t = self.theme
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        indent_group = QWidget()
        indent_layout = QFormLayout(indent_group)
        indent_layout.setSpacing(12)
        
        tab_size_label = QLabel("TAB SIZE:")
        tab_size_label.setFont(mono(10, bold=True, spacing=1))
        tab_size_label.setStyleSheet(f"color: {t['text_secondary']};")
        
        self.tab_size_spin = QSpinBox()
        self.tab_size_spin.setRange(2, 8)
        self.tab_size_spin.setFont(mono(11))
        indent_layout.addRow(tab_size_label, self.tab_size_spin)
        
        self.use_spaces_check = QCheckBox("INSERT SPACES INSTEAD OF TABS")
        self.use_spaces_check.setFont(mono(11))
        indent_layout.addRow(self.use_spaces_check)
        
        layout.addWidget(indent_group)
        
        behavior_group = QWidget()
        behavior_layout = QVBoxLayout(behavior_group)
        behavior_layout.setSpacing(12)
        
        self.auto_close_brackets_check = QCheckBox("AUTO-CLOSE BRACKETS AND QUOTES")
        self.auto_close_brackets_check.setFont(mono(11))
        behavior_layout.addWidget(self.auto_close_brackets_check)
        
        self.auto_indent_check = QCheckBox("AUTO-INDENT ON NEW LINE")
        self.auto_indent_check.setFont(mono(11))
        behavior_layout.addWidget(self.auto_indent_check)
        
        self.show_minimap_check = QCheckBox("SHOW MINIMAP")
        self.show_minimap_check.setFont(mono(11))
        behavior_layout.addWidget(self.show_minimap_check)
        
        self.show_line_numbers_check = QCheckBox("SHOW LINE NUMBERS")
        self.show_line_numbers_check.setFont(mono(11))
        behavior_layout.addWidget(self.show_line_numbers_check)
        
        layout.addWidget(behavior_group)
        
        layout.addStretch()
        return widget
    
    def create_ide_tab(self):
        t = self.theme
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        general_group = QWidget()
        general_layout = QVBoxLayout(general_group)
        general_layout.setSpacing(12)
        
        self.auto_save_check = QCheckBox("AUTO-SAVE FILES ON CHANGE")
        self.auto_save_check.setFont(mono(11))
        general_layout.addWidget(self.auto_save_check)
        
        self.restore_session_check = QCheckBox("RESTORE PREVIOUS SESSION ON STARTUP")
        self.restore_session_check.setFont(mono(11))
        general_layout.addWidget(self.restore_session_check)
        
        self.animations_check = QCheckBox("ENABLE ANIMATIONS")
        self.animations_check.setFont(mono(11))
        general_layout.addWidget(self.animations_check)
        
        layout.addWidget(general_group)
        
        interpreter_group = QWidget()
        interpreter_layout = QHBoxLayout(interpreter_group)
        interpreter_layout.setSpacing(12)
        
        interpreter_label = QLabel("SPIDER INTERPRETER PATH:")
        interpreter_label.setFont(mono(10, bold=True, spacing=1))
        interpreter_label.setStyleSheet(f"color: {t['text_secondary']};")
        
        self.interpreter_path = QLineEdit()
        self.interpreter_path.setPlaceholderText("PATH TO SPIDER INTERPRETER...")
        self.interpreter_path.setFont(mono(11))
        interpreter_layout.addWidget(interpreter_label)
        interpreter_layout.addWidget(self.interpreter_path)
        
        browse_btn = outline_button("BROWSE", t, compact=True)
        browse_btn.clicked.connect(self.browse_interpreter)
        interpreter_layout.addWidget(browse_btn)
        
        layout.addWidget(interpreter_group)
        
        layout.addStretch()
        return widget
    
    def browse_interpreter(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Spider Interpreter", "",
            "Executables (*.exe);;All Files (*)"
        )
        if path:
            self.interpreter_path.setText(path)
    
    def load_settings(self):
        config = self.config
        
        theme_name = config.get('theme', 'brutal')
        self.theme_combo.setCurrentIndex(0 if theme_name == 'brutal' else 1)
        
        self.font_family_combo.setCurrentText(config.get('font_family', 'Consolas'))
        self.font_size_spin.setValue(config.get('font_size', 14))
        
        self.tab_size_spin.setValue(config.get('tab_size', 4))
        self.use_spaces_check.setChecked(config.get('use_spaces', True))
        self.auto_close_brackets_check.setChecked(config.get('auto_close_brackets', True))
        self.auto_indent_check.setChecked(config.get('auto_indent', True))
        self.show_minimap_check.setChecked(config.get('show_minimap', True))
        self.show_line_numbers_check.setChecked(config.get('show_line_numbers', True))
        
        self.auto_save_check.setChecked(config.get('auto_save_enabled', False))
        self.restore_session_check.setChecked(config.get('restore_session', True))
        self.animations_check.setChecked(config.get('animations', True))
        self.interpreter_path.setText(config.get('interpreter_path', ''))
    
    def apply_settings(self):
        self.save_to_config()
        self.main_window.apply_theme()
        self.main_window.apply_editor_settings()
    
    def save_to_config(self):
        config = self.config
        
        theme_name = 'brutal' if self.theme_combo.currentIndex() == 0 else 'light'
        config.set('theme', theme_name)
        
        config.set('font_family', self.font_family_combo.currentText())
        config.set('font_size', self.font_size_spin.value())
        
        config.set('tab_size', self.tab_size_spin.value())
        config.set('use_spaces', self.use_spaces_check.isChecked())
        config.set('auto_close_brackets', self.auto_close_brackets_check.isChecked())
        config.set('auto_indent', self.auto_indent_check.isChecked())
        config.set('show_minimap', self.show_minimap_check.isChecked())
        config.set('show_line_numbers', self.show_line_numbers_check.isChecked())
        
        config.set('auto_save_enabled', self.auto_save_check.isChecked())
        config.set('restore_session', self.restore_session_check.isChecked())
        config.set('animations', self.animations_check.isChecked())
        config.set('interpreter_path', self.interpreter_path.text())
    
    def save_and_close(self):
        self.save_to_config()
        self.main_window.apply_theme()
        self.main_window.apply_editor_settings()
        self.accept() 