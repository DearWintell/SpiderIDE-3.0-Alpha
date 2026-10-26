import os
import re
from PyQt6.QtWidgets import (
    QPlainTextEdit, QWidget, QListWidget, QListWidgetItem,
    QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton, QFrame, QApplication, QLabel
)
from PyQt6.QtCore import Qt, QRect, QSize, QTimer, QPoint
from PyQt6.QtGui import (
    QColor, QPainter, QTextCursor, QPen, QPolygon, QPalette
)

from spider_ide.core.code_folding import CodeFoldingManager
from spider_ide.ui.style_kit import DARK_THEME, mono, set_editor_grid


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        if self.width() <= 1 or self.height() <= 1:
            return

        theme = getattr(self.editor, 'theme', DARK_THEME)
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor(theme['bg']))

        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top())
        bottom = top + round(self.editor.blockBoundingRect(block).height())
        current_block_number = self.editor.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)

                if self.editor.folding_manager.has_fold(block_number):
                    region = self.editor.folding_manager.get_fold_at_line(block_number)
                    if region:
                        icon_x = 4
                        icon_y = top + (self.editor.fontMetrics().height() // 2) - 4
                        painter.setBrush(QColor(theme['accent']))
                        painter.setPen(Qt.PenStyle.NoPen)

                        if region.is_collapsed:
                            points = [QPoint(icon_x, icon_y), QPoint(icon_x + 8, icon_y + 4), QPoint(icon_x, icon_y + 8)]
                            painter.drawPolygon(QPolygon(points))
                        else:
                            points = [QPoint(icon_x, icon_y), QPoint(icon_x + 8, icon_y), QPoint(icon_x + 4, icon_y + 8)]
                            painter.drawPolygon(QPolygon(points))

                text_x = self.editor.fold_icons_width + 2
                if block_number == current_block_number:
                    painter.setPen(QColor(theme['text']))
                else:
                    painter.setPen(QColor(theme['text_secondary']))

                painter.drawText(text_x, top, self.width() - self.editor.fold_icons_width - 8, self.editor.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + round(self.editor.blockBoundingRect(block).height())
            block_number += 1


class Minimap(QWidget):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.setFixedWidth(100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

        self.hover_y = -1
        self.is_dragging = False
        self.LINE_HEIGHT = 2

        self.editor.updateRequest.connect(self.update)
        self.editor.blockCountChanged.connect(lambda _: self.update())
        self.editor.verticalScrollBar().valueChanged.connect(lambda: self.update())
        self.editor.textChanged.connect(self.update)
        self.editor.cursorPositionChanged.connect(lambda: self.update())

    def _analyze_block(self, text):
        if not text.strip():
            return None, 0
        indent = sum(4 if ch == '\t' else 1 for ch in text.split(text.lstrip())[0])
        stripped = text.strip()

        if stripped.startswith('#') or stripped.startswith('//'): return 'comment', indent
        elif stripped.startswith('func ') or stripped.startswith('function '): return 'function', indent
        elif stripped.startswith('class '): return 'class', indent
        elif any(kw in stripped for kw in ['if ', 'else:', 'elif ', 'while ', 'for ']): return 'keyword', indent
        elif any(cmd in stripped for cmd in ['print(', 'var ', 'window(', 'button(', 'text(']): return 'command', indent
        elif '"' in stripped or "'" in stripped: return 'string', indent
        elif any(c.isdigit() for c in stripped): return 'number', indent
        return 'default', indent

    def paintEvent(self, event):
        if self.width() <= 1 or self.height() <= 1:
            return

        theme = getattr(self.editor, 'theme', DARK_THEME)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.fillRect(self.rect(), QColor(theme['bg']))

        doc = self.editor.document()
        if doc.blockCount() == 0:
            return

        line_height = self.LINE_HEIGHT
        max_bar_width = self.width() * 0.6
        block = doc.begin()
        block_number = 0
        is_dark = theme['bg'].startswith('#0') or theme['bg'].startswith('#1')

        color_map = {
            'comment': theme['text_secondary'],
            'keyword': theme.get('keyword', '#7dd3fc') if is_dark else '#005f87',
            'function': theme.get('function', '#7dd3fc') if is_dark else '#795e26',
            'command': theme.get('command', '#4ade80') if is_dark else '#267f99',
            'string': theme.get('string', '#fbbf24') if is_dark else '#a31515',
            'number': theme.get('number', '#c084fc') if is_dark else '#098658',
            'param': theme['text'],
            'class': theme.get('special', '#f472b6') if is_dark else '#af00db',
        }

        while block.isValid() and block_number * line_height < self.height():
            text = block.text()
            block_type, indent = self._analyze_block(text)

            if block_type:
                y = block_number * line_height
                content_len = len(text.strip())
                bar_width = max(2, min(content_len * 0.4, max_bar_width - indent * 0.5))
                bar_x = 2 + indent * 0.5
                bar_height = max(1, line_height - 0.5)

                color = color_map.get(block_type, theme['text_secondary'])
                painter.fillRect(int(bar_x), int(y), int(bar_width), int(bar_height), QColor(color))

            block = block.next()
            block_number += 1

        scrollbar = self.editor.verticalScrollBar()
        if scrollbar.maximum() > 0:
            total_range = scrollbar.maximum() - scrollbar.minimum()
            visible_range = scrollbar.pageStep()
            current_pos = scrollbar.value()

            scale = self.height() / (total_range + visible_range)
            viewport_rect = QRect(0, int(current_pos * scale), self.width(), int(visible_range * scale))

            accent = QColor(theme['accent'])
            accent.setAlpha(30)
            painter.fillRect(viewport_rect, accent)
            painter.setPen(QPen(QColor(theme['accent']), 1))
            painter.drawRect(viewport_rect)

        if self.hover_y >= 0 and not self.is_dragging:
            hover_rect = QRect(0, int(self.hover_y - 5), self.width(), 10)
            hover_color = QColor(theme['text'])
            hover_color.setAlpha(15)
            painter.fillRect(hover_rect, hover_color)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.jump_to_position(event.pos().y())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False

    def mouseMoveEvent(self, event):
        self.hover_y = event.pos().y()
        if self.is_dragging:
            self.jump_to_position(event.pos().y())
        self.update()

    def leaveEvent(self, event):
        self.hover_y = -1
        self.update()

    def jump_to_position(self, y_pos):
        block_index = max(0, min(int(y_pos / self.LINE_HEIGHT), self.editor.document().blockCount() - 1))
        block = self.editor.document().begin()
        for _ in range(block_index):
            block = block.next()
            if not block.isValid():
                break

        if block.isValid():
            self.editor.setTextCursor(QTextCursor(block))
            self.editor.centerCursor()


class FindReplaceWidget(QFrame):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.theme = DARK_THEME
        self.setVisible(False)
        self.match_count = 0
        self.current_match = 0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("FIND...")
        self.find_input.setFont(mono(11))
        self.find_input.setMinimumWidth(180)
        self.find_input.textChanged.connect(self.on_find_changed)
        self.find_input.returnPressed.connect(self.find_next)
        layout.addWidget(self.find_input)

        self.count_label = QLabel("0/0")
        self.count_label.setFont(mono(10, bold=True, spacing=1))
        self.count_label.setMinimumWidth(50)
        layout.addWidget(self.count_label)

        prev_btn = QPushButton("◀")
        prev_btn.setFont(mono(10, bold=True))
        prev_btn.setFixedWidth(30)
        prev_btn.clicked.connect(self.find_prev)
        layout.addWidget(prev_btn)

        next_btn = QPushButton("▶")
        next_btn.setFont(mono(10, bold=True))
        next_btn.setFixedWidth(30)
        next_btn.clicked.connect(self.find_next)
        layout.addWidget(next_btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        sep.setFixedHeight(20)
        layout.addWidget(sep)

        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("REPLACE...")
        self.replace_input.setFont(mono(11))
        self.replace_input.setMinimumWidth(180)
        layout.addWidget(self.replace_input)

        replace_btn = QPushButton("REPLACE")
        replace_btn.setFont(mono(10, bold=True, spacing=1))
        replace_btn.clicked.connect(self.replace_current)
        layout.addWidget(replace_btn)

        replace_all_btn = QPushButton("ALL")
        replace_all_btn.setFont(mono(10, bold=True, spacing=1))
        replace_all_btn.clicked.connect(self.replace_all)
        layout.addWidget(replace_all_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setFont(mono(10, bold=True))
        self.close_btn.setFixedWidth(25)
        self.close_btn.clicked.connect(self.hide_and_clear)
        layout.addWidget(self.close_btn)
        layout.addStretch()
        self.apply_theme()

    def apply_theme(self, theme=None):
        if theme is None: theme = DARK_THEME
        self.theme = theme

        self.setStyleSheet(f"""
            FindReplaceWidget {{
                background-color: {theme['surface']};
                border: 1px solid {theme['border']};
                border-radius: 0px;
                padding: 4px;
            }}
            QLineEdit {{
                background-color: {theme['bg']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                padding: 4px 8px;
                border-radius: 0px;
                font-family: "Consolas", monospace;
                font-size: 12px;
            }}
            QLineEdit:focus {{ border: 1px solid {theme['accent']}; }}
            QPushButton {{
                background-color: transparent;
                color: {theme['text_secondary']};
                border: 1px solid {theme['border']};
                padding: 4px 10px;
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
            QLabel {{ color: {theme['text_secondary']}; font-size: 11px; padding: 0 4px; background: transparent; }}
        """)
        self.close_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {theme['text_secondary']}; border: none; }}
            QPushButton:hover {{ background-color: #ef4444; color: {theme['bg']}; }}
        """)

    def show_find(self):
        self.setVisible(True)
        self.find_input.setFocus()
        self.find_input.selectAll()
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            self.find_input.setText(cursor.selectedText())
        self.on_find_changed(self.find_input.text())

    def hide_and_clear(self):
        self.setVisible(False)
        self.clear_highlights()
        self.editor.setFocus()

    def on_find_changed(self, text):
        if not text:
            self.count_label.setText("0/0")
            self.clear_highlights()
            return
        self.find_all_matches()

    def find_all_matches(self):
        self.clear_highlights()
        text = self.find_input.text()
        if not text:
            self.match_count = 0
            self.current_match = 0
            self.count_label.setText("0/0")
            return

        doc = self.editor.document()
        cursor = doc.find(text, 0)
        matches = []
        while not cursor.isNull():
            matches.append(cursor.selectionStart())
            cursor = doc.find(text, cursor)

        self.match_count = len(matches)
        highlight_cursor = QTextCursor(doc)
        for pos in matches:
            highlight_cursor.setPosition(pos)
            highlight_cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, len(text))
            fmt = highlight_cursor.charFormat()
            fmt.setBackground(QColor(self.theme['accent']))
            fmt.setForeground(QColor(self.theme['bg']))
            highlight_cursor.setCharFormat(fmt)

        current_pos = self.editor.textCursor().position()
        self.current_match = 0
        for i, pos in enumerate(matches):
            if pos >= current_pos:
                self.current_match = i
                break

        self.count_label.setText(f"{self.current_match + 1}/{self.match_count}" if self.match_count > 0 else "0/0")

    def find_next(self):
        if self.match_count == 0: return
        self.current_match = (self.current_match + 1) % self.match_count
        self.jump_to_current_match()

    def find_prev(self):
        if self.match_count == 0: return
        self.current_match = (self.current_match - 1) % self.match_count
        self.jump_to_current_match()

    def jump_to_current_match(self):
        text = self.find_input.text()
        if not text: return
        doc = self.editor.document()
        cursor = doc.find(text, 0)
        matches = []
        while not cursor.isNull():
            matches.append(cursor.selectionStart())
            cursor = doc.find(text, cursor)

        if 0 <= self.current_match < len(matches):
            pos = matches[self.current_match]
            new_cursor = QTextCursor(doc)
            new_cursor.setPosition(pos)
            new_cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, len(text))
            self.editor.setTextCursor(new_cursor)
            self.editor.centerCursor()
            self.count_label.setText(f"{self.current_match + 1}/{self.match_count}")

    def replace_current(self):
        cursor = self.editor.textCursor()
        if cursor.hasSelection() and cursor.selectedText() == self.find_input.text():
            cursor.insertText(self.replace_input.text())
        self.find_next()
        self.on_find_changed(self.find_input.text())

    def replace_all(self):
        text = self.find_input.text()
        replace_text = self.replace_input.text()
        if not text: return
        doc = self.editor.document()
        cursor = doc.find(text, 0)
        cursor.beginEditBlock()
        while not cursor.isNull():
            cursor.insertText(replace_text)
            cursor = doc.find(text, cursor)
        cursor.endEditBlock()
        self.on_find_changed(self.find_input.text())

    def clear_highlights(self):
        doc = self.editor.document()
        cursor = QTextCursor(doc)
        cursor.select(QTextCursor.SelectionType.Document)
        fmt = cursor.charFormat()
        fmt.setBackground(QColor(0, 0, 0, 0))
        fmt.setForeground(QColor(0, 0, 0, 0))
        cursor.setCharFormat(fmt)
        if hasattr(self.editor, 'highlighter') and self.editor.highlighter:
            self.editor.highlighter.rehighlight()


class CompletionPopup(QListWidget):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.theme = DARK_THEME
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setIconSize(QSize(20, 20))
        self.setFont(mono(12))
        self.itemClicked.connect(self.on_item_clicked)
        self.apply_theme()

    def apply_theme(self, theme=None):
        if theme is None: theme = DARK_THEME
        self.theme = theme
        self.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme['surface']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                font-family: "Consolas", monospace;
                font-size: 12px;
                outline: none;
            }}
            QListWidget::item {{ padding: 4px 8px; border: none; }}
            QListWidget::item:selected {{ background-color: {theme['accent']}; color: {theme['bg']}; }}
            QListWidget::item:hover {{ background-color: {theme['bg']}; }}
        """)

    def on_item_clicked(self, item):
        self.editor.insert_completion(item)


class SpiderEditor(QPlainTextEdit):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.file_path = None
        self.highlighter = None
        self.theme = DARK_THEME

        self.setFont(mono(14))
        self.setTabStopDistance(40)

        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.on_cursor_changed)

        self.folding_manager = CodeFoldingManager()
        self.fold_icons_width = 16
        self.update_line_number_area_width(0)

        self.popup = CompletionPopup(self)
        self.popup.setVisible(False)
        self.completion_prefix = ""

        self.completions = {
            'Spider': '', 'Start': '', 'End': '', 'if': '', 'else': '', 'elif': '',
            'func': '', 'return': '', 'param': '', 'loop': '', 'while': '', 'for': '',
            'break': '', 'continue': '', 'window': '', 'button': '', 'text': '', 'textv': '',
            'shape': '', 'image': '', 'input': '', 'checkbox': '', 'slider': '', 'dropdown': '',
            'move': '', 'bind': '', 'clear': '', 'show': '', 'hide': '', 'destroy': '',
            'focus': '', 'update': '', 'var': '', 'print': '', 'array': '', 'dict': '',
            'string': '', 'number': '', 'boolean': '', 'color': '', 'size': '', 'x': '', 'y': '',
            'id': '', 'width': '', 'height': '', 'bg': '', 'fg': '', 'font': '',
            'type': '', 'key': '', 'title': '', 'visible': '', 'enabled': '',
            'click': '', 'hover': '', 'keypress': '', 'change': '', 'focus_in': '', 'focus_out': '',
            'wait': '', 'check': '', 'action': '', 'import': '', 'export': '', 'true': '', 'false': '', 'None': '',
        }

        self.snippets = {
            'for': 'for ${1:i} in range(${2:10}):\n    ${3:pass}',
            'while': 'while ${1:condition}:\n    ${2:pass}',
            'if': 'if ${1:condition}:\n    ${2:pass}',
            'elif': 'elif ${1:condition}:\n    ${2:pass}',
            'else': 'else:\n    ${1:pass}',
            'func': 'func ${1:name}(${2:params}):\n    ${3:return value}',
            'loop': 'loop:\n    ${1:pass}',
            'Spider': 'Spider(Start)\n${1:    \n}End',
            'window': 'window(title="${1:My Window}", width=${2:800}, height=${3:600}, bg="${4:#0a0a0a}")',
            'button': 'button(id="${1:btn1}", text="${2:Click}", x=${3:0}, y=${4:0})',
            'print': 'print("${1:message}")',
            'var': 'var(${1:x}=${2:5})', 
        }

        self.auto_close_pairs = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'"}

        self.linter_timer = QTimer()
        self.linter_timer.setSingleShot(True)
        self.linter_timer.setInterval(500)
        self.linter_timer.timeout.connect(self.run_linter)
        self.textChanged.connect(self.on_text_changed)
        self.linter_errors = []

        self._show_popup_timer = QTimer()
        self._show_popup_timer.setSingleShot(True)
        self._show_popup_timer.setInterval(50)
        self._show_popup_timer.timeout.connect(self._do_show_popup)
        self._pending_popup = False

        self.apply_theme(getattr(main_window, 'theme', DARK_THEME)) 

    def apply_theme(self, theme=None):
        if theme is None: theme = DARK_THEME
        self.theme = theme

        self.setStyleSheet(f"""
            QPlainTextEdit {{
                color: {theme['text']};
                border: none;
                selection-background-color: {theme['accent']};
                selection-color: {theme['bg']};
            }}
        """)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Text, QColor(theme['text']))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(theme['accent']))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(theme['bg']))
        self.setPalette(palette)

        if self.highlighter:
            self.highlighter.apply_theme(theme)

        set_editor_grid(self, theme, step=40)
        if hasattr(self, 'line_number_area'):
            self.line_number_area.update()
        self.update() 

    def on_cursor_changed(self):
        cursor = self.textCursor()
        if hasattr(self.main_window, 'line_col_label'):
            self.main_window.line_col_label.setText(f"LN {cursor.blockNumber() + 1}, COL {cursor.columnNumber() + 1}")

    def line_number_area_width(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        return self.fold_icons_width + 10 + self.fontMetrics().horizontalAdvance('9') * (digits + 1)

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            click_x = event.position().x()
            if 0 <= click_x <= self.fold_icons_width:
                line_num = self.cursorForPosition(event.position().toPoint()).blockNumber()
                if self.folding_manager.has_fold(line_num):
                    self.toggle_fold_at_line(line_num)
                    return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if self.popup.isVisible():
            if event.key() == Qt.Key.Key_Escape:
                self.popup.hide()
                super().keyPressEvent(event)
                return
            elif event.key() == Qt.Key.Key_Up:
                row = self.popup.currentRow()
                if row > 0: self.popup.setCurrentRow(row - 1)
                return
            elif event.key() == Qt.Key.Key_Down:
                row = self.popup.currentRow()
                if row < self.popup.count() - 1: self.popup.setCurrentRow(row + 1)
                return
            elif event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Tab):
                item = self.popup.currentItem()
                if item: self.insert_completion(item)
                return

        text = event.text()
        if text in self.auto_close_pairs:
            cursor = self.textCursor()
            if cursor.hasSelection():
                cursor.insertText(text + cursor.selectedText() + self.auto_close_pairs[text])
                return
            if text in ('"', "'"):
                if self.get_char_after_cursor() == text:
                    cursor.movePosition(QTextCursor.MoveOperation.Right)
                    self.setTextCursor(cursor)
                    return
            super().keyPressEvent(event)
            self.insertPlainText(self.auto_close_pairs[text])
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Left)
            self.setTextCursor(cursor)
            return

        if text in (')', ']', '}'):
            if self.get_char_after_cursor() == text:
                cursor = self.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.Right)
                self.setTextCursor(cursor)
                return

        if event.key() == Qt.Key.Key_Backspace:
            cursor = self.textCursor()
            if not cursor.hasSelection():
                prev_char = self.get_char_before_cursor()
                next_char = self.get_char_after_cursor()
                if prev_char in self.auto_close_pairs and self.auto_close_pairs[prev_char] == next_char:
                    cursor.deleteChar()
                    cursor.deletePreviousChar()
                    return

        if event.key() == Qt.Key.Key_Tab:
            cursor = self.textCursor()
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            word = cursor.selectedText()
            if word in self.snippets:
                snippet = self.snippets[word]
                match = re.search(r'\$\{1:([^}]+)\}', snippet)
                if match:
                    placeholder_text = match.group(1)
                    clean_snippet = snippet.replace(f'${{1:{placeholder_text}}}', placeholder_text)
                    cursor.insertText(clean_snippet)
                    cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, len(placeholder_text))
                    self.setTextCursor(cursor)
                else:
                    cursor.insertText(snippet)
                return
            else:
                cursor.insertText('    ')
                return

        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            cursor = self.textCursor()
            text = cursor.block().text()
            indent = ""
            for ch in text:
                if ch in (' ', '\t'): indent += ch
                else: break
            stripped = text.rstrip()
            if stripped.endswith(':') or stripped.endswith('(') or stripped.endswith('{'):
                indent += '    '
            super().keyPressEvent(event)
            if indent: self.insertPlainText(indent)
            return

        super().keyPressEvent(event)
        if text and (text.isalpha() or text == '_'):
            self.update_completions()
        else:
            self.popup.hide()

    def get_char_before_cursor(self):
        cursor = self.textCursor()
        if cursor.atBlockStart(): return ''
        cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor)
        return cursor.selectedText()

    def get_char_after_cursor(self):
        cursor = self.textCursor()
        if cursor.atBlockEnd(): return ''
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor)
        return cursor.selectedText()

    def update_completions(self):
        try:
            cursor = self.textCursor()
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            word = cursor.selectedText()
            if len(word) < 1:
                self.popup.hide()
                return

            text = self.toPlainText()
            dynamic_vars = re.findall(r'var\s+([a-zA-Z_]\w*)\s*=', text)
            dynamic_funcs = re.findall(r'func\s+([a-zA-Z_]\w*)\s*\(', text)

            all_completions = set(self.completions.keys()) | set(dynamic_vars) | set(dynamic_funcs)
            filtered = [k for k in all_completions if k.lower().startswith(word.lower()) and k != word]
            filtered.sort(key=lambda x: (not x.lower().startswith(word.lower()), x.lower()))

            if not filtered:
                self.popup.hide()
                return

            self.popup.clear()
            self.completion_prefix = word
            for name in filtered[:15]:
                icon = '📦' if name in dynamic_vars else '⚙️' if name in dynamic_funcs else '🕸️'
                item = QListWidgetItem(f" {icon}  {name}")
                item.setData(Qt.ItemDataRole.UserRole, name)
                self.popup.addItem(item)

            self.popup.setCurrentRow(0)
            self.position_popup()
            self._pending_popup = True
            self._show_popup_timer.start()
        except Exception:
            self.popup.hide()

    def _do_show_popup(self):
        if self._pending_popup:
            self.popup.show()
            self.setFocus()
            self._pending_popup = False

    def position_popup(self):
        try:
            cursor_rect = self.cursorRect()
            popup_size = self.popup.sizeHint()
            x = self.mapToGlobal(cursor_rect.bottomLeft()).x()
            y = self.mapToGlobal(cursor_rect.bottomLeft()).y() + 2
            screen = QApplication.primaryScreen().geometry()
            if x + popup_size.width() > screen.right():
                x = screen.right() - popup_size.width() - 10
            self.popup.setGeometry(x, y, max(250, popup_size.width()), min(300, popup_size.height()))
        except Exception:
            pass

    def insert_completion(self, item):
        if not item: return
        word = item.data(Qt.ItemDataRole.UserRole)
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.insertText(word)
        self.setTextCursor(cursor)
        self.popup.hide()
        self.setFocus()

    def on_text_changed(self):
        self.linter_timer.start()
        self.update_folding()

    def run_linter(self):
        try:
            from spider_runtime.parser import SpiderParser
            code = self.toPlainText()
            parser = SpiderParser()
            if hasattr(parser, 'parse'):
                self.set_linter_errors(parser.parse(code))
            else:
                self.run_simple_linter()
        except Exception:
            self.run_simple_linter()

    def run_simple_linter(self):
        errors = []
        lines = self.toPlainText().split('\n')
        known_commands = {'var', 'print', 'window', 'button', 'text', 'textv', 'shape', 'move', 'clear', 'wait', 'check', 'bind', 'title', 'if', 'else', 'elif', 'while', 'for', 'loop', 'break', 'continue', 'return', 'func'}
        open_parens = open_brackets = open_braces = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#') or stripped.startswith('//'):
                continue

            cmd_match = re.match(r'^([a-zA-Z_]\w*)\s*\(', stripped)
            if cmd_match:
                cmd = cmd_match.group(1)
                if cmd not in known_commands and cmd != 'Spider':
                    errors.append((i, f"Unknown command: '{cmd}'"))

            in_string = False
            string_char = None
            for j, ch in enumerate(stripped):
                if ch in ('"', "'") and (j == 0 or stripped[j-1] != '\\'):
                    if not in_string:
                        in_string = True
                        string_char = ch
                    elif ch == string_char:
                        in_string = False
            if in_string:
                errors.append((i, "Unclosed string literal"))

            for ch in stripped:
                if ch == '(':
                    open_parens += 1
                elif ch == ')':
                    open_parens -= 1
                elif ch == '[':
                    open_brackets += 1
                elif ch == ']':
                    open_brackets -= 1
                elif ch == '{':
                    open_braces += 1
                elif ch == '}':
                    open_braces -= 1

        if open_parens != 0:
            msg = "more '('" if open_parens > 0 else "more ')'"
            errors.append((len(lines), f"Unbalanced parentheses: {msg}"))

        if open_brackets != 0:
            msg = "more '['" if open_brackets > 0 else "more ']'"
            errors.append((len(lines), f"Unbalanced brackets: {msg}"))

        if open_braces != 0:
            msg = "more '{'" if open_braces > 0 else "more '}'"
            errors.append((len(lines), f"Unbalanced braces: {msg}"))

        self.set_linter_errors(errors)

    def set_linter_errors(self, errors):
        self.linter_errors = errors
        if hasattr(self.main_window, 'console'):
            self.main_window.console.clear_errors()
            for line, msg in errors:
                self.main_window.console.add_error(line, msg)
        if self.highlighter:
            if hasattr(self.highlighter, 'set_errors'):
                self.highlighter.set_errors(errors)
            else:
                self.highlighter.rehighlight()

    def update_folding(self):
        self.folding_manager.analyze_code(self.toPlainText())
        self._apply_folding()
        self.update_line_number_area_width(0)
        self.viewport().update()

    def toggle_fold_at_line(self, line_number: int):
        region = self.folding_manager.toggle_fold(line_number)
        if region:
            self._apply_folding()
            self.update()

    def _apply_folding(self):
        block = self.document().firstBlock()
        while block.isValid():
            block.setVisible(True)
            block = block.next()
        for line_num in self.folding_manager.collapsed_lines:
            block = self.document().findBlockByLineNumber(line_num)
            if block.isValid(): block.setVisible(False)
        self.document().markContentsDirty(0, self.document().characterCount())

    def load_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.setPlainText(f.read())
            self.file_path = file_path
            self.document().setModified(False)
            self.run_linter()
            return True
        except Exception:
            return False

    def save_file(self, file_path=None):
        path = file_path or self.file_path
        if not path: return False
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.toPlainText())
            self.file_path = path
            self.document().setModified(False)
            return True
        except Exception:
            return False

    def get_content(self): return self.toPlainText()
    def set_content(self, content):
        self.setPlainText(content)
        self.document().setModified(False)


class EditorContainer(QWidget):
    def __init__(self, main_window, file_path=None):
        super().__init__()
        self.main_window = main_window
        self.file_path = file_path

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.editor = SpiderEditor(main_window)
        self.find_replace = FindReplaceWidget(self.editor)
        self.editor.find_replace = self.find_replace

        inner = QWidget()
        inner.setStyleSheet("background-color: transparent;")
        inner_layout = QHBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(0)

        editor_vbox = QWidget()
        editor_vbox.setStyleSheet("background-color: transparent;")
        vbox = QVBoxLayout(editor_vbox)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(self.find_replace)
        vbox.addWidget(self.editor, 1)
        inner_layout.addWidget(editor_vbox, 1)

        self.minimap = Minimap(self.editor)
        inner_layout.addWidget(self.minimap)
        layout.addWidget(inner, 1)

        try:
            from spider_ide.core.syntax import SpiderSyntaxHighlighter
            self.editor.highlighter = SpiderSyntaxHighlighter(self.editor.document())
            self.editor.highlighter.apply_theme(self.editor.theme)
        except ImportError: 
            pass

        if file_path and os.path.isfile(file_path):
            self.editor.load_file(file_path)
        self.apply_theme(getattr(main_window, 'theme', DARK_THEME)) 

    def apply_theme(self, theme=None):
        if theme is None:
            theme = getattr(self.main_window, 'theme', DARK_THEME)
        self.editor.apply_theme(theme)
        self.find_replace.apply_theme(theme)
        self.minimap.update()

    def show_find_replace(self):
        self.find_replace.show_find()

    def hide_find_replace(self):
        self.find_replace.hide_and_clear() 