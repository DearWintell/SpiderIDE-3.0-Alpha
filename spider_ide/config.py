from spider_ide.core.config import Config
from spider_ide.ui.style_kit import DARK_THEME

THEMES = {'brutal': DARK_THEME}

FONTS = {
    'editor': {'family': 'Consolas', 'size': 14},
    'ui': {'family': 'Consolas', 'size': 10},
    'monospace': ['Consolas', 'Courier New', 'Monaco', 'DejaVu Sans Mono', 'JetBrains Mono'],
}

__all__ = ['Config', 'THEMES', 'FONTS'] 