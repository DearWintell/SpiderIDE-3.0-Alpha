import json
from pathlib import Path


class Config:
    def __init__(self):
        self.settings_dir = Path.home() / '.spider_ide'
        self.settings_file = self.settings_dir / 'settings.json'
        self.data = {}
        self.load()

    def default_config(self):
        return {
            'theme': 'brutal',
            'font_family': 'Consolas',
            'font_size': 14,
            'tab_size': 4,
            'use_spaces': True,
            'auto_close_brackets': True,
            'auto_indent': True,
            'show_minimap': True,
            'show_line_numbers': True,
            'show_indent_guides': True,
            'auto_save_enabled': False,
            'auto_save_interval': 30,
            'restore_session': True,
            'animations': True,
            'interpreter_path': '',
            'recent_files': [],
            'recent_projects': [],
            'session_files': '[]',
            'window_geometry': None,
        }

    def load(self):
        defaults = self.default_config()
        try:
            self.settings_dir.mkdir(parents=True, exist_ok=True)
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                self.data = {**defaults, **loaded}
                self.migrate()
            else:
                self.data = defaults
                self.save()
        except Exception:
            self.data = defaults

    def migrate(self):
        changed = False
        if 'auto_save' in self.data:
            self.data['auto_save_enabled'] = bool(self.data.pop('auto_save'))
            changed = True
        if changed:
            self.save()

    def save(self):
        try:
            self.settings_dir.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def get_theme_name(self):
        return self.data.get('theme', 'brutal')

    def get_theme(self, theme_name=None):
        from spider_ide.ui.style_kit import get_theme_by_name
        name = theme_name or self.get_theme_name()
        return dict(get_theme_by_name(name))

    def add_recent_file(self, path):
        recent = self.data.get('recent_files', [])
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        self.data['recent_files'] = recent[:10]
        self.save()

    def add_recent_project(self, path):
        recent = self.data.get('recent_projects', [])
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        self.data['recent_projects'] = recent[:5]
        self.save()

    def get_recent_files(self):
        return [p for p in self.data.get('recent_files', []) if Path(p).exists()]

    def get_recent_projects(self):
        return [p for p in self.data.get('recent_projects', []) if Path(p).is_dir()]

    def clear_recent_files(self):
        self.data['recent_files'] = []
        self.save()

    def clear_recent_projects(self):
        self.data['recent_projects'] = []
        self.save() 