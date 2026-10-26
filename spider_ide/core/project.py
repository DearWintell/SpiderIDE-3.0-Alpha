import os
import json
from pathlib import Path

class ProjectManager:
    def __init__(self):
        self.current_project = None
        self.project_config = None
        
    def create_project(self, name, location):
        project_path = Path(location) / name
        project_path.mkdir(parents=True, exist_ok=True)
        

        (project_path / 'src').mkdir(exist_ok=True)
        (project_path / 'assets').mkdir(exist_ok=True)
        (project_path / 'build').mkdir(exist_ok=True)
        

        config = {
            'name': name,
            'version': '1.0',
            'main': 'src/main.spider',
            'author': '',
            'description': ''
        }
        
        with open(project_path / 'project.json', 'w') as f:
            json.dump(config, f, indent=2)
            

        main_file = project_path / 'src' / 'main.spider'
        with open(main_file, 'w') as f:
            f.write('Spider(Start)\n\n')
            f.write('window("title=\'My Project\' width=800 height=600 bg=\'#0d1117\'")\n\n')
            f.write('text("text=\'Hello Spider!\' x=400 y=300 color=\'#58a6ff\' size=24")\n')
            
        self.current_project = str(project_path)
        return str(project_path)
        
    def open_project(self, project_path):
        config_file = Path(project_path) / 'project.json'
        if config_file.exists():
            with open(config_file, 'r') as f:
                self.project_config = json.load(f)
            self.current_project = project_path
            return True
        return False
        
    def get_project_files(self):
        if not self.current_project:
            return []
            
        files = []
        for ext in ['*.spider']:
            files.extend(Path(self.current_project).rglob(ext))
        return [str(f) for f in files]
        
    def get_main_file(self):
        if self.project_config:
            main = self.project_config.get('main', 'src/main.spider')
            return str(Path(self.current_project) / main)
        return None