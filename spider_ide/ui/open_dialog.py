from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QWidget, QComboBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path

from spider_ide.ui.style_kit import DARK_THEME, mono, outline_button


class ModernOpenDialog(QDialog):
    file_selected = pyqtSignal(str)
    folder_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OPEN FILE OR PROJECT")
        self.setMinimumSize(750, 520)
        self.resize(850, 580)
        self.current_path = Path.home()
        
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
                padding: 6px 10px;
                font-family: "Consolas", monospace;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {DARK_THEME['accent']};
            }}
            QComboBox {{
                background-color: {DARK_THEME['surface']};
                color: {DARK_THEME['text']};
                border: 1px solid {DARK_THEME['border']};
                border-radius: 0px;
                padding: 4px 8px;
                font-family: "Consolas", monospace;
                font-size: 12px;
            }}
            QComboBox:focus {{
                border: 1px solid {DARK_THEME['accent']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {DARK_THEME['surface']};
                color: {DARK_THEME['text']};
                border: 1px solid {DARK_THEME['border']};
                selection-background-color: {DARK_THEME['accent']};
                selection-color: {DARK_THEME['bg']};
            }}
            QListWidget {{
                background-color: {DARK_THEME['surface']};
                color: {DARK_THEME['text']};
                border: 1px solid {DARK_THEME['border']};
                border-radius: 0px;
                font-family: "Consolas", monospace;
                font-size: 12px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 4px 8px;
                border: 1px solid transparent;
            }}
            QListWidget::item:hover {{
                background-color: {DARK_THEME['bg']};
                border: 1px solid {DARK_THEME['border']};
            }}
            QListWidget::item:selected {{
                background-color: {DARK_THEME['accent']};
                color: {DARK_THEME['bg']};
                border: 1px solid {DARK_THEME['accent']};
            }}
            QFrame {{
                background-color: {DARK_THEME['border']};
            }}
        """)
        
        self.setup_ui()
        self.refresh_file_list()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header_label = QLabel("// OPEN FILE OR PROJECT")
        header_label.setFont(mono(14, bold=True, spacing=2))
        header_label.setStyleSheet(f"color: {DARK_THEME['text_secondary']}; background: transparent;")
        layout.addWidget(header_label)
        
        address_layout = QHBoxLayout()
        address_layout.setSpacing(8)
        
        back_btn = QPushButton("←")
        back_btn.setFont(mono(12, bold=True))
        back_btn.setFixedSize(32, 32)
        back_btn.setToolTip("BACK")
        back_btn.clicked.connect(self.go_back)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {DARK_THEME['text']};
                border: 1px solid {DARK_THEME['border']};
            }}
            QPushButton:hover {{
                background-color: {DARK_THEME['accent']};
                color: {DARK_THEME['bg']};
                border-color: {DARK_THEME['accent']};
            }}
        """)
        address_layout.addWidget(back_btn)
        
        up_btn = QPushButton("↑")
        up_btn.setFont(mono(12, bold=True))
        up_btn.setFixedSize(32, 32)
        up_btn.setToolTip("UP")
        up_btn.clicked.connect(self.go_up)
        up_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {DARK_THEME['text']};
                border: 1px solid {DARK_THEME['border']};
            }}
            QPushButton:hover {{
                background-color: {DARK_THEME['accent']};
                color: {DARK_THEME['bg']};
                border-color: {DARK_THEME['accent']};
            }}
        """)
        address_layout.addWidget(up_btn)
        
        self.address_bar = QLineEdit()
        self.address_bar.setText(str(self.current_path))
        self.address_bar.setFont(mono(12))
        self.address_bar.returnPressed.connect(self.on_address_enter)
        address_layout.addWidget(self.address_bar, 1)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("SEARCH...")
        self.search_box.setFixedWidth(220)
        self.search_box.setFont(mono(12))
        self.search_box.textChanged.connect(self.filter_files)
        address_layout.addWidget(self.search_box)
        
        layout.addLayout(address_layout)
        
        content_layout = QHBoxLayout()
        content_layout.setSpacing(8)
        
        left_panel = QWidget()
        left_panel.setFixedWidth(180)
        left_panel.setStyleSheet(f"background-color: {DARK_THEME['surface']}; border: 1px solid {DARK_THEME['border']};")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(2)
        
        quick_header = QLabel("QUICK ACCESS")
        quick_header.setFont(mono(9, bold=True, spacing=1))
        quick_header.setStyleSheet(f"color: {DARK_THEME['text_secondary']}; padding: 8px; background: transparent;")
        left_layout.addWidget(quick_header)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        left_layout.addWidget(sep)
        
        self.quick_list = QListWidget()
        self.quick_list.setFont(mono(11))
        self.quick_list.addItems([
            "HOME",
            "DESKTOP",
            "DOCUMENTS",
            "DOWNLOADS",
            "THIS PC"
        ])
        self.quick_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                padding: 6px 8px;
                border: 1px solid transparent;
            }}
            QListWidget::item:hover {{
                background-color: {DARK_THEME['bg']};
                border: 1px solid {DARK_THEME['border']};
            }}
            QListWidget::item:selected {{
                background-color: {DARK_THEME['accent']};
                color: {DARK_THEME['bg']};
                border: 1px solid {DARK_THEME['accent']};
            }}
        """)
        self.quick_list.clicked.connect(self.on_quick_access)
        left_layout.addWidget(self.quick_list)
        
        content_layout.addWidget(left_panel)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        self.file_list = QListWidget()
        self.file_list.setFont(mono(12))
        self.file_list.itemDoubleClicked.connect(self.on_item_double_click)
        right_layout.addWidget(self.file_list, 1)
        
        content_layout.addWidget(right_panel, 1)
        layout.addLayout(content_layout)
        
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep2)
        
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)
        
        file_type_label = QLabel("FILES OF TYPE:")
        file_type_label.setFont(mono(10, bold=True, spacing=1))
        file_type_label.setStyleSheet(f"color: {DARK_THEME['text_secondary']};")
        bottom_layout.addWidget(file_type_label)
        
        self.file_type_combo = QComboBox()
        self.file_type_combo.addItems(["SPIDER FILES (*.spider)", "ALL FILES (*)"])
        self.file_type_combo.setFixedWidth(240)
        self.file_type_combo.setFont(mono(11))
        bottom_layout.addWidget(self.file_type_combo)
        
        bottom_layout.addStretch()
        
        file_name_label = QLabel("FILE NAME:")
        file_name_label.setFont(mono(10, bold=True, spacing=1))
        file_name_label.setStyleSheet(f"color: {DARK_THEME['text_secondary']};")
        bottom_layout.addWidget(file_name_label)
        
        self.file_name_input = QLineEdit()
        self.file_name_input.setFixedWidth(320)
        self.file_name_input.setFont(mono(12))
        bottom_layout.addWidget(self.file_name_input)
        
        open_btn = outline_button("OPEN", DARK_THEME, compact=True)
        open_btn.setFixedWidth(100)
        open_btn.clicked.connect(self.on_open_clicked)
        bottom_layout.addWidget(open_btn)
        
        cancel_btn = outline_button("CANCEL", DARK_THEME, compact=True)
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(cancel_btn)
        
        layout.addLayout(bottom_layout)
    
    def refresh_file_list(self):
        self.file_list.clear()
        
        try:
            items = list(self.current_path.iterdir())
            items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for item in items:
                if item.name.startswith('.'):
                    continue
                if item.is_dir():
                    text = f"[DIR]  {item.name.upper()}"
                elif item.suffix == '.spider':
                    text = f"[FILE] {item.name.upper()}"
                else:
                    text = f"[FILE] {item.name.upper()}"
                
                list_item = QListWidgetItem(text)
                list_item.setData(Qt.ItemDataRole.UserRole, item)
                self.file_list.addItem(list_item)
            
            self.address_bar.setText(str(self.current_path))
        except PermissionError:
            self.file_list.addItem("PERMISSION DENIED")
        except Exception as e:
            self.file_list.addItem(f"ERROR: {str(e)}")
    
    def go_back(self):
        self.go_up()
    
    def go_up(self):
        if self.current_path.parent != self.current_path:
            self.current_path = self.current_path.parent
            self.refresh_file_list()
            self.search_box.clear()
    
    def on_address_enter(self):
        try:
            new_path = Path(self.address_bar.text())
            if new_path.exists() and new_path.is_dir():
                self.current_path = new_path
                self.refresh_file_list()
        except Exception:
            pass
    
    def on_quick_access(self, index):
        row = index.row()
        try:
            if row == 0:
                self.current_path = Path.home()
            elif row == 1:
                self.current_path = Path.home() / "Desktop"
            elif row == 2:
                self.current_path = Path.home() / "Documents"
            elif row == 3:
                self.current_path = Path.home() / "Downloads"
            elif row == 4:
                self.current_path = Path("C:\\")
            
            if self.current_path.exists():
                self.refresh_file_list()
                self.search_box.clear()
        except Exception:
            pass
    
    def filter_files(self, text):
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
    
    def on_item_double_click(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and path.is_dir():
            self.current_path = path
            self.refresh_file_list()
            self.search_box.clear()
        elif path and path.is_file():
            self.file_name_input.setText(path.name)
    
    def on_open_clicked(self):
        file_name = self.file_name_input.text().strip()
        if file_name:
            full_path = self.current_path / file_name
            if full_path.exists():
                if full_path.is_file():
                    self.file_selected.emit(str(full_path))
                    self.accept()
                elif full_path.is_dir():
                    self.folder_selected.emit(str(full_path))
                    self.accept()
                return
        
        current_item = self.file_list.currentItem()
        if current_item:
            path = current_item.data(Qt.ItemDataRole.UserRole)
            if path and path.is_file():
                self.file_selected.emit(str(path))
                self.accept()
            elif path and path.is_dir():
                self.folder_selected.emit(str(path))
                self.accept() 