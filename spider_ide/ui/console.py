from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QTextEdit, QPushButton, QLabel, QFrame
)
from PyQt6.QtGui import QTextCharFormat, QColor, QFont, QTextCursor
from PyQt6.QtCore import Qt

from spider_ide.ui.style_kit import DARK_THEME, mono


class Console(QWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.theme = DARK_THEME
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.notebook = QTabWidget()
        self.notebook.setTabsClosable(False)
        self.notebook.setMovable(False)
        layout.addWidget(self.notebook)
        
        self.output_frame = QWidget()
        output_layout = QVBoxLayout(self.output_frame)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(0)
        
        self.btn_frame = QFrame()
        btn_layout = QHBoxLayout(self.btn_frame)
        btn_layout.setContentsMargins(8, 4, 8, 4)
        btn_layout.addStretch()
        
        self.clear_btn = QPushButton("CLEAR")
        self.clear_btn.setFont(mono(10, bold=True, spacing=1))
        self.clear_btn.clicked.connect(self.clear_output)
        btn_layout.addWidget(self.clear_btn)
        output_layout.addWidget(self.btn_frame)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(mono(12))
        output_layout.addWidget(self.output_text)
        self.notebook.addTab(self.output_frame, "OUTPUT")
        
        self.problems_frame = QWidget()
        problems_layout = QVBoxLayout(self.problems_frame)
        problems_layout.setContentsMargins(0, 0, 0, 0)
        problems_layout.setSpacing(0)
        
        self.problems_text = QTextEdit()
        self.problems_text.setReadOnly(True)
        self.problems_text.setFont(mono(12))
        problems_layout.addWidget(self.problems_text)
        self.notebook.addTab(self.problems_frame, "PROBLEMS")
        
        self.errors = []
        self.formats = {}
        self.apply_theme()
    
    def apply_theme(self, theme=None):
        if theme is None:
            theme = DARK_THEME
        self.theme = theme
        

        self.setStyleSheet(f"QWidget {{ background-color: {theme['bg']}; }}")
        
        self.notebook.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {theme['bg']}; /* Фон области вывода */
                border-top: 1px solid {theme['border']};
            }}
            QTabBar::tab {{
                background-color: {theme['surface']}; /* Неактивные вкладки */
                color: {theme['text_secondary']};
                padding: 6px 16px;
                border: none;
                border-right: 1px solid {theme['border']};
                font-family: "Consolas", monospace;
                font-size: 11px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background-color: {theme['bg']}; /* Активная сливается с контентом */
                color: {theme['text']};
                border-bottom: 2px solid {theme['accent']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {theme['bg']};
                color: {theme['text']};
            }}
        """)
        
        if hasattr(self, 'btn_frame'):
            self.btn_frame.setStyleSheet(f"QFrame {{ background-color: {theme['bg']}; border-bottom: 1px solid {theme['border']}; }}")
        
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {theme['text_secondary']};
                border: 1px solid {theme['border']};
                padding: 4px 12px;
                border-radius: 0px;
                font-family: "Consolas", monospace;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {theme['accent']};
                color: {theme['bg']};
                border-color: {theme['accent']};
            }}
            QPushButton:pressed {{
                background-color: {theme['accent_hover']};
                color: {theme['bg']};
            }}
        """)
        
        self.output_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme['bg']};
                color: {theme['text']};
                border: none;
                padding: 8px;
                selection-background-color: {theme['accent']};
                selection-color: {theme['bg']};
                font-family: "Consolas", monospace;
                font-size: 12px;
            }}
            QScrollBar:vertical {{
                background-color: {theme['bg']};
                width: 10px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {theme['border']};
                min-height: 20px;
                border-radius: 0px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme['text_secondary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        
        self.problems_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme['bg']};
                color: {theme['text']};
                border: none;
                padding: 8px;
                font-family: "Consolas", monospace;
                font-size: 12px;
            }}
            QScrollBar:vertical {{
                background-color: {theme['bg']};
                width: 10px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {theme['border']};
                min-height: 20px;
                border-radius: 0px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme['text_secondary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        
        self.formats = {
            'normal': self._create_format(theme['text']),
            'error': self._create_format(theme.get('error', '#ef4444')),
            'success': self._create_format(theme.get('success', '#4ade80')),
            'warning': self._create_format(theme.get('warning', '#fbbf24')),
            'info': self._create_format(theme['text_secondary']),
        }
        
        if self.errors:
            self.update_problems()


    
    def _create_format(self, color_hex):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color_hex))
        fmt.setFont(mono(12))
        return fmt
    
    def write(self, text, tag=None):
        fmt = self.formats.get(tag, self.formats['normal'])
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text, fmt)
        self.output_text.setTextCursor(cursor)
        self.output_text.verticalScrollBar().setValue(self.output_text.verticalScrollBar().maximum())
    
    def add_error(self, line, message):
        self.errors.append({'line': line, 'message': message})
        self.update_problems()
        
    def clear_errors(self):
        self.errors = []
        self.update_problems()
        
    def update_problems(self):
        self.problems_text.clear()
        theme = self.theme
        
        if self.errors:
            header_fmt = self._create_format(theme.get('error', '#ef4444'))
            cursor = self.problems_text.textCursor()
            cursor.insertText(f" {len(self.errors)} ERRORS:\n\n", header_fmt)
            
            error_fmt = self._create_format(theme.get('error', '#ef4444'))
            for err in self.errors:
                cursor.insertText(f"LINE {err['line']}: {err['message']}\n", error_fmt)
        else:
            success_fmt = self._create_format(theme.get('success', '#4ade80'))
            cursor = self.problems_text.textCursor()
            cursor.insertText(" NO PROBLEMS FOUND.\n", success_fmt)
            
    def clear_output(self):
        self.output_text.clear()
        
    def clear(self):
        self.clear_output()
        self.clear_errors() 