from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QLineEdit, QPlainTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCharFormat, QColor, QTextCursor

from spider_ide.ui.style_kit import DARK_THEME, mono


class Terminal(QWidget):
    command_executed = pyqtSignal(str)

    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.theme = DARK_THEME
        self.history = []
        self.history_index = -1
        self.current_input = ""
        self.is_processing = False
        self.prompt = "// SPIDER> "
        self.prompt_length = len(self.prompt)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header = QFrame()
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(12, 8, 12, 8)

        self.header_label = QLabel("// TERMINAL")
        self.header_label.setFont(mono(10, bold=True, spacing=1))
        self.header_layout.addWidget(self.header_label)
        self.header_layout.addStretch()

        self.clear_btn = QLabel("[CLEAR]")
        self.clear_btn.setFont(mono(10, bold=True, spacing=1))
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.mousePressEvent = lambda event: self.clear_terminal()
        self.header_layout.addWidget(self.clear_btn)

        layout.addWidget(self.header)

        self.line = QFrame()
        self.line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(self.line)

        self.output = TerminalOutput(self)
        self.output.setFont(mono(12))
        layout.addWidget(self.output)

        self.input_line = TerminalInput(self)
        self.input_line.setFont(mono(12))
        self.input_line.setPlaceholderText(self.prompt)

        self.input_line.returnPressed.connect(self.execute_command)
        self.input_line.upPressed.connect(self.history_up)
        self.input_line.downPressed.connect(self.history_down)

        layout.addWidget(self.input_line)

        self.apply_theme()
        self.welcome_message()

    def apply_theme(self, theme=None):
        if theme is None:
            theme = DARK_THEME
        self.theme = theme

        self.header_label.setStyleSheet(
            f"color: {theme['text_secondary']}; background: transparent;"
        )

        self.clear_btn.setStyleSheet(f"""
            QLabel {{
                color: {theme['text_secondary']};
                background: transparent;
            }}
            QLabel:hover {{
                color: {theme['accent']};
            }}
        """)

        self.line.setStyleSheet(
            f"background-color: {theme['border']}; max-height: 1px;"
        )

        self.input_line.setStyleSheet(f"""
            QLineEdit {{
                background-color: {theme['surface']};
                color: {theme['text']};
                border: none;
                border-top: 1px solid {theme['border']};
                padding: 8px 12px;
                font-family: "Consolas", monospace;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border-top: 1px solid {theme['accent']};
            }}
        """)

        self.output.apply_theme(theme)

    def welcome_message(self):
        self.write_output("SPIDER TERMINAL v1.3", "info")
        self.write_output("Type 'help' for available commands.", "info")
        self.write_output("", "normal")

    def write_output(self, text, tag="normal"):
        self.output.write(text + "\n", tag)

    def execute_command(self):
        command = self.input_line.text().strip()

        if not command:
            return

        self.input_line.clear()
        self.history.append(command)
        self.history_index = len(self.history)

        self.write_output(f"{self.prompt}{command}", "command")

        command_lower = command.lower()

        if command_lower in ("clear", "cls"):
            self.clear_terminal()
            return

        if command_lower == "help":
            self.show_help()
            return

        if command_lower in ("exit", "quit"):
            self.write_output("Terminal session ended.", "info")
            return

        if command_lower == "version":
            self.write_output("Spider IDE v1.3 | Runtime v1.0", "info")
            return

        if command_lower.startswith("run "):
            file_path = command[4:].strip().strip('"').strip("'")
            self.run_file(file_path)
            return

        self.run_code(command)
        self.command_executed.emit(command)

    def run_code(self, code):
        try:
            from spider_runtime.executor import Executor
            executor = Executor()
            result = executor.execute(code)
            if result is not None:
                self.write_output(str(result), "success")
        except ImportError:
            try:
                from spider_runtime.spider import SpiderInterpreter
                interpreter = SpiderInterpreter()
                result = interpreter.run(code)
                if result is not None:
                    self.write_output(str(result), "success")
            except Exception as error:
                self.write_output(f"Runtime error: {error}", "error")
        except Exception as error:
            self.write_output(f"Error: {error}", "error")

    def run_file(self, file_path):
        import os
        if not os.path.exists(file_path):
            self.write_output(f"File not found: {file_path}", "error")
            return

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                code = file.read()
            self.write_output(f"Running {os.path.basename(file_path)}...", "info")
            self.run_code(code)
        except Exception as error:
            self.write_output(f"Error: {error}", "error")

    def show_help(self):
        self.write_output("Available commands:", "info")
        self.write_output("  help          - Show this help", "normal")
        self.write_output("  clear / cls   - Clear terminal", "normal")
        self.write_output("  run <file>    - Run a .spider file", "normal")
        self.write_output("  version       - Show version", "normal")
        self.write_output("  exit / quit   - End session", "normal")
        self.write_output("", "normal")
        self.write_output("Or type any Spider code to execute it directly.", "info")

    def history_up(self):
        if not self.history:
            return
        if self.history_index > 0:
            self.history_index -= 1
        command = self.history[self.history_index]
        self.input_line.setText(command)
        self.input_line.setCursorPosition(len(command))

    def history_down(self):
        if not self.history:
            return
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            command = self.history[self.history_index]
            self.input_line.setText(command)
            self.input_line.setCursorPosition(len(command))
        else:
            self.history_index = len(self.history)
            self.input_line.clear()

    def clear_terminal(self):
        self.output.clear()

    def focus_input(self):
        self.input_line.setFocus()


class TerminalOutput(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(1000)
        self.setFont(mono(12))
        self.theme = DARK_THEME
        self.apply_theme()

    def apply_theme(self, theme=None):
        if theme is None:
            theme = DARK_THEME
        self.theme = theme

        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {theme['bg']};
                color: {theme['text']};
                border: none;
                padding: 12px;
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
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme['text_secondary']};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        self.formats = {
            "normal": self._create_format(theme["text"]),
            "command": self._create_format("#7dd3fc", bold=True),
            "error": self._create_format(theme.get("error", "#ef4444")),
            "success": self._create_format(theme.get("success", "#4ade80")),
            "info": self._create_format(theme["text_secondary"]),
        }

    def _create_format(self, color_hex, bold=False):
        text_format = QTextCharFormat()
        text_format.setForeground(QColor(color_hex))
        text_format.setFont(mono(12, bold=bold))
        return text_format

    def write(self, text, tag="normal"):
        text_format = self.formats.get(tag, self.formats["normal"])
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text, text_format)
        self.setTextCursor(cursor)
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear(self):
        super().clear()


class TerminalInput(QLineEdit):
    upPressed = pyqtSignal()
    downPressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up:
            self.upPressed.emit()
        elif event.key() == Qt.Key.Key_Down:
            self.downPressed.emit()
        else:
            super().keyPressEvent(event) 