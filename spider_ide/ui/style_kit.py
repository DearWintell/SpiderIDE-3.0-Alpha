from PyQt6.QtWidgets import QWidget, QPushButton, QLabel, QFrame
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QPixmap, QBrush, QPalette


DARK_THEME = {
    'bg': '#0a0a0a',
    'surface': '#111111',
    'text': '#ffffff',
    'text_secondary': '#888888',
    'border': '#333333',
    'accent': '#ffffff',
    'accent_hover': '#cccccc',
    'grid': '#1e1e1e',
    'editor_bg': '#0a0a0a',
    'editor_fg': '#ffffff',
    'tab_active': '#0a0a0a',
    'tab_inactive': '#111111',
    'sidebar': '#0a0a0a',
    'button': '#111111',
    'button_hover': '#1a1a1a',
    'selection': '#ffffff',
    'line_highlight': '#1a1a1a',
    'error': '#ef4444',
    'warning': '#f59e0b',
    'success': '#4ade80',
    'keyword': '#7dd3fc',
    'command': '#4ade80',
    'string': '#fbbf24',
    'number': '#c084fc',
    'comment': '#6a9955',
    'param': '#e0e0e0',
    'special': '#f472b6',
    'function': '#7dd3fc',
    'operator': '#94a3b8',
}


LIGHT_THEME = {
    'bg': '#f0f0f0',
    'surface': '#ffffff',
    'text': '#1a1a1a',
    'text_secondary': '#666666',
    'border': '#c0c0c0',
    'accent': '#1a1a1a',
    'accent_hover': '#444444',
    'grid': '#e0e0e0',
    'editor_bg': '#ffffff',
    'editor_fg': '#1a1a1a',
    'tab_active': '#ffffff',
    'tab_inactive': '#e8e8e8',
    'sidebar': '#f5f5f5',
    'button': '#e0e0e0',
    'button_hover': '#d0d0d0',
    'selection': '#1a1a1a',
    'line_highlight': '#f5f5f5',
    'error': '#d32f2f',
    'warning': '#bf8803',
    'success': '#388e3c',
    'keyword': '#0000ff',
    'command': '#267f99',
    'string': '#a31515',
    'number': '#098658',
    'comment': '#008000',
    'param': '#001080',
    'special': '#af00db',
    'function': '#795e26',
    'operator': '#000000',
}


THEMES = {
    'brutal': DARK_THEME,
    'light': LIGHT_THEME,
}


def get_theme_by_name(name):
    return THEMES.get(name, DARK_THEME)


def make_grid_pixmap(theme, step=40):
    bg = QColor(theme.get('editor_bg', theme.get('bg', '#0a0a0a')))
    grid = QColor(theme.get('grid', '#1e1e1e'))

    pm = QPixmap(step, step)
    pm.fill(bg)

    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    pen = QPen(grid, 1)
    painter.setPen(pen)

    painter.drawLine(0, 0, step - 1, 0)
    painter.drawLine(0, 0, 0, step - 1)

    painter.end()
    return pm


def set_grid_background(widget, theme, step=40):
    widget.setAutoFillBackground(True)
    palette = widget.palette()
    brush = QBrush(make_grid_pixmap(theme, step))
    palette.setBrush(QPalette.ColorRole.Window, brush)
    widget.setPalette(palette)
    widget.update()


def set_editor_grid(viewport_or_editor, theme, step=40):
    editor = viewport_or_editor
    if hasattr(viewport_or_editor, 'parent') and isinstance(viewport_or_editor.parent(), QWidget):
        candidate = viewport_or_editor.parent()
        if hasattr(candidate, 'document'):
            editor = candidate

    editor.setAutoFillBackground(True)
    palette = editor.palette()
    brush = QBrush(make_grid_pixmap(theme, step))
    palette.setBrush(QPalette.ColorRole.Base, brush)
    palette.setBrush(QPalette.ColorRole.Window, brush)
    editor.setPalette(palette)

    if hasattr(editor, 'viewport'):
        vp = editor.viewport()
        vp.setAutoFillBackground(True)
        vp_palette = vp.palette()
        vp_palette.setBrush(QPalette.ColorRole.Base, brush)
        vp.setPalette(vp_palette)
        vp.update()

    editor.update()


def mono(size=12, bold=False, spacing=0):
    font = QFont("Consolas", size)
    font.setStyleHint(QFont.StyleHint.Monospace)
    if bold:
        font.setWeight(QFont.Weight.Bold)
    if spacing > 0:
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
    return font


def outline_button(text, theme, compact=False):
    btn = QPushButton(text)
    size = 10 if compact else 11
    padding_v = "4px 12px" if compact else "8px 20px"
    btn.setFont(mono(size, bold=True, spacing=1))
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: transparent;
            color: {theme['text']};
            border: 1px solid {theme['border']};
            padding: {padding_v};
            border-radius: 0px;
            font-family: "Consolas", monospace;
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
    return btn


class CardFrame(QWidget):
    def __init__(self, parent=None, theme=None):
        super().__init__(parent)
        self.theme = theme or DARK_THEME
        self.setStyleSheet(f"""
            CardFrame {{
                background-color: {self.theme['surface']};
                border: 1px solid {self.theme['border']};
            }}
        """)


def logo_label(theme, size=12, spacing=2):
    label = QLabel("// SPIDER.IDE")
    label.setFont(mono(size, bold=True, spacing=spacing))
    label.setStyleSheet(f"color: {theme['text']}; background: transparent;")
    return label


def hero_title(text, theme, size=32, spacing=4):
    label = QLabel(text)
    label.setFont(mono(size, bold=True, spacing=spacing))
    label.setStyleSheet(f"color: {theme['text']}; background: transparent;")
    label.setWordWrap(True)
    return label


def caption(text, theme):
    label = QLabel(text)
    label.setFont(mono(10, spacing=1))
    label.setStyleSheet(f"color: {theme['text_secondary']}; background: transparent;")
    return label 