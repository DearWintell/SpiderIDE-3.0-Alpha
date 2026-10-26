import sys
import os
import json
import re
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QSplitter, QStatusBar, QMenuBar, QMenu, QFileDialog, QMessageBox,
    QToolBar, QPushButton, QLabel, QFrame, QTabWidget, QInputDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon, QFont, QColor, QKeySequence, QAction, QPixmap, QTextCursor

from spider_ide.core.config import Config
from spider_ide.core.runner import Runner
from spider_ide.ui.console import Console
from spider_ide.ui.terminal import Terminal
from spider_ide.ui.sidebar import Sidebar
from spider_ide.ui.help_dialog import HelpDialog
from spider_ide.ui.settings_dialog import SettingsDialog
from spider_ide.ui.project_search import ProjectSearchDialog
from spider_ide.ui.file_open_dialog import FileOpenDialog
from spider_ide.core.editor import EditorContainer
from spider_ide.ui.tabs import BrutalistTabBar

from spider_ide.ui.style_kit import (
    set_grid_background, set_editor_grid,
    hero_title, caption, outline_button, CardFrame, logo_label, mono
)


def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class VariableInspectorPanel(QFrame):
    def __init__(self, parent=None, theme=None):
        super().__init__(parent)
        self.theme = theme
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self.header = QLabel(" VARIABLES (STATIC ANALYSIS)")
        self.header.setFont(mono(10, bold=True, spacing=1))
        self.header.setStyleSheet(f"color: {self.theme['text_secondary']}; background: transparent;")
        layout.addWidget(self.header)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["NAME", "VALUE / DEFAULT"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setFont(mono(9, bold=True))
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        self.table.setFont(mono(11))
        layout.addWidget(self.table)

        self.is_live_mode = False
        self.debug_file_path = None
        self.last_debug_content = ""

        self.debug_timer = QTimer(self)
        self.debug_timer.timeout.connect(self.check_live_debug)
        self.debug_timer.start(500)

    def enable_live_mode(self, debug_file_path):
        self.debug_file_path = debug_file_path
        self.is_live_mode = True
        self.last_debug_content = ""
        self.header.setText(" VARIABLES (LIVE DEBUG)")
        self.header.setStyleSheet(f"color: {self.theme['success']}; background: transparent;")

    def disable_live_mode(self):
        self.is_live_mode = False
        self.debug_file_path = None
        self.header.setText(" VARIABLES (STATIC ANALYSIS)")
        self.header.setStyleSheet(f"color: {self.theme['text_secondary']}; background: transparent;")

    def check_live_debug(self):
        if not self.is_live_mode:
            return
        if not Runner.is_running():
            self.disable_live_mode()
            return
        if self.debug_file_path and os.path.exists(self.debug_file_path):
            try:
                with open(self.debug_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if content != self.last_debug_content:
                    self.last_debug_content = content
                    data = json.loads(content)
                    self.update_from_dict(data)
            except Exception:
                pass

    def update_from_dict(self, data):
        self.table.setRowCount(0)
        self.table.setRowCount(len(data))

        for row, (name, val) in enumerate(data.items()):
            name_item = QTableWidgetItem(str(name))
            name_item.setForeground(QColor("#7dd3fc"))
            self.table.setItem(row, 0, name_item)

            val_str = str(val)
            if (val_str.startswith('"') and val_str.endswith('"')) or \
               (val_str.startswith("'") and val_str.endswith("'")):
                val_str = val_str[1:-1]

            val_item = QTableWidgetItem(val_str)
            val_item.setForeground(QColor("#fbbf24"))
            self.table.setItem(row, 1, val_item)

    def update_variables(self, code_text):
        if self.is_live_mode:
            return

        self.table.setRowCount(0)
        var_pattern = re.compile(r'var\s+([a-zA-Z_]\w*)\s*(?:=\s*(.+))?')
        matches = var_pattern.findall(code_text)

        unique_vars = {}
        for name, value in matches:
            unique_vars[name] = value.strip() if value else "None"

        self.table.setRowCount(len(unique_vars))
        for row, (name, val_str) in enumerate(unique_vars.items()):
            name_item = QTableWidgetItem(name)
            name_item.setForeground(QColor("#7dd3fc"))
            self.table.setItem(row, 0, name_item)

            if (val_str.startswith('"') and val_str.endswith('"')) or \
               (val_str.startswith("'") and val_str.endswith("'")):
                val_str = val_str[1:-1]

            val_item = QTableWidgetItem(val_str)
            val_item.setForeground(QColor("#fbbf24"))
            self.table.setItem(row, 1, val_item)


class MainWindow(QMainWindow):
    def __init__(self, file_path=None):
        super().__init__()

        self.file_path = file_path
        self.fullscreen = False
        self.current_project = None
        self.config = Config()
        self.theme = self.config.get_theme()

        self.tab_widget2 = None
        self._last_active_tabs = None
        self.recent_files_menu = None
        self.recent_projects_menu = None

        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_all)
        self.auto_save_interval = self.config.get('auto_save_interval', 30)
        if self.config.get('auto_save_enabled', False):
            self.auto_save_timer.start(self.auto_save_interval * 1000)

        self.setWindowTitle("SPIDER.IDE")
        self.setGeometry(100, 100, 1400, 900)

        if self.config.get('window_geometry'):
            try:
                self.restoreGeometry(bytes.fromhex(self.config.get('window_geometry')))
            except Exception:
                pass

        self.load_icon()

        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()

        self.apply_theme()

        if not file_path:
            self.restore_session()
        else:
            if os.path.isdir(file_path):
                self.open_project(file_path)
            else:
                self.open_file(file_path)

    def all_tab_widgets(self):
        if not hasattr(self, 'tab_widget'):
            return []
        if self.tab_widget2 is None:
            return [self.tab_widget]
        return [self.tab_widget, self.tab_widget2]

    def active_tab_widget(self):
        if not hasattr(self, 'tab_widget'):
            return None
        if self.tab_widget2 is None:
            return self.tab_widget
        if self._last_active_tabs in (self.tab_widget, self.tab_widget2):
            return self._last_active_tabs
        return self.tab_widget

    def _recent_files(self):
        recent = self.config.get('recent_files', []) or []
        return [p for p in recent if isinstance(p, str) and Path(p).is_file()][:10]

    def _recent_projects(self):
        recent = self.config.get('recent_projects', []) or []
        return [p for p in recent if isinstance(p, str) and Path(p).is_dir()][:5]

    def update_recent_files_menu(self, menu):
        if menu is None:
            return
        menu.clear()
        recent = self._recent_files()
        if not recent:
            empty = QAction("NO RECENT FILES", self)
            empty.setEnabled(False)
            menu.addAction(empty)
            return

        for path in recent:
            action = QAction(Path(path).name.upper(), self)
            action.setToolTip(path)
            action.triggered.connect(lambda checked, p=path: self.open_file(p))
            menu.addAction(action)

        menu.addSeparator()
        clear_action = QAction("CLEAR LIST", self)
        clear_action.triggered.connect(self.clear_recent_files_menu)
        menu.addAction(clear_action)

    def update_recent_projects_menu(self, menu):
        if menu is None:
            return
        menu.clear()
        recent = self._recent_projects()
        if not recent:
            empty = QAction("NO RECENT PROJECTS", self)
            empty.setEnabled(False)
            menu.addAction(empty)
            return

        for path in recent:
            action = QAction(Path(path).name.upper(), self)
            action.setToolTip(path)
            action.triggered.connect(lambda checked, p=path: self.open_project(p))
            menu.addAction(action)

        menu.addSeparator()
        clear_action = QAction("CLEAR LIST", self)
        clear_action.triggered.connect(self.clear_recent_projects_menu)
        menu.addAction(clear_action)

    def clear_recent_files_menu(self):
        self.config.set('recent_files', [])
        self.update_recent_files_menu(self.recent_files_menu)

    def clear_recent_projects_menu(self):
        self.config.set('recent_projects', [])
        self.update_recent_projects_menu(self.recent_projects_menu)

    def _update_tab_title(self, container):
        if not isinstance(container, EditorContainer):
            return
        path = container.editor.file_path
        if not path or path == "Untitled.spider":
            title = "UNTITLED.SPIDER"
        else:
            title = Path(path).name.upper()
            if container.editor.document().isModified():
                title += " *"

        for tabs in self.all_tab_widgets():
            index = tabs.indexOf(container)
            if index >= 0:
                tabs.setTabText(index, title)

    def _connect_editor_signals(self, container):
        container.editor.document().modificationChanged.connect(
            lambda modified, c=container: self._update_tab_title(c)
        )

    def restore_session(self):
        session_files = self.config.get('session_files', '[]')
        try:
            files = json.loads(session_files)
            for f in files:
                if os.path.exists(f):
                    self.open_file(f)
        except Exception:
            pass
        if self.tab_widget.count() == 0:
            self.show_welcome_tab()

    def closeEvent(self, event):
        open_files = []
        for tabs in self.all_tab_widgets():
            for i in range(tabs.count()):
                container = tabs.widget(i)
                if isinstance(container, EditorContainer):
                    path = container.editor.file_path
                    if path and path != "Untitled.spider":
                        open_files.append(path)

        self.config.set('session_files', json.dumps(open_files))

        try:
            self.config.set('window_geometry', self.saveGeometry().data().hex())
        except Exception:
            pass
        event.accept()

    def load_icon(self):
        try:
            icon_path = get_resource_path('assets/little_logo.png')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"Failed to load icon: {e}")

    def apply_theme(self):
        self.theme = self.config.get_theme()
        theme = self.theme

        qss = f"""
            QMainWindow {{
                background-color: {theme['bg']};
            }}

            QMenuBar {{
                background-color: {theme['bg']};
                color: {theme['text']};
                padding: 4px 8px;
                border-bottom: 1px solid {theme['border']};
                font-family: "Consolas", monospace;
                font-size: 12px;
            }}
            QMenuBar::item:selected {{
                background-color: {theme['surface']};
                color: {theme['text']};
            }}

            QMenu {{
                background-color: {theme['surface']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                padding: 4px;
                font-family: "Consolas", monospace;
                font-size: 12px;
            }}
            QMenu::item {{
                padding: 6px 24px;
                border-radius: 0px;
            }}
            QMenu::item:selected {{
                background-color: {theme['accent']};
                color: {theme['bg']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {theme['border']};
                margin: 4px 8px;
            }}

            QToolBar {{
                background-color: {theme['bg']};
                border: none;
                border-bottom: 1px solid {theme['border']};
                spacing: 8px;
                padding: 6px;
            }}
            QToolBar::separator {{
                width: 1px;
                background-color: {theme['border']};
                margin: 4px 8px;
            }}

            QPushButton {{
                background-color: {theme['surface']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                padding: 6px 12px;
                border-radius: 0px;
                font-family: "Consolas", monospace;
                font-size: 11px;
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

            QSplitter::handle {{
                background-color: {theme['border']};
            }}
            QSplitter::handle:horizontal {{
                width: 1px;
            }}
            QSplitter::handle:vertical {{
                height: 1px;
            }}

            QStatusBar {{
                background-color: {theme['surface']};
                color: {theme['text_secondary']};
                padding: 4px 8px;
                border-top: 1px solid {theme['border']};
                font-family: "Consolas", monospace;
                font-size: 11px;
            }}
            QStatusBar QLabel {{
                color: {theme['text_secondary']};
                padding: 0 8px;
                background: transparent;
            }}

            QScrollBar:vertical {{
                background-color: {theme['bg']};
                width: 10px;
                margin: 0;
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

            QScrollBar:horizontal {{
                background-color: {theme['bg']};
                height: 10px;
                margin: 0;
                border: none;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {theme['border']};
                min-width: 20px;
                border-radius: 0px;
                margin: 2px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {theme['text_secondary']};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
            }}

            QTabWidget::pane {{
                border: none;
                background-color: transparent;
            }}
        """
        self.setStyleSheet(qss)

        if hasattr(self, 'var_panel'):
            self.var_panel.theme = theme

        self._apply_theme_to_components(theme)
        self.apply_editor_settings()

    def apply_theme(self):
        self.theme = self.config.get_theme()
        theme = self.theme

        qss = f"""
            QMainWindow {{
                background-color: {theme['bg']};
            }}

            QMenuBar {{
                background-color: {theme['bg']};
                color: {theme['text']};
                padding: 4px 8px;
                border-bottom: 1px solid {theme['border']};
                font-family: "Consolas", monospace;
                font-size: 12px;
            }}
            QMenuBar::item:selected {{
                background-color: {theme['surface']};
                color: {theme['text']};
            }}

            QMenu {{
                background-color: {theme['surface']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                padding: 4px;
                font-family: "Consolas", monospace;
                font-size: 12px;
            }}
            QMenu::item {{
                padding: 6px 24px;
                border-radius: 0px;
            }}
            QMenu::item:selected {{
                background-color: {theme['accent']};
                color: {theme['bg']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {theme['border']};
                margin: 4px 8px;
            }}

            QToolBar {{
                background-color: {theme['bg']};
                border: none;
                border-bottom: 1px solid {theme['border']};
                spacing: 8px;
                padding: 6px;
            }}
            QToolBar::separator {{
                width: 1px;
                background-color: {theme['border']};
                margin: 4px 8px;
            }}

            QPushButton {{
                background-color: {theme['surface']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                padding: 6px 12px;
                border-radius: 0px;
                font-family: "Consolas", monospace;
                font-size: 11px;
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

            QSplitter::handle {{
                background-color: {theme['border']};
            }}
            QSplitter::handle:horizontal {{
                width: 1px;
            }}
            QSplitter::handle:vertical {{
                height: 1px;
            }}

            QStatusBar {{
                background-color: {theme['surface']};
                color: {theme['text_secondary']};
                padding: 4px 8px;
                border-top: 1px solid {theme['border']};
                font-family: "Consolas", monospace;
                font-size: 11px;
            }}
            QStatusBar QLabel {{
                color: {theme['text_secondary']};
                padding: 0 8px;
                background: transparent;
            }}

            QScrollBar:vertical {{
                background-color: {theme['bg']};
                width: 10px;
                margin: 0;
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

            QScrollBar:horizontal {{
                background-color: {theme['bg']};
                height: 10px;
                margin: 0;
                border: none;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {theme['border']};
                min-width: 20px;
                border-radius: 0px;
                margin: 2px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {theme['text_secondary']};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
            }}

            /* ИСПРАВЛЕНИЕ ДЛЯ СВЕТЛОЙ ТЕМЫ */
            QTabWidget::pane {{
                border: none;
                background-color: {theme['bg']}; /* Фон области под вкладками */
                border-top: 1px solid {theme['border']};
            }}
            QTabBar::tab {{
                background-color: {theme['surface']}; /* Неактивные вкладки чуть темнее фона */
                color: {theme['text_secondary']};
                padding: 8px 16px;
                border: 1px solid {theme['border']};
                border-bottom: none;
                font-family: "Consolas", monospace;
                font-size: 11px;
                font-weight: bold;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {theme['bg']}; /* Активная сливается с областью контента */
                color: {theme['text']};
                border-bottom: 2px solid {theme['accent']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {theme['bg']};
                color: {theme['text']};
            }}
        """
        self.setStyleSheet(qss)

        if hasattr(self, 'var_panel'):
            self.var_panel.theme = theme

        self._apply_theme_to_components(theme)
        self.apply_editor_settings() 

    def _apply_theme_to_components(self, theme):
        if hasattr(self, 'sidebar'):
            self.sidebar.apply_theme(theme)

        if hasattr(self, 'console'):
            self.console.apply_theme(theme)

        if hasattr(self, 'terminal'):
            self.terminal.apply_theme(theme)

        if hasattr(self, 'var_panel'):
            self.var_panel.theme = theme
            self.var_panel.setStyleSheet(f"""
                QFrame {{
                    background-color: {theme['surface']};
                    border: 1px solid {theme['border']};
                    border-radius: 0px;
                }}
                QTableWidget {{
                    background-color: transparent;
                    color: {theme['text']};
                    border: none;
                    gridline-color: {theme['border']};
                    font-family: "Consolas", monospace;
                }}
                QHeaderView::section {{
                    background-color: {theme['bg']};
                    color: {theme['text_secondary']};
                    padding: 4px;
                    border: none;
                    border-bottom: 1px solid {theme['border']};
                    font-family: "Consolas", monospace;
                    font-size: 10px;
                }}
            """)

        for tabs in self.all_tab_widgets():
            for i in range(tabs.count()):
                container = tabs.widget(i)
                if isinstance(container, EditorContainer):
                    container.apply_theme(theme)
                    if hasattr(container.editor, 'viewport'):
                        set_editor_grid(container.editor, theme, step=40)

    def apply_editor_settings(self):
        if not hasattr(self, 'tab_widget'):
            return

        font_size = self.config.get('font_size', 14)
        font_family = self.config.get('font_family', 'Consolas')
        theme = self.theme

        for tabs in self.all_tab_widgets():
            for i in range(tabs.count()):
                container = tabs.widget(i)
                if isinstance(container, EditorContainer):
                    editor = container.editor
                    font = QFont(font_family, font_size)
                    font.setStyleHint(QFont.StyleHint.Monospace)
                    editor.setFont(font)

                    if hasattr(container, 'minimap'):
                        container.minimap.setVisible(self.config.get('show_minimap', True))

                    if self.config.get('show_line_numbers', True):
                        editor.setViewportMargins(editor.line_number_area_width(), 0, 0, 0)
                    else:
                        editor.setViewportMargins(0, 0, 0, 0)

                    if hasattr(editor, 'show_indent_guides'):
                        editor.show_indent_guides = self.config.get('show_indent_guides', True)
                        editor.viewport().update()

                    if hasattr(editor, 'viewport'):
                        set_editor_grid(editor.viewport(), theme, step=40)

    def setup_ui(self):
        t = self.theme
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        set_grid_background(central_widget, t, step=40)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)

        self.sidebar = Sidebar(self)
        self.sidebar.setMinimumWidth(200)
        self.sidebar.setMaximumWidth(400)
        self.sidebar.file_open_requested.connect(self.open_file)
        self.splitter.addWidget(self.sidebar)

        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: transparent;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabBar(BrutalistTabBar())
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        self.editor_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.editor_splitter.setStyleSheet("background-color: transparent;")
        self.editor_splitter.addWidget(self.tab_widget)
        right_layout.addWidget(self.editor_splitter, 3)

        self.var_panel = VariableInspectorPanel(self, theme=t)
        self.var_panel.setMaximumHeight(180)
        right_layout.addWidget(self.var_panel, 1)

        self.console = Console(main_window=self)
        self.console.setMaximumHeight(200)
        right_layout.addWidget(self.console, 1)

        self.terminal = Terminal(main_window=self)
        self.terminal.setMaximumHeight(250)
        self.terminal.setVisible(False)
        right_layout.addWidget(self.terminal, 1)

        self.splitter.addWidget(right_panel)
        self.splitter.setSizes([250, 1150])

    def _make_editor_tabs(self):
        tabs = QTabWidget()
        tabs.setTabBar(BrutalistTabBar())
        tabs.setTabsClosable(True)
        tabs.setMovable(True)
        tabs.tabCloseRequested.connect(self.close_tab)
        tabs.currentChanged.connect(self.on_tab_changed)
        return tabs

    def setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")

        new_file_action = QAction("&New File", self)
        new_file_action.setShortcut(QKeySequence("Ctrl+N"))
        new_file_action.triggered.connect(self.new_file)
        file_menu.addAction(new_file_action)

        new_project_action = QAction("New &Project...", self)
        new_project_action.triggered.connect(self.new_project)
        file_menu.addAction(new_project_action)

        file_menu.addSeparator()

        open_file_action = QAction("&Open File...", self)
        open_file_action.setShortcut(QKeySequence("Ctrl+O"))
        open_file_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_file_action)

        open_project_action = QAction("Open &Project...", self)
        open_project_action.triggered.connect(self.open_project_dialog)
        file_menu.addAction(open_project_action)

        file_menu.addSeparator()

        self.recent_files_menu = file_menu.addMenu("RECENT FILES")
        self.update_recent_files_menu(self.recent_files_menu)

        self.recent_projects_menu = file_menu.addMenu("RECENT PROJECTS")
        self.update_recent_projects_menu(self.recent_projects_menu)

        file_menu.addSeparator()

        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        settings_action = QAction("Se&ttings...", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = menubar.addMenu("&Edit")

        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        find_action = QAction("&Find/Replace", self)
        find_action.setShortcut(QKeySequence("Ctrl+F"))
        find_action.triggered.connect(self.show_find_replace)
        edit_menu.addAction(find_action)

        project_search_action = QAction("Search in &Project...", self)
        project_search_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
        project_search_action.triggered.connect(self.show_project_search)
        edit_menu.addAction(project_search_action)

        goto_action = QAction("&Go to Line...", self)
        goto_action.setShortcut(QKeySequence("Ctrl+G"))
        goto_action.triggered.connect(self.goto_line)
        edit_menu.addAction(goto_action)

        view_menu = menubar.addMenu("&View")

        fullscreen_action = QAction("Toggle &Fullscreen", self)
        fullscreen_action.setShortcut(QKeySequence("F11"))
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        split_view_action = QAction("SPLIT VIEW", self)
        split_view_action.setShortcut(QKeySequence("Ctrl+\\"))
        split_view_action.triggered.connect(self.toggle_split_view)
        view_menu.addAction(split_view_action)

        toggle_console_action = QAction("Toggle &Console", self)
        toggle_console_action.setShortcut(QKeySequence("Ctrl+`"))
        toggle_console_action.triggered.connect(self.toggle_console)
        view_menu.addAction(toggle_console_action)

        toggle_terminal_action = QAction("Toggle &Terminal", self)
        toggle_terminal_action.setShortcut(QKeySequence("Ctrl+Shift+`"))
        toggle_terminal_action.triggered.connect(self.toggle_terminal)
        view_menu.addAction(toggle_terminal_action)

        toggle_minimap_action = QAction("Toggle &Minimap", self)
        toggle_minimap_action.triggered.connect(self.toggle_minimap)
        view_menu.addAction(toggle_minimap_action)

        auto_save_action = QAction("Toggle Auto-Save", self)
        auto_save_action.setCheckable(True)
        auto_save_action.setChecked(self.config.get('auto_save_enabled', False))
        auto_save_action.triggered.connect(self.toggle_auto_save)
        view_menu.addAction(auto_save_action)

        run_menu = menubar.addMenu("&Run")

        run_action = QAction("&Run", self)
        run_action.setShortcut(QKeySequence("F5"))
        run_action.triggered.connect(self.run_code)
        run_menu.addAction(run_action)

        debug_action = QAction("&Debug (Live)", self)
        debug_action.setShortcut(QKeySequence("F6"))
        debug_action.triggered.connect(self.run_debug)
        run_menu.addAction(debug_action)

        stop_action = QAction("&Stop", self)
        stop_action.setShortcut(QKeySequence("Shift+F5"))
        stop_action.triggered.connect(self.stop_code)
        run_menu.addAction(stop_action)

        help_menu = menubar.addMenu("&Help")

        help_action = QAction("&Documentation", self)
        help_action.setShortcut(QKeySequence("F1"))
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

        about_action = QAction("&About Spider IDE", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_toolbar(self):
        t = self.theme
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        logo_w = logo_label(t, size=12, spacing=2)
        logo_w.setToolTip("Spider IDE v1.3")
        toolbar.addWidget(logo_w)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        sep.setFixedHeight(24)
        sep.setStyleSheet(f"background-color: {t['border']};")
        toolbar.addWidget(sep)

        spacer = QWidget()
        spacer.setFixedWidth(8)
        toolbar.addWidget(spacer)

        new_btn = QPushButton("NEW")
        new_btn.setFont(mono(10, bold=True, spacing=1))
        new_btn.clicked.connect(self.new_file)
        toolbar.addWidget(new_btn)

        open_btn = QPushButton("OPEN")
        open_btn.setFont(mono(10, bold=True, spacing=1))
        open_btn.clicked.connect(self.open_smart_dialog)
        toolbar.addWidget(open_btn)

        save_btn = QPushButton("SAVE")
        save_btn.setFont(mono(10, bold=True, spacing=1))
        save_btn.clicked.connect(self.save_file)
        toolbar.addWidget(save_btn)

        toolbar.addSeparator()

        run_btn = QPushButton("RUN")
        run_btn.setFont(mono(10, bold=True, spacing=1))
        run_btn.clicked.connect(self.run_code)
        toolbar.addWidget(run_btn)

        debug_btn = QPushButton("DEBUG")
        debug_btn.setFont(mono(10, bold=True, spacing=1))
        debug_btn.clicked.connect(self.run_debug)
        toolbar.addWidget(debug_btn)

        stop_btn = QPushButton("STOP")
        stop_btn.setFont(mono(10, bold=True, spacing=1))
        stop_btn.clicked.connect(self.stop_code)
        toolbar.addWidget(stop_btn)

        toolbar.addSeparator()

        split_btn = QPushButton("SPLIT")
        split_btn.setFont(mono(10, bold=True, spacing=1))
        split_btn.setToolTip("SPLIT VIEW (CTRL+\\)")
        split_btn.clicked.connect(self.toggle_split_view)
        toolbar.addWidget(split_btn)

        settings_btn = QPushButton("SETTINGS")
        settings_btn.setFont(mono(10, bold=True, spacing=1))
        settings_btn.clicked.connect(self.show_settings)
        toolbar.addWidget(settings_btn)

    def setup_statusbar(self):
        t = self.theme
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.status_label = QLabel("READY")
        self.status_label.setFont(mono(10, spacing=1))
        self.statusbar.addWidget(self.status_label, 1)

        self.encoding_label = QLabel("UTF-8")
        self.encoding_label.setFont(mono(10))
        self.encoding_label.setStyleSheet("padding: 0 8px;")
        self.statusbar.addPermanentWidget(self.encoding_label)

        sep1 = QLabel("|")
        sep1.setStyleSheet(f"padding: 0 4px; color: {t['border']};")
        self.statusbar.addPermanentWidget(sep1)

        self.version_label = QLabel("SPIDER v1.3")
        self.version_label.setFont(mono(10, bold=True, spacing=1))
        self.version_label.setStyleSheet("padding: 0 8px;")
        self.statusbar.addPermanentWidget(self.version_label)

        sep2 = QLabel("|")
        sep2.setStyleSheet(f"padding: 0 4px; color: {t['border']};")
        self.statusbar.addPermanentWidget(sep2)

        self.line_col_label = QLabel("LN 1, COL 1")
        self.line_col_label.setFont(mono(10, bold=True, spacing=1))
        self.line_col_label.setStyleSheet("padding: 0 8px;")
        self.statusbar.addPermanentWidget(self.line_col_label)

        sep3 = QLabel("|")
        sep3.setStyleSheet(f"padding: 0 4px; color: {t['border']};")
        self.statusbar.addPermanentWidget(sep3)

        self.memory_label = QLabel("MEM: -- MB")
        self.memory_label.setFont(mono(10))
        self.memory_label.setStyleSheet("padding: 0 8px;")
        self.statusbar.addPermanentWidget(self.memory_label)

        self.memory_timer = QTimer()
        self.memory_timer.timeout.connect(self.update_memory_info)
        self.memory_timer.start(2000)
        self.update_memory_info()

    def update_memory_info(self):
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_mb = process.memory_info().rss / 1024 / 1024
            self.memory_label.setText(f"MEM: {mem_mb:.1f} MB")
        except ImportError:
            try:
                import resource
                mem_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 / 1024
                self.memory_label.setText(f"MEM: {mem_mb:.1f} MB")
            except Exception:
                self.memory_label.setText("MEM: -- MB")
        except Exception:
            self.memory_label.setText("MEM: -- MB")

    def new_file(self):
        tabs = self.active_tab_widget()
        container = EditorContainer(self)
        container.file_path = None
        container.editor.file_path = "Untitled.spider"
        self._connect_editor_signals(container)

        index = tabs.addTab(container, "UNTITLED.SPIDER")
        tabs.setCurrentIndex(index)
        self._last_active_tabs = tabs
        self.status_label.setText("NEW FILE CREATED")

    def new_project(self):
        from spider_ide.ui.dialogs import Dialogs
        Dialogs.new_project(self, self)

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "",
            "Spider Files (*.spider);;All Files (*)"
        )
        if file_path:
            self.open_file(file_path)

    def open_project_dialog(self):
        from spider_ide.ui.dialogs import Dialogs
        Dialogs.open_project(self, self)

    def open_smart_dialog(self):
        dialog = FileOpenDialog(self)
        dialog.file_selected.connect(self.open_file)
        dialog.folder_selected.connect(self.open_project)
        dialog.exec()

    def open_file_in(self, tabs, file_path):
        if tabs is None:
            return
        for i in range(tabs.count()):
            container = tabs.widget(i)
            if isinstance(container, EditorContainer) and container.editor.file_path == file_path:
                tabs.setCurrentIndex(i)
                return
        try:
            container = EditorContainer(self, file_path)
            self._connect_editor_signals(container)
            file_name = Path(file_path).name.upper()
            tabs.addTab(container, file_name)
            tabs.setCurrentWidget(container)
            self.status_label.setText(f"OPENED: {file_name}")
            self.apply_editor_settings()
        except Exception as e:
            QMessageBox.critical(self, "ERROR", f"FAILED TO OPEN FILE:\n{e}")

    def open_file(self, file_path):
        for tabs in self.all_tab_widgets():
            for i in range(tabs.count()):
                container = tabs.widget(i)
                if isinstance(container, EditorContainer) and container.editor.file_path == file_path:
                    tabs.setCurrentIndex(i)
                    self._last_active_tabs = tabs
                    self.config.add_recent_file(file_path)
                    self.update_recent_files_menu(self.recent_files_menu)
                    return

        self.open_file_in(self.active_tab_widget(), file_path)
        self.config.add_recent_file(file_path)
        self.update_recent_files_menu(self.recent_files_menu)

    def open_project(self, project_path):
        try:
            self.sidebar.load_project(project_path)
            self.current_project = project_path
            self.config.add_recent_project(project_path)
            self.update_recent_projects_menu(self.recent_projects_menu)
            self.status_label.setText(f"PROJECT: {os.path.basename(project_path).upper()}")

            for root, dirs, files in os.walk(project_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
                for file in files:
                    if file.endswith('.spider'):
                        self.open_file(os.path.join(root, file))
                        return
        except Exception as e:
            QMessageBox.critical(self, "ERROR", f"FAILED TO OPEN PROJECT:\n{e}")

    def save_container(self, container):
        if not isinstance(container, EditorContainer):
            return False

        editor = container.editor
        if not editor.file_path or editor.file_path == "Untitled.spider":
            return self.save_container_as(container)

        if editor.save_file():
            self.status_label.setText(f"SAVED: {Path(editor.file_path).name.upper()}")
            self._update_tab_title(container)
            return True

        QMessageBox.critical(self, "ERROR", "FAILED TO SAVE FILE")
        return False

    def save_container_as(self, container):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "",
            "Spider Files (*.spider);;All Files (*)"
        )
        if not file_path:
            return False

        editor = container.editor
        if editor.save_file(file_path):
            container.file_path = file_path
            self.status_label.setText(f"SAVED: {Path(file_path).name.upper()}")
            self._update_tab_title(container)
            self.config.add_recent_file(file_path)
            self.update_recent_files_menu(self.recent_files_menu)
            return True

        QMessageBox.critical(self, "ERROR", "FAILED TO SAVE FILE")
        return False

    def save_file(self):
        container = self.active_tab_widget().currentWidget()
        self.save_container(container)

    def save_file_as(self):
        container = self.active_tab_widget().currentWidget()
        self.save_container_as(container)

    def close_tab(self, index):
        tabs = self.sender()
        if not isinstance(tabs, QTabWidget):
            tabs = self.active_tab_widget()
        if tabs is None or index < 0 or index >= tabs.count():
            return

        container = tabs.widget(index)
        if isinstance(container, EditorContainer):
            if container.editor.document().isModified():
                reply = QMessageBox.question(
                    self, "UNSAVED CHANGES",
                    f"SAVE CHANGES TO '{container.editor.file_path}'?",
                    QMessageBox.StandardButton.Save |
                    QMessageBox.StandardButton.Discard |
                    QMessageBox.StandardButton.Cancel
                )
                if reply == QMessageBox.StandardButton.Save:
                    if not self.save_container(container):
                        return
                elif reply == QMessageBox.StandardButton.Cancel:
                    return

        tabs.removeTab(index)
        if isinstance(container, QWidget):
            container.deleteLater()

        if self.tab_widget.count() == 0 and (self.tab_widget2 is None or self.tab_widget2.count() == 0):
            self.show_welcome_tab()

    def on_tab_changed(self, index):
        tabs = self.sender()
        if isinstance(tabs, QTabWidget):
            self._last_active_tabs = tabs
        if index < 0:
            return

        container = self.active_tab_widget().widget(index)
        if isinstance(container, EditorContainer):
            file_path = container.editor.file_path
            if file_path:
                self.status_label.setText(Path(file_path).name.upper())
            self.var_panel.update_variables(container.editor.toPlainText())
            if hasattr(container.editor, 'viewport'):
                set_editor_grid(container.editor.viewport(), self.theme, step=40)

    def toggle_split_view(self):
        if self.tab_widget2 is None:
            self.tab_widget2 = self._make_editor_tabs()
            self.editor_splitter.addWidget(self.tab_widget2)
            self.editor_splitter.setSizes([575, 575])

            container = self.tab_widget.currentWidget()
            if isinstance(container, EditorContainer):
                index = self.tab_widget.indexOf(container)
                title = self.tab_widget.tabText(index)
                self.tab_widget.removeTab(index)
                self.tab_widget2.addTab(container, title)
                self.tab_widget2.setCurrentWidget(container)
                self._last_active_tabs = self.tab_widget2

            if self.tab_widget.count() == 0:
                self.show_welcome_tab_in(self.tab_widget)

            self.status_label.setText("SPLIT VIEW ENABLED")
        else:
            right = self.tab_widget2
            while right.count() > 0:
                container = right.widget(0)
                title = right.tabText(0)
                right.removeTab(0)
                if isinstance(container, EditorContainer):
                    self.tab_widget.addTab(container, title)
                else:
                    container.deleteLater()

            right.deleteLater()
            self.tab_widget2 = None
            self._last_active_tabs = self.tab_widget

            if self.tab_widget.count() == 0:
                self.show_welcome_tab()
            else:
                self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)

            self.status_label.setText("SPLIT VIEW DISABLED")

    def show_find_replace(self):
        container = self.active_tab_widget().currentWidget()
        if isinstance(container, EditorContainer):
            container.show_find_replace()

    def show_project_search(self):
        dialog = ProjectSearchDialog(self, self.current_project, self.theme)
        dialog.file_open_requested.connect(self.open_file_at_line)
        dialog.exec()

    def open_file_at_line(self, file_path, line_num):
        self.open_file(file_path)

        for tabs in self.all_tab_widgets():
            for i in range(tabs.count()):
                container = tabs.widget(i)
                if isinstance(container, EditorContainer) and container.editor.file_path == file_path:
                    editor = container.editor
                    cursor = editor.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.Start)
                    cursor.movePosition(
                        QTextCursor.MoveOperation.Down,
                        QTextCursor.MoveMode.MoveAnchor,
                        max(0, line_num - 1)
                    )
                    editor.setTextCursor(cursor)
                    editor.centerCursor()
                    editor.setFocus()
                    return

    def auto_save_all(self):
        saved_count = 0
        for tabs in self.all_tab_widgets():
            for i in range(tabs.count()):
                container = tabs.widget(i)
                if isinstance(container, EditorContainer):
                    editor = container.editor
                    if editor.document().isModified() and editor.file_path and editor.file_path != "Untitled.spider":
                        if editor.save_file():
                            saved_count += 1
                            self._update_tab_title(container)

        if saved_count > 0:
            self.status_label.setText(f"AUTO-SAVED {saved_count} FILE(S)")
            QTimer.singleShot(2000, lambda: self.status_label.setText("READY"))

    def toggle_auto_save(self, enabled):
        self.config.set('auto_save_enabled', enabled)
        if enabled:
            self.auto_save_timer.start(self.auto_save_interval * 1000)
            self.status_label.setText(f"AUTO-SAVE ENABLED (EVERY {self.auto_save_interval}S)")
        else:
            self.auto_save_timer.stop()
            self.status_label.setText("AUTO-SAVE DISABLED")
        QTimer.singleShot(2000, lambda: self.status_label.setText("READY"))

    def goto_line(self):
        container = self.active_tab_widget().currentWidget()
        if not isinstance(container, EditorContainer):
            return

        line_num, ok = QInputDialog.getInt(
            self, "GO TO LINE", "LINE NUMBER:",
            container.editor.textCursor().blockNumber() + 1,
            1, container.editor.blockCount()
        )

        if ok:
            cursor = container.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(
                QTextCursor.MoveOperation.Down,
                QTextCursor.MoveMode.MoveAnchor,
                line_num - 1
            )
            container.editor.setTextCursor(cursor)
            container.editor.centerCursor()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.showFullScreen()
        else:
            self.showNormal()

    def toggle_console(self):
        self.console.setVisible(not self.console.isVisible())

    def toggle_terminal(self):
        self.terminal.setVisible(not self.terminal.isVisible())
        if self.terminal.isVisible():
            self.terminal.focus_input()

    def toggle_minimap(self):
        current = self.config.get('show_minimap', True)
        self.config.set('show_minimap', not current)
        self.apply_editor_settings()

    def undo(self):
        container = self.active_tab_widget().currentWidget()
        if isinstance(container, EditorContainer):
            container.editor.undo()

    def redo(self):
        container = self.active_tab_widget().currentWidget()
        if isinstance(container, EditorContainer):
            container.editor.redo()

    def run_code(self):
        self._start_execution(debug=False)

    def run_debug(self):
        self._start_execution(debug=True)

    def _start_execution(self, debug=False):
        container = self.active_tab_widget().currentWidget()
        if not isinstance(container, EditorContainer):
            QMessageBox.information(self, "INFO", "NO FILE TO RUN!")
            return

        editor = container.editor
        if not editor.file_path or editor.file_path == "Untitled.spider":
            QMessageBox.information(self, "INFO", "SAVE FILE FIRST!")
            return

        editor.save_file()
        self._update_tab_title(container)
        Runner.run(editor.file_path, self.console, debug=debug)

        if debug and Runner.debug_file:
            self.var_panel.enable_live_mode(Runner.debug_file)
        else:
            self.var_panel.disable_live_mode()

        self.status_label.setText("DEBUGGING..." if debug else "RUNNING...")

    def stop_code(self):
        Runner.stop()
        self.var_panel.disable_live_mode()
        self.console.write(">>> STOPPED\n", 'warning')
        self.status_label.setText("STOPPED")

    def show_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.apply_theme()

    def show_help(self):
        dialog = HelpDialog(self)
        dialog.exec()

    def show_about(self):
        QMessageBox.about(
            self, "About Spider IDE",
            "<h3>SPIDER.IDE v1.3</h3>"
            "<p>A modern IDE for Spider Script</p>"
            "<p>Built with PyQt6</p>"
            "<p>Features: Split View, Recent Files, Themes, Autocomplete, Minimap, Linter, Live Debug, Project Search, Auto-Save</p>"
        )

    def show_welcome_tab(self):
        self.show_welcome_tab_in(self.active_tab_widget())

    def show_welcome_tab_in(self, tabs):
        if tabs is None:
            return

        t = self.theme

        welcome = QWidget()
        welcome.setStyleSheet("background-color: transparent;")

        main_layout = QVBoxLayout(welcome)
        main_layout.setContentsMargins(60, 60, 60, 60)
        main_layout.setSpacing(24)

        top_bar = QHBoxLayout()
        top_bar.addWidget(logo_label(t, size=13, spacing=2))
        top_bar.addStretch()

        nav_items = ["DOCS", "GITHUB", "SETTINGS"]
        for item in nav_items:
            btn = QPushButton(item)
            btn.setFont(mono(10, bold=True, spacing=1))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {t['text_secondary']};
                    border: none;
                    padding: 4px 12px;
                }}
                QPushButton:hover {{
                    color: {t['text']};
                }}
            """)
            if item == "SETTINGS":
                btn.clicked.connect(self.show_settings)
            top_bar.addWidget(btn)

        main_layout.addLayout(top_bar)
        main_layout.addStretch()

        center_layout = QVBoxLayout()
        center_layout.setSpacing(16)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        badge = QLabel("INTEGRATED DEVELOPMENT ENVIRONMENT")
        badge.setFont(mono(10, bold=True, spacing=2))
        badge.setStyleSheet(f"""
            color: {t['text']};
            border: 1px solid {t['border']};
            padding: 6px 16px;
            background-color: transparent;
        """)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(badge)

        title = hero_title("SPIDER — СРЕДА РАЗРАБОТКИ\nДЛЯ ТЕХ, КТО ПИШЕТ БЫСТРО", t, size=32, spacing=4)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(title)

        desc = QLabel(
            "ЛЁГКАЯ, РАСШИРЯЕМАЯ IDE С ВСТРОЕННЫМ ИНТЕРПРЕТАТОРОМ,\n"
            "ИНТЕЛЛЕКТУАЛЬНЫМ АВТОДОПОЛНЕНИЕМ И ПОДДЕРЖКОЙ\n"
            "МНОЖЕСТВА ЯЗЫКОВ. ОТКРОЙТЕ ПРОЕКТ И НАЧНИТЕ ПИСАТЬ\n"
            "КОД ЗА СЕКУНДЫ."
        )
        desc.setFont(mono(11, spacing=1))
        desc.setStyleSheet(f"color: {t['text_secondary']}; background: transparent;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(desc)

        center_layout.addSpacing(20)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_download = outline_button("НОВЫЙ ФАЙЛ", t)
        btn_docs = outline_button("ОТКРЫТЬ ПРОЕКТ", t)

        btn_download.clicked.connect(self.new_file)
        btn_docs.clicked.connect(self.open_project_dialog)

        btn_layout.addWidget(btn_download)
        btn_layout.addWidget(btn_docs)

        center_layout.addLayout(btn_layout)
        main_layout.addLayout(center_layout)
        main_layout.addStretch()

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        features = [
            ("01", "БЫСТРЫЙ\nСТАРТ", "Откройте проект\nи пишите код"),
            ("02", "SPLIT VIEW", "Два файла\nодновременно"),
            ("03", "ОТЛАДКА", "Live-режим\nпеременных"),
            ("04", "ТЕРМИНАЛ", "Встроенная\nкомандная строка"),
        ]

        for num, title_text, desc_text in features:
            card = CardFrame(welcome, theme=t)
            card.setFixedSize(180, 120)

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 16, 16, 16)
            card_layout.setSpacing(6)
            card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            num_label = QLabel(num)
            num_label.setFont(mono(18, bold=True))
            num_label.setStyleSheet(f"color: {t['text_secondary']}; background: transparent;")

            title_label = QLabel(title_text)
            title_label.setFont(mono(11, bold=True, spacing=1))
            title_label.setStyleSheet(f"color: {t['text']}; background: transparent;")

            desc_label = QLabel(desc_text)
            desc_label.setFont(mono(9))
            desc_label.setStyleSheet(f"color: {t['text_secondary']}; background: transparent;")
            desc_label.setWordWrap(True)

            card_layout.addWidget(num_label)
            card_layout.addWidget(title_label)
            card_layout.addWidget(desc_label)
            card_layout.addStretch()

            cards_layout.addWidget(card)

        main_layout.addLayout(cards_layout)
        tabs.addTab(welcome, " WELCOME")
        tabs.setCurrentWidget(welcome) 