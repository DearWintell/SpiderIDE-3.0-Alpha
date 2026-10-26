from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QWidget, QTreeWidget, QTreeWidgetItem,
    QSplitter, QFrame, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path

from spider_ide.ui.style_kit import DARK_THEME, mono, outline_button


class FileOpenDialog(QDialog):
    file_selected = pyqtSignal(str)
    folder_selected = pyqtSignal(str)
    
    def __init__(self, parent=None, title="OPEN FILE OR PROJECT"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(900, 600)
        self.resize(1000, 650)
        self.current_path = Path.home()
        self.selection_mode = 'file'
        
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
            QTreeWidget {{
                background-color: {DARK_THEME['surface']};
                color: {DARK_THEME['text']};
                border: none;
                font-family: "Consolas", monospace;
                font-size: 12px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 6px 8px;
                border: 1px solid transparent;
            }}
            QTreeWidget::item:hover {{
                background-color: {DARK_THEME['bg']};
                border: 1px solid {DARK_THEME['border']};
            }}
            QTreeWidget::item:selected {{
                background-color: {DARK_THEME['accent']};
                color: {DARK_THEME['bg']};
                border: 1px solid {DARK_THEME['accent']};
            }}
            QListWidget {{
                background-color: {DARK_THEME['surface']};
                color: {DARK_THEME['text']};
                border: none;
                font-family: "Consolas", monospace;
                font-size: 12px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 6px 10px;
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
        
        self.setup_ui()
        self.refresh_file_list()
        self.populate_tree()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header_label = QLabel("// OPEN FILE OR PROJECT")
        header_label.setFont(mono(14, bold=True, spacing=2))
        header_label.setStyleSheet(f"color: {DARK_THEME['text_secondary']};")
        layout.addWidget(header_label)
        
        top_bar = self.create_top_bar()
        layout.addWidget(top_bar)
        
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {DARK_THEME['border']};
            }}
            QSplitter::handle:horizontal {{
                width: 1px;
            }}
        """)
        
        left_panel = self.create_navigation_panel()
        content_splitter.addWidget(left_panel)
        
        right_panel = self.create_file_list_panel()
        content_splitter.addWidget(right_panel)
        
        content_splitter.setSizes([250, 750])
        layout.addWidget(content_splitter, 1)
        
        bottom_bar = self.create_bottom_bar()
        layout.addWidget(bottom_bar)
    
    def create_top_bar(self):
        top_widget = QWidget()
        top_widget.setStyleSheet("background-color: transparent;")
        
        layout = QHBoxLayout(top_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
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
        layout.addWidget(back_btn)
        
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
        layout.addWidget(up_btn)
        
        self.address_bar = QLineEdit()
        self.address_bar.setText(str(self.current_path))
        self.address_bar.setFont(mono(12))
        self.address_bar.returnPressed.connect(self.on_address_enter)
        layout.addWidget(self.address_bar, 1)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("SEARCH...")
        self.search_box.setFixedWidth(220)
        self.search_box.setFont(mono(12))
        self.search_box.textChanged.connect(self.filter_files)
        layout.addWidget(self.search_box)
        
        return top_widget
    
    def create_navigation_panel(self):
        left_widget = QWidget()
        left_widget.setStyleSheet(f"""
            background-color: {DARK_THEME['surface']};
            border: 1px solid {DARK_THEME['border']};
        """)
        
        layout = QVBoxLayout(left_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        quick_header = QLabel("QUICK ACCESS")
        quick_header.setFont(mono(9, bold=True, spacing=1))
        quick_header.setStyleSheet(f"color: {DARK_THEME['text_secondary']}; padding: 8px; background: transparent;")
        layout.addWidget(quick_header)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {DARK_THEME['border']}; max-height: 1px;")
        layout.addWidget(sep)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self.on_tree_item_clicked)
        self.tree.itemDoubleClicked.connect(self.on_tree_item_double_clicked)
        layout.addWidget(self.tree)
        
        return left_widget
    
    def create_file_list_panel(self):
        right_widget = QWidget()
        right_widget.setStyleSheet(f"""
            background-color: {DARK_THEME['surface']};
            border: 1px solid {DARK_THEME['border']};
        """)
        
        layout = QVBoxLayout(right_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.file_list = QListWidget()
        self.file_list.setViewMode(QListWidget.ViewMode.ListMode)
        self.file_list.setSpacing(0)
        self.file_list.itemDoubleClicked.connect(self.on_item_double_click)
        self.file_list.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.file_list, 1)
        
        return right_widget
    
    def create_bottom_bar(self):
        bottom_widget = QWidget()
        bottom_widget.setStyleSheet("background-color: transparent;")
        
        layout = QHBoxLayout(bottom_widget)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(12)
        
        mode_label = QLabel("OPEN:")
        mode_label.setFont(mono(10, bold=True, spacing=1))
        mode_label.setStyleSheet(f"color: {DARK_THEME['text_secondary']};")
        layout.addWidget(mode_label)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["FILE", "PROJECT FOLDER"])
        self.mode_combo.setFont(mono(11))
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        self.mode_combo.setFixedWidth(180)
        layout.addWidget(self.mode_combo)
        
        layout.addStretch()
        
        file_name_label = QLabel("FILE NAME:")
        file_name_label.setFont(mono(10, bold=True, spacing=1))
        file_name_label.setStyleSheet(f"color: {DARK_THEME['text_secondary']};")
        layout.addWidget(file_name_label)
        
        self.file_name_input = QLineEdit()
        self.file_name_input.setFixedWidth(320)
        self.file_name_input.setFont(mono(12))
        self.file_name_input.returnPressed.connect(self.on_open_clicked)
        layout.addWidget(self.file_name_input)
        
        open_btn = outline_button("OPEN", DARK_THEME, compact=True)
        open_btn.setFixedWidth(100)
        open_btn.clicked.connect(self.on_open_clicked)
        layout.addWidget(open_btn)
        
        cancel_btn = outline_button("CANCEL", DARK_THEME, compact=True)
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        return bottom_widget
    
    def populate_tree(self):
        self.tree.clear()
        
        quick_access = QTreeWidgetItem(["QUICK ACCESS"])
        quick_access.setFont(0, mono(11, bold=True))
        
        items = [
            ("DESKTOP", Path.home() / "Desktop"),
            ("DOCUMENTS", Path.home() / "Documents"),
            ("DOWNLOADS", Path.home() / "Downloads"),
            ("THIS PC", Path("C:/")),
        ]
        
        for name, path in items:
            if path.exists():
                item = QTreeWidgetItem([name])
                item.setData(0, Qt.ItemDataRole.UserRole, path)
                quick_access.addChild(item)
        
        self.tree.addTopLevelItem(quick_access)
        quick_access.setExpanded(True)
    
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
    
    def on_tree_item_clicked(self, item, column):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path and path.exists():
            self.current_path = path
            self.refresh_file_list()
            self.search_box.clear()
    
    def on_tree_item_double_clicked(self, item, column):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path and path.exists() and path.is_dir():
            self.current_path = path
            self.refresh_file_list()
            self.search_box.clear()
    
    def on_item_clicked(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.file_name_input.setText(path.name)
    
    def on_item_double_click(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            if path.is_dir():
                self.current_path = path
                self.refresh_file_list()
                self.search_box.clear()
                self.file_name_input.clear()
            else:
                self.file_name_input.setText(path.name)
                self.on_open_clicked()
    
    def on_mode_changed(self, index):
        self.selection_mode = 'folder' if index == 1 else 'file'
    
    def filter_files(self, text):
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
    
    def on_open_clicked(self):
        file_name = self.file_name_input.text().strip()
        if file_name:
            full_path = self.current_path / file_name
            if full_path.exists():
                if full_path.is_file() and self.selection_mode == 'file':
                    self.file_selected.emit(str(full_path))
                    self.accept()
                    return
                elif full_path.is_dir() and self.selection_mode == 'folder':
                    self.folder_selected.emit(str(full_path))
                    self.accept()
                    return
                elif full_path.is_dir() and self.selection_mode == 'file':
                    self.current_path = full_path
                    self.refresh_file_list()
                    self.file_name_input.clear()
                    return
        
        current_item = self.file_list.currentItem()
        if current_item:
            path = current_item.data(Qt.ItemDataRole.UserRole)
            if path:
                if path.is_file() and self.selection_mode == 'file':
                    self.file_selected.emit(str(path))
                    self.accept()
                    return
                elif path.is_dir() and self.selection_mode == 'folder':
                    self.folder_selected.emit(str(path))
                    self.accept()
                    return
                elif path.is_dir() and self.selection_mode == 'file':
                    self.current_path = path
                    self.refresh_file_list()
                    self.file_name_input.clear()
                    return 