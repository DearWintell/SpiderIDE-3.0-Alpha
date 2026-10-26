import os
import json
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QTreeWidget, QTreeWidgetItem, QFrame,
    QHeaderView, QWidget
)
from PyQt6.QtCore import Qt

from spider_ide.ui.style_kit import DARK_THEME, mono, outline_button


class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("NEW PROJECT")
        self.setFixedSize(600, 380)
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {DARK_THEME['bg']};
                border: 1px solid {DARK_THEME['border']};
            }}
            QLabel {{
                color: {DARK_THEME['text']};
                background: transparent;
            }}
            QLineEdit {{
                background-color: {DARK_THEME['surface']};
                color: {DARK_THEME['text']};
                border: 1px solid {DARK_THEME['border']};
                border-radius: 0px;
                padding: 8px 12px;
                font-family: "Consolas", monospace;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {DARK_THEME['accent']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        
        header_label = QLabel("// CREATE NEW PROJECT")
        header_label.setFont(mono(14, bold=True, spacing=2))
        header_label.setStyleSheet(f"color: {DARK_THEME['text_secondary']};")
        layout.addWidget(header_label)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {DARK_THEME['border']}; max-height: 1px;")
        layout.addWidget(line)
        
        name_label = QLabel("PROJECT NAME:")
        name_label.setFont(mono(10, bold=True, spacing=1))
        name_label.setStyleSheet(f"color: {DARK_THEME['text_secondary']};")
        layout.addWidget(name_label)
        
        self.name_entry = QLineEdit()
        self.name_entry.setText("MySpiderProject")
        self.name_entry.setFont(mono(12))
        layout.addWidget(self.name_entry)
        
        loc_label = QLabel("LOCATION:")
        loc_label.setFont(mono(10, bold=True, spacing=1))
        loc_label.setStyleSheet(f"color: {DARK_THEME['text_secondary']};")
        layout.addWidget(loc_label)
        
        loc_layout = QHBoxLayout()
        loc_layout.setSpacing(8)
        
        self.loc_entry = QLineEdit()
        self.loc_entry.setText(Dialogs.get_projects_folder())
        self.loc_entry.setFont(mono(12))
        loc_layout.addWidget(self.loc_entry, 1)
        
        browse_btn = outline_button("BROWSE", DARK_THEME, compact=True)
        browse_btn.clicked.connect(self.browse_location)
        loc_layout.addWidget(browse_btn)
        
        layout.addLayout(loc_layout)
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.setSpacing(12)
        
        create_btn = outline_button("CREATE PROJECT", DARK_THEME)
        create_btn.clicked.connect(self.create_project)
        btn_layout.addWidget(create_btn)
        
        cancel_btn = outline_button("CANCEL", DARK_THEME, compact=True)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.created_path = None
    
    def browse_location(self):
        path = QFileDialog.getExistingDirectory(self, "SELECT PROJECT LOCATION", "")
        if path:
            self.loc_entry.setText(path)
    
    def create_project(self):
        name = self.name_entry.text().strip()
        location = self.loc_entry.text().strip()
        
        if not name:
            QMessageBox.critical(self, "ERROR", "PROJECT NAME IS REQUIRED!")
            return
        
        project_path = os.path.join(location, name)
        
        try:
            os.makedirs(project_path, exist_ok=True)
            os.makedirs(os.path.join(project_path, "src"), exist_ok=True)
            os.makedirs(os.path.join(project_path, "assets"), exist_ok=True)
            os.makedirs(os.path.join(project_path, "build"), exist_ok=True)
            
            config = {
                "name": name,
                "version": "1.0.0",
                "main": "src/main.spider",
                "author": "",
                "created": str(Path(project_path).stat().st_ctime)
            }
            
            with open(os.path.join(project_path, "project.json"), "w") as f:
                json.dump(config, f, indent=4)
            
            main_file = os.path.join(project_path, "src", "main.spider")
            with open(main_file, "w", encoding="utf-8") as f:
                f.write('Spider(Start)\n\n')
                f.write(f'window(title="{name}" width=800 height=600 bg="#0a0a0a")\n\n')
                f.write('text(text="Hello Spider!" x=400 y=300 color="#ffffff" size=24)\n')
            
            self.created_path = project_path
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "ERROR", f"FAILED TO CREATE PROJECT:\n{str(e)}")


class OpenProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OPEN PROJECT")
        self.setMinimumSize(750, 520)
        self.resize(800, 560)
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {DARK_THEME['bg']};
                border: 1px solid {DARK_THEME['border']};
            }}
            QLabel {{
                color: {DARK_THEME['text']};
                background: transparent;
            }}
            QTreeWidget {{
                background-color: {DARK_THEME['surface']};
                color: {DARK_THEME['text']};
                border: 1px solid {DARK_THEME['border']};
                border-radius: 0px;
                font-family: "Consolas", monospace;
                font-size: 12px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 6px 8px;
                border-bottom: 1px solid {DARK_THEME['border']};
            }}
            QTreeWidget::item:hover {{
                background-color: {DARK_THEME['bg']};
            }}
            QTreeWidget::item:selected {{
                background-color: {DARK_THEME['accent']};
                color: {DARK_THEME['bg']};
            }}
            QHeaderView::section {{
                background-color: {DARK_THEME['bg']};
                color: {DARK_THEME['text_secondary']};
                padding: 6px 8px;
                border: none;
                border-bottom: 1px solid {DARK_THEME['border']};
                font-family: "Consolas", monospace;
                font-size: 10px;
                font-weight: bold;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        
        header_label = QLabel("// OPEN PROJECT")
        header_label.setFont(mono(14, bold=True, spacing=2))
        header_label.setStyleSheet(f"color: {DARK_THEME['text_secondary']};")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        browse_btn = outline_button("BROWSE...", DARK_THEME, compact=True)
        browse_btn.clicked.connect(self.browse_folder)
        header_layout.addWidget(browse_btn)
        
        layout.addLayout(header_layout)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {DARK_THEME['border']}; max-height: 1px;")
        layout.addWidget(line)
        
        projects_folder = Dialogs.get_projects_folder()
        info_label = QLabel(f"SCANNING: {projects_folder.upper()}")
        info_label.setFont(mono(10, spacing=1))
        info_label.setStyleSheet(f"color: {DARK_THEME['text_secondary']};")
        layout.addWidget(info_label)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["PROJECT NAME", "TYPE", "LOCATION"])
        self.tree.setColumnCount(3)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.setFont(mono(11))
        self.tree.itemDoubleClicked.connect(self.on_open_double_click)
        layout.addWidget(self.tree, 1)
        
        self.load_projects()
        
        hint_label = QLabel("DOUBLE-CLICK TO OPEN, OR USE BROWSE... FOR OTHER LOCATIONS")
        hint_label.setFont(mono(9, spacing=1))
        hint_label.setStyleSheet(f"color: {DARK_THEME['text_secondary']};")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.setSpacing(12)
        
        open_btn = outline_button("OPEN", DARK_THEME)
        open_btn.clicked.connect(self.open_selected)
        btn_layout.addWidget(open_btn)
        
        cancel_btn = outline_button("CANCEL", DARK_THEME, compact=True)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.selected_path = None
    
    def load_projects(self):
        projects = Dialogs.scan_projects()
        self.tree.clear()
        
        if not projects:
            item = QTreeWidgetItem(["NO PROJECTS FOUND", "", ""])
            item.setForeground(0, DARK_THEME['text_secondary'])
            self.tree.addTopLevelItem(item)
            return
        
        for p in projects:
            proj_type = "SPIDER PROJECT" if p['is_spider'] else "FOLDER"
            item = QTreeWidgetItem([p['name'].upper(), proj_type, p['path']])
            item.setData(0, Qt.ItemDataRole.UserRole, p['path'])
            self.tree.addTopLevelItem(item)
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "SELECT PROJECT FOLDER", "")
        if folder:
            self.selected_path = folder
            self.accept()
    
    def on_open_double_click(self, item, column):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path:
            self.selected_path = path
            self.accept()
    
    def open_selected(self):
        current_item = self.tree.currentItem()
        if current_item:
            path = current_item.data(0, Qt.ItemDataRole.UserRole)
            if path:
                self.selected_path = path
                self.accept()


class Dialogs:
    @staticmethod
    def welcome(parent, main_window):
        from spider_ide.ui.welcome_dialog import WelcomeDialog
        dialog = WelcomeDialog(parent)
        result = dialog.exec()
        
        if result == 1:
            main_window.open_file_dialog()
        elif result == 2:
            Dialogs.open_project(parent, main_window)
        elif result == 3:
            Dialogs.new_project(parent, main_window)
        elif result == 4:
            main_window.new_file()
    
    @staticmethod
    def get_projects_folder():
        return os.path.join(os.path.expanduser("~"), "Documents", "SpiderProjects")
    
    @staticmethod
    def scan_projects():
        projects_folder = Dialogs.get_projects_folder()
        projects = []
        
        if os.path.exists(projects_folder):
            for item in os.listdir(projects_folder):
                item_path = os.path.join(projects_folder, item)
                if os.path.isdir(item_path):
                    config_file = os.path.join(item_path, "project.json")
                    is_spider_project = os.path.exists(config_file)
                    
                    config_info = {}
                    if is_spider_project:
                        try:
                            with open(config_file, 'r') as f:
                                config_info = json.load(f)
                        except Exception:
                            pass
                    
                    projects.append({
                        'name': item,
                        'path': item_path,
                        'is_spider': is_spider_project,
                        'config': config_info
                    })
        
        return sorted(projects, key=lambda p: p['name'].lower())
    
    @staticmethod
    def new_project(parent, main_window):
        dialog = NewProjectDialog(parent)
        if dialog.exec() and dialog.created_path:
            main_file = os.path.join(dialog.created_path, "src", "main.spider")
            main_window.open_project(dialog.created_path)
            if os.path.exists(main_file):
                main_window.open_file(main_file)
    
    @staticmethod
    def open_project(parent, main_window):
        dialog = OpenProjectDialog(parent)
        if dialog.exec() and dialog.selected_path:
            main_window.open_project(dialog.selected_path) 