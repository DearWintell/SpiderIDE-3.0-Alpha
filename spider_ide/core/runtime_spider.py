import sys
import os
import re


if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

NO_GUI = os.environ.get('SPIDER_NO_GUI', '0') == '1'


class SpiderError:
    CODES = {
        'NO_START': 'Script must start with Spider(Start)',
        'UNKNOWN_CMD': 'Unknown command',
        'MISSING_PARAM': 'Missing required parameter',
    }

    @staticmethod
    def show(code, line_num, command='', extra=''):
        message = SpiderError.CODES.get(code, 'Unknown error')
        print(f"\n[ERROR] Line {line_num}: {message}")
        if command:
            print(f"   Command: {command}")
        sys.exit(1)


class SpiderVars:
    def __init__(self):
        self.vars = {}
    
    def set(self, name, value):
        try:
            if '.' in str(value):
                value = float(value)
            else:
                value = int(value)
        except:
            value = str(value).strip("'\"")
        self.vars[name] = value
    
    def get(self, name):
        return self.vars.get(name, None)


class SpiderExecutor:
    def __init__(self):
        self.vars = SpiderVars()
        self.root = None
        self.canvas = None
        self.elements = {}
        
    def execute_line(self, line, line_num):
        line = line.strip()
        if not line or line.startswith('/') or line.startswith('#'):
            return
            
        if '(' not in line:
            return
            
        cmd = line[:line.index('(')]
        params_str = line[line.index('(')+1:line.rindex(')')]
        
        if cmd == 'var':
            self.cmd_var(params_str, line_num)
        elif cmd == 'print':
            self.cmd_print(params_str, line_num)
        elif cmd == 'window':
            self.cmd_window(params_str, line_num)
        elif cmd == 'title':
            self.cmd_title(params_str, line_num)
        elif cmd == 'text':
            self.cmd_text(params_str, line_num)
        elif cmd == 'button':
            self.cmd_button(params_str, line_num)
        elif cmd == 'Spider':
            pass  # Игнорируем Spider(Start)
        else:
            print(f"[WARNING] Line {line_num}: Unknown command '{cmd}'")
            
    def parse_params(self, s):
        params = {}
        
        s = s.strip()
        if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
            return {'text': s[1:-1]}
        
        # Парсим key=value пары
        for m in re.finditer(r"(\w+)=('[^']*'|\"[^\"]*\"|\S+)", s):
            key = m.group(1)
            val = m.group(2)
            if (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
                val = val[1:-1]
            else:
                try:
                    val = int(val) if '.' not in val else float(val)
                except:
                    pass
            params[key] = val
        
        return params
        
    def cmd_var(self, params_str, line_num):
        p = self.parse_params(params_str)
        name = p.get('name', '')
        value = p.get('value', '')
        if name:
            self.vars.set(name, value)
            print(f"[SPIDER] var '{name}' = {self.vars.get(name)}")
        else:
            print(f"[ERROR] Line {line_num}: var requires 'name' parameter")
            
    def cmd_print(self, params_str, line_num):
        p = self.parse_params(params_str)
        text = p.get('text', '')
        print(text, flush=True)  
        
    def cmd_window(self, params_str, line_num):
        if NO_GUI:
            print(f"[SPIDER] Window creation skipped (NO_GUI mode)")
            return
            
        import tkinter as tk
        p = self.parse_params(params_str)
        title = p.get('title', 'Spider Script')
        width = p.get('width', 800)
        height = p.get('height', 600)
        bg = p.get('bg', '#0d1117')
        
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")
        self.canvas = tk.Canvas(self.root, width=width, height=height, bg=bg)
        self.canvas.pack()
        print(f"[SPIDER] Window created: {width}x{height}")
        
    def cmd_title(self, params_str, line_num):
        p = self.parse_params(params_str)
        text = p.get('text', '')
        print(f"\n{'='*50}\n  {text}\n{'='*50}\n")
        
    def cmd_text(self, params_str, line_num):
        if NO_GUI or not self.canvas:
            if not NO_GUI:
                print(f"[WARNING] Line {line_num}: text requires window")
            return
        p = self.parse_params(params_str)
        text = p.get('text', '')
        x = p.get('x', 10)
        y = p.get('y', 10)
        color = p.get('color', 'white')
        size = p.get('size', 12)
        self.canvas.create_text(x, y, text=text, fill=color, font=('Arial', size), anchor='nw')
        
    def cmd_button(self, params_str, line_num):
        if NO_GUI or not self.root:
            if not NO_GUI:
                print(f"[WARNING] Line {line_num}: button requires window")
            return
        import tkinter as tk
        p = self.parse_params(params_str)
        text = p.get('text', 'Button')
        x = p.get('x', 10)
        y = p.get('y', 10)
        width = p.get('width', 100)
        height = p.get('height', 30)
        bg = p.get('bg', '#238636')
        fg = p.get('color', 'white')
        action = p.get('action', '')
        
        btn = tk.Button(self.root, text=text, bg=bg, fg=fg,
                       command=lambda: print(f"[SPIDER] Action: {action}"))
        btn.place(x=x, y=y, width=width, height=height)
        print(f"[SPIDER] Button '{text}' created")
        
    def run_loop(self):
        if self.root and not NO_GUI:
            self.root.mainloop()


def run_spider(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines or lines[0].strip() != 'Spider(Start)':
        SpiderError.show('NO_START', 1)

    print(f"\n[SPIDER SCRIPT]")
    print(f"File: {file_path}")
    print("=" * 50 + "\n", flush=True)

    executor = SpiderExecutor()

    for i, line in enumerate(lines[1:], start=2):
        try:
            executor.execute_line(line, i)
        except Exception as e:
            print(f"\n[ERROR] Line {i}: {e}")
            break

    executor.run_loop()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python spider.py <file.spider>")
    else:
        run_spider(sys.argv[1]) 