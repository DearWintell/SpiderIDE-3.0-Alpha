from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QWidget, QCheckBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor

import os
import re

from spider_ide.ui.style_kit import DARK_THEME, mono, outline_button


class ProjectSearchDialog(QDialog):
    file_open_requested = pyqtSignal(str, int)
    
    def __init__(self, parent=None, project_path=None, theme=None):
        super().__init__(parent)
        self.setWindowTitle("PROJECT SEARCH")
        self.setMinimumSize(700, 500)
        self.resize(800, 550)
        self.project_path = project_path
        self.theme = DARK_THEME
        self.results = []
        
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)
        self.search_timer.timeout.connect(self.perform_search)
        
        self.setup_ui()
        self.apply_theme()
        
        if self.project_path:
            self.path_label.setText(f"PROJECT: {self.project_path}")
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        header_label = QLabel("// SEARCH IN PROJECT")
        header_label.setFont(mono(14, bold=True, spacing=2))
        header_label.setStyleSheet(f"color: {self.theme['text_secondary']}; background: transparent;")
        layout.addWidget(header_label)
        
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("SEARCH TEXT...")
        self.search_input.setFont(mono(12))
        self.search_input.returnPressed.connect(self.perform_search)
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input, 1)
        
        search_btn = outline_button("SEARCH", self.theme, compact=True)
        search_btn.setFixedWidth(100)
        search_btn.clicked.connect(self.perform_search)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        options_layout = QHBoxLayout()
        options_layout.setSpacing(20)
        
        self.case_sensitive_cb = QCheckBox("MATCH CASE")
        self.case_sensitive_cb.setFont(mono(10, bold=True, spacing=1))
        options_layout.addWidget(self.case_sensitive_cb)
        
        self.regex_cb = QCheckBox("USE REGEX")
        self.regex_cb.setFont(mono(10, bold=True, spacing=1))
        options_layout.addWidget(self.regex_cb)
        
        self.path_label = QLabel("NO PROJECT OPENED")
        self.path_label.setFont(mono(10))
        self.path_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
        options_layout.addWidget(self.path_label, 1)
        
        self.results_count_label = QLabel("")
        self.results_count_label.setFont(mono(10, bold=True))
        options_layout.addWidget(self.results_count_label)
        
        layout.addLayout(options_layout)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)
        
        self.results_list = QListWidget()
        self.results_list.setFont(mono(12))
        self.results_list.itemDoubleClicked.connect(self.on_result_double_click)
        layout.addWidget(self.results_list, 1)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = outline_button("CLOSE", self.theme, compact=True)
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def apply_theme(self):
        theme = self.theme
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme['bg']};
                border: 1px solid {theme['border']};
            }}
            QLabel {{
                color: {theme['text']};
                background: transparent;
            }}
            QLineEdit {{
                background-color: {theme['surface']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                border-radius: 0px;
                padding: 6px 10px;
            }}
            QLineEdit:focus {{
                border: 1px solid {theme['accent']};
            }}
            QCheckBox {{
                color: {theme['text']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border: 1px solid {theme['border']};
                border-radius: 0px;
                background-color: {theme['surface']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {theme['accent']};
                border: 1px solid {theme['accent']};
            }}
            QFrame {{
                background-color: {theme['border']};
                max-height: 1px;
            }}
            QListWidget {{
                background-color: {theme['surface']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                border-radius: 0px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 4px 8px;
                border-bottom: 1px solid {theme['border']};
            }}
            QListWidget::item:hover {{
                background-color: {theme['bg']};
            }}
            QListWidget::item:selected {{
                background-color: {theme['accent']};
                color: {theme['bg']};
            }}
        """)
    
    def set_theme(self, theme):
        self.theme = theme
        self.apply_theme()
    
    def on_search_changed(self, text):
        if len(text) >= 2:
            self.search_timer.start()
        else:
            self.results_list.clear()
            self.results_count_label.setText("")
    
    def perform_search(self):
        query = self.search_input.text().strip()
        if not query:
            return
        
        if not self.project_path or not os.path.isdir(self.project_path):
            self.results_count_label.setText("NO PROJECT OPENED")
            return
        
        self.results_list.clear()
        self.results = []
        
        case_sensitive = self.case_sensitive_cb.isChecked()
        use_regex = self.regex_cb.isChecked()
        
        try:
            pattern = re.compile(query if use_regex else re.escape(query),
                               re.IGNORECASE if not case_sensitive else 0)
        except re.error as e:
            self.results_count_label.setText(f"INVALID REGEX: {e}")
            return
        
        total_matches = 0
        files_with_matches = 0
        
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'build']
            
            for file in files:
                if not file.endswith('.spider'):
                    continue
                
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    file_matches = []
                    for line_num, line in enumerate(lines, 1):
                        if pattern.search(line):
                            file_matches.append((line_num, line.rstrip()))
                    
                    if file_matches:
                        files_with_matches += 1
                        total_matches += len(file_matches)
                        
                        rel_path = os.path.relpath(file_path, self.project_path)
                        file_item = QListWidgetItem(f"// {rel_path.upper()} ({len(file_matches)} MATCHES)")
                        file_item.setForeground(QColor(self.theme['text_secondary']))
                        file_item.setFont(mono(11, bold=True))
                        file_item.setData(Qt.ItemDataRole.UserRole, None)
                        self.results_list.addItem(file_item)
                        
                        for line_num, line_text in file_matches:
                            display_text = f"  {line_num}: {line_text}"
                            result_item = QListWidgetItem(display_text)
                            result_item.setForeground(QColor(self.theme['text']))
                            result_item.setFont(mono(11))
                            result_item.setData(Qt.ItemDataRole.UserRole, (file_path, line_num))
                            self.results_list.addItem(result_item)
                            self.results.append((file_path, line_num))
                
                except Exception:
                    pass
        
        self.results_count_label.setText(f"{total_matches} MATCHES IN {files_with_matches} FILES")
    
    def on_result_double_click(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            file_path, line_num = data
            self.file_open_requested.emit(file_path, line_num)
            self.accept()
    
    def set_project_path(self, project_path):
        self.project_path = project_path
        if project_path:
            self.path_label.setText(f"PROJECT: {project_path}")
        else:
            self.path_label.setText("NO PROJECT OPENED") 