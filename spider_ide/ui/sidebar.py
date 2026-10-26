import os
import shutil
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLineEdit, QLabel, QMenu, QInputDialog, QMessageBox,
    QFileDialog, QFrame, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from spider_ide.ui.style_kit import DARK_THEME, mono


class Sidebar(QWidget):
    file_open_requested = pyqtSignal(str)
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.current_project = None
        self.path_items = {}
        self.open_file_nodes = {}
        self.search_filter = ""
        self.all_files = []
        self.theme = DARK_THEME
        
        self.ignore_dirs = {
            '.git', '__pycache__', 'build', 'dist', '.vscode', '.idea',
            'run.build', 'run.dist', '.pytest_cache', 'node_modules', '.cache'
        }
        self.ignore_exts = {'.pyc', '.pyo', '.exe', '.spec', '.log'}
        
        self.setup_ui()
    
    def get_theme(self):
        if hasattr(self.main_window, 'theme'):
            return self.main_window.theme
        return DARK_THEME
    
    def apply_theme(self, theme=None):
        if theme is None:
            theme = self.get_theme()
        self.theme = theme
        
        self.setStyleSheet(f"QWidget {{ background-color: {theme['bg']}; }}")
        
        if hasattr(self, 'header'):
            self.header.setStyleSheet(f"QFrame {{ background-color: {theme['bg']}; border-bottom: 1px solid {theme['border']}; }}")
        
        if hasattr(self, 'title_label'):
            self.title_label.setStyleSheet(f"QLabel {{ color: {theme['text_secondary']}; font-family: 'Consolas', monospace; font-size: 10px; font-weight: bold; letter-spacing: 1px; background: transparent; }}")
        
        button_style = f"""
            QPushButton {{
                background-color: {theme['surface']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                padding: 4px 8px;
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
        """
        if hasattr(self, 'new_file_btn'): self.new_file_btn.setStyleSheet(button_style)
        if hasattr(self, 'new_folder_btn'): self.new_folder_btn.setStyleSheet(button_style)
        if hasattr(self, 'refresh_btn'): self.refresh_btn.setStyleSheet(button_style)
        
        if hasattr(self, 'search_frame'):
            self.search_frame.setStyleSheet(f"QFrame {{ background-color: {theme['bg']}; }}")
        
        if hasattr(self, 'search_box'):
            self.search_box.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {theme['surface']};
                    color: {theme['text']};
                    border: 1px solid {theme['border']};
                    padding: 4px 8px;
                    border-radius: 0px;
                    font-family: "Consolas", monospace;
                    font-size: 11px;
                }}
                QLineEdit:focus {{ border: 1px solid {theme['accent']}; }}
            """)
        
        if hasattr(self, 'tree_frame'):
            self.tree_frame.setStyleSheet(f"QFrame {{ background-color: {theme['bg']}; }}")
        
        if hasattr(self, 'tree'):
            self.tree.setStyleSheet(f"""
                QTreeWidget {{
                    background-color: {theme['bg']};
                    color: {theme['text']};
                    border: none;
                    font-family: "Consolas", monospace;
                    font-size: 12px;
                    outline: none;
                }}
                QTreeWidget::item {{ padding: 4px 8px; border: none; background: transparent; }}
                QTreeWidget::item:selected {{ background-color: {theme['accent']}; color: {theme['bg']}; font-weight: bold; }}
                QTreeWidget::item:hover {{ background-color: {theme['surface']}; }}
                QTreeWidget::branch {{ background: transparent; }}
            """)
        
        self._context_menu_style = f"""
            QMenu {{
                background-color: {theme['surface']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                font-family: "Consolas", monospace;
                font-size: 11px;
            }}
            QMenu::item {{ padding: 6px 24px; }}
            QMenu::item:selected {{ background-color: {theme['accent']}; color: {theme['bg']}; }}
            QMenu::separator {{ height: 1px; background-color: {theme['border']}; margin: 4px 8px; }}
        """
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.header = QFrame()
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(12, 10, 12, 10)
        
        self.title_label = QLabel("// EXPLORER")
        self.title_label.setFont(mono(10, bold=True, spacing=1))
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        layout.addWidget(self.header)
        
        btn_frame = QFrame()
        btn_frame.setStyleSheet("background-color: transparent;")
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(8, 8, 8, 4)
        btn_layout.setSpacing(4)
        
        self.new_file_btn = QPushButton("+ FILE")
        self.new_file_btn.setFont(mono(9, bold=True, spacing=1))
        self.new_file_btn.clicked.connect(self.create_new_file)
        btn_layout.addWidget(self.new_file_btn)
        
        self.new_folder_btn = QPushButton("+ FOLDER")
        self.new_folder_btn.setFont(mono(9, bold=True, spacing=1))
        self.new_folder_btn.clicked.connect(self.create_new_folder)
        btn_layout.addWidget(self.new_folder_btn)
        
        self.refresh_btn = QPushButton("↻")
        self.refresh_btn.setFont(mono(10, bold=True))
        self.refresh_btn.setFixedWidth(32)
        self.refresh_btn.clicked.connect(self.refresh_tree)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        layout.addWidget(btn_frame)
        
        self.search_frame = QFrame()
        search_layout = QHBoxLayout(self.search_frame)
        search_layout.setContentsMargins(8, 4, 8, 4)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(" Search files...")
        self.search_box.setFont(mono(11))
        self.search_box.textChanged.connect(self.on_search_change)
        search_layout.addWidget(self.search_box)
        layout.addWidget(self.search_frame)
        
        self.tree_frame = QFrame()
        tree_layout = QVBoxLayout(self.tree_frame)
        tree_layout.setContentsMargins(8, 8, 8, 8)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setFont(mono(12))
        self.tree.setIndentation(16)
        self.tree.setRootIsDecorated(False)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setAnimated(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.itemDoubleClicked.connect(self.on_double_click)
        self.tree.itemExpanded.connect(self.update_branch_icons)
        self.tree.itemCollapsed.connect(self.update_branch_icons)
        
        tree_layout.addWidget(self.tree)
        layout.addWidget(self.tree_frame)
        
        self.apply_theme()
    
    def load_project(self, project_path):
        if not os.path.isdir(project_path):
            raise ValueError(f"Not a directory: {project_path}")
        
        self.current_project = project_path
        self.path_items = {}
        self.open_file_nodes = {}
        self.all_files = []
        self.tree.clear()
        
        project_name = Path(project_path).name
        theme = self.get_theme()
        root_item = QTreeWidgetItem([f"▾ {project_name}"])
        root_item.setData(0, Qt.ItemDataRole.UserRole, str(project_path))
        root_item.setData(0, Qt.ItemDataRole.UserRole + 1, 'project')
        root_item.setFont(0, mono(12, bold=True))
        root_item.setForeground(0, QColor(theme['text']))
        
        self._load_children_recursive(root_item, Path(project_path), depth=0, max_depth=3)
        
        self.tree.addTopLevelItem(root_item)
        root_item.setExpanded(True)
        
        if hasattr(self.main_window, 'tab_widget'):
            open_files = []
            for tabs in self.main_window.all_tab_widgets():
                for i in range(tabs.count()):
                    container = tabs.widget(i)
                    if hasattr(container, 'editor') and container.editor.file_path:
                        open_files.append(container.editor.file_path)
            self.update_open_file_highlights(open_files)
    
    def _load_children_recursive(self, parent_node, path, depth=0, max_depth=3):
        try:
            items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            theme = self.get_theme()
            
            for item in items:
                if self.should_ignore(item):
                    continue
                
                if self.search_filter and self.search_filter.lower() not in item.name.lower():
                    continue
                
                if item.is_dir():
                    node = QTreeWidgetItem([f"▸ {item.name}"])
                    node.setData(0, Qt.ItemDataRole.UserRole, str(item))
                    node.setData(0, Qt.ItemDataRole.UserRole + 1, 'folder')
                    node.setFont(0, mono(12))
                    node.setForeground(0, QColor(theme['text_secondary']))
                    parent_node.addChild(node)
                    self.path_items[str(item)] = node
                    
                    if depth < max_depth:
                        self._load_children_recursive(node, item, depth + 1, max_depth)
                else:
                    icon = '🕷' if item.suffix == '.spider' else '📄'
                    node = QTreeWidgetItem([f"  {icon} {item.name}"])
                    node.setData(0, Qt.ItemDataRole.UserRole, str(item))
                    node.setData(0, Qt.ItemDataRole.UserRole + 1, 'file')
                    node.setFont(0, mono(12))
                    node.setForeground(0, QColor(theme['text']))
                    parent_node.addChild(node)
                    self.path_items[str(item)] = node
                    self.all_files.append(str(item))
        except PermissionError:
            pass
    
    def should_ignore(self, path):
        if path.name.startswith('.'): return True
        if path.name in self.ignore_dirs: return True
        if path.is_file() and path.suffix in self.ignore_exts: return True
        return False
    
    def update_branch_icons(self, item):
        text = item.text(0)
        if text.startswith("▸ "):
            item.setText(0, "▾ " + text[2:])
        elif text.startswith("▾ "):
            item.setText(0, "▸ " + text[2:])
    
    def on_search_change(self, text):
        self.search_filter = text.strip() if text else ""
        if self.current_project:
            self.load_project(self.current_project)
            if self.search_filter:
                self._expand_all_nodes()
    
    def _expand_all_nodes(self):
        for i in range(self.tree.topLevelItemCount()):
            self._expand_node_recursive(self.tree.topLevelItem(i))
    
    def _expand_node_recursive(self, item):
        item.setExpanded(True)
        for i in range(item.childCount()):
            self._expand_node_recursive(item.child(i))
    
    def refresh_tree(self):
        if self.current_project:
            current_filter = self.search_filter
            self.load_project(self.current_project)
            if current_filter:
                self.search_box.setText(current_filter)
    
    def get_selected_folder(self):
        item = self.tree.currentItem()
        if not item:
            return Path(self.current_project) if self.current_project else None
        
        selected_path = item.data(0, Qt.ItemDataRole.UserRole)
        item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
        
        if not selected_path:
            return Path(self.current_project) if self.current_project else None
        
        selected_path = Path(selected_path)
        if item_type == 'folder' or selected_path.is_dir():
            return selected_path
        return selected_path.parent
    
    def create_new_file(self):
        folder = self.get_selected_folder()
        if not folder or not folder.exists():
            QMessageBox.information(self, 'Spider IDE', 'Select a folder to create a new file.')
            return
        
        file_name, ok = QInputDialog.getText(self, 'New File', 'Enter file name:', text="untitled.spider")
        if not ok or not file_name:
            return
        
        if not file_name.endswith('.spider'):
            file_name += '.spider'
        
        new_file_path = folder / file_name
        if new_file_path.exists():
            QMessageBox.error(self, 'Error', f'File "{new_file_path.name}" already exists.')
            return
        
        try:
            new_file_path.write_text('Spider(Start)\n\n', encoding='utf-8')
            self.refresh_tree()
            self.file_open_requested.emit(str(new_file_path))
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Could not create file:\n{e}')
    
    def create_new_folder(self):
        folder = self.get_selected_folder()
        if not folder or not folder.exists():
            QMessageBox.information(self, 'Spider IDE', 'Select a folder to create a new folder.')
            return
        
        folder_name, ok = QInputDialog.getText(self, 'New Folder', 'Enter folder name:', text="new_folder")
        if not ok or not folder_name:
            return
        
        new_folder_path = folder / folder_name
        if new_folder_path.exists():
            QMessageBox.error(self, 'Error', f'Folder "{folder_name}" already exists.')
            return
        
        try:
            new_folder_path.mkdir(parents=True)
            self.refresh_tree()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Could not create folder:\n{e}')
    
    def delete_item(self):
        item = self.tree.currentItem()
        if not item: return
        
        path = Path(item.data(0, Qt.ItemDataRole.UserRole))
        if not path.exists(): return
        
        reply = QMessageBox.question(self, 'Delete', f'Are you sure you want to delete "{path.name}"?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if path.is_dir(): shutil.rmtree(path)
                else: path.unlink()
                self.refresh_tree()
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Could not delete:\n{e}')
    
    def rename_item(self):
        item = self.tree.currentItem()
        if not item: return
        
        old_path = Path(item.data(0, Qt.ItemDataRole.UserRole))
        if not old_path.exists(): return
        
        new_name, ok = QInputDialog.getText(self, 'Rename', 'Enter new name:', text=old_path.name)
        if not ok or not new_name or new_name == old_path.name: return
        
        new_path = old_path.parent / new_name
        if new_path.exists():
            QMessageBox.error(self, 'Error', f'"{new_name}" already exists.')
            return
        
        try:
            old_path.rename(new_path)
            self.refresh_tree()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Could not rename:\n{e}')
    
    def show_context_menu(self, position):
        item = self.tree.itemAt(position)
        menu = QMenu(self)
        menu.setStyleSheet(self._context_menu_style)
        menu.setFont(mono(11))
        
        if item:
            item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
            if item_type == 'file':
                menu.addAction("Open", lambda: self.open_file(item))
                menu.addSeparator()
                menu.addAction("Rename", self.rename_item)
                menu.addAction("Delete", self.delete_item)
            elif item_type == 'folder':
                menu.addAction("New File", self.create_new_file)
                menu.addAction("New Folder", self.create_new_folder)
                menu.addSeparator()
                menu.addAction("Rename", self.rename_item)
                menu.addAction("Delete", self.delete_item)
            elif item_type == 'project':
                menu.addAction("New File", self.create_new_file)
                menu.addAction("New Folder", self.create_new_folder)
        else:
            menu.addAction("Open Project...", self.open_project_dialog)
        
        menu.exec(self.tree.viewport().mapToGlobal(position))
    
    def open_file(self, item):
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        if file_path and os.path.isfile(file_path):
            self.file_open_requested.emit(file_path)
    
    def open_project_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Open Project Folder", "", QFileDialog.Option.ShowDirsOnly)
        if folder:
            self.load_project(folder)
            if hasattr(self.main_window, 'status_label'):
                self.main_window.status_label.setText(f"Opened project: {os.path.basename(folder).upper()}")
    
    def on_double_click(self, item, column):
        if item.data(0, Qt.ItemDataRole.UserRole + 1) == 'file':
            self.open_file(item)
    
    def update_open_file_highlights(self, open_files):
        theme = self.get_theme()
        for path_str, node in self.path_items.items():
            if path_str in open_files:
                node.setForeground(0, QColor(theme['accent']))
            else:
                node.setForeground(0, QColor(theme['text'])) 