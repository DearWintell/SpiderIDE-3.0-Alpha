import time
import tkinter as tk

from .vars import SpiderVars
from .parser import SpiderParser
from .errors import SpiderError
from .widgets import WidgetMixin


class SpiderExecutor(WidgetMixin):
    def __init__(self):
        self.vars = SpiderVars()
        self.parser = SpiderParser()
        self.root = None
        self.canvas = None
        self.elements = {}
        self.textv_bindings = {}
        self.window_created = False

    def pv(self, raw):
        from .values import evaluate
        return evaluate(raw, self.vars)

    def unwrap(self, raw):
        from .values import unwrap_literal
        return unwrap_literal(raw)

    def _int(self, raw, default=0):
        try:
            return int(float(self.pv(raw)))
        except Exception:
            return default

    def execute_line(self, line, line_num):
        line = line.strip()
        if not line or self.parser.is_comment(line):
            return
        try:
            cmd = self.parser.extract_command(line)
            if not cmd:
                return
            params_str = self.parser.extract_params_string(line)
            params = self.parser.parse_params(params_str, cmd)
            self._dispatch(cmd, params, line_num)
        except Exception as e:
            print(f"\n[ERROR] Line {line_num}: {type(e).__name__}: {e}")

    def _dispatch(self, cmd, params, line_num):
        if cmd == 'var':        self.cmd_var(params, line_num)
        elif cmd == 'print':    self.cmd_print(params, line_num)
        elif cmd == 'title':    self.cmd_title(params, line_num)
        elif cmd == 'button':   self.cmd_button(params, line_num)
        elif cmd == 'wait':     self.cmd_wait(params, line_num)
        elif cmd == 'check':    self.cmd_check(params, line_num)
        elif cmd == 'bind':     self.cmd_bind(params, line_num)
        elif cmd == 'window':   self.cmd_window(params, line_num)
        elif cmd == 'text':     self.cmd_text(params, line_num)
        elif cmd == 'textv':    self.cmd_textv(params, line_num)
        elif cmd == 'shape':    self.cmd_shape(params, line_num)
        elif cmd == 'move':     self.cmd_move(params, line_num)
        elif cmd == 'clear':    self.cmd_clear(params, line_num)
        elif cmd == 'input':    self.cmd_input(params, line_num)
        elif cmd == 'checkbox': self.cmd_checkbox(params, line_num)
        elif cmd == 'slider':   self.cmd_slider(params, line_num)
        elif cmd == 'dropdown': self.cmd_dropdown(params, line_num)
        elif cmd == 'image':    self.cmd_image(params, line_num)
        elif cmd == 'on':       self.cmd_on(params, line_num)

    def cmd_window(self, params, line_num):
        if self.window_created:
            return
        title = self.pv(params.get('title', 'Spider Script'))
        width = self._int(params.get('width', 800), 800)
        height = self._int(params.get('height', 600), 600)
        bg = self.pv(params.get('bg', 'white'))
        self.root = tk.Tk()
        self.root.title(str(title))
        self.root.geometry(f"{width}x{height}")
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(self.root, width=width, height=height, bg=str(bg))
        self.canvas.place(x=0, y=0, width=width, height=height)
        self.window_created = True
        print(f"[SPIDER] Window created: {width}x{height}")

    def cmd_text(self, params, line_num):
        if not self.canvas:
            return
        text = self.pv(params.get('text', ''))
        x = self._int(params.get('x', 10), 10)
        y = self._int(params.get('y', 10), 10)
        color = self.pv(params.get('color', 'black'))
        size = self._int(params.get('size', 12), 12)
        self.canvas.create_text(x, y, text=str(text), fill=str(color),
                                font=('Arial', size), anchor='nw')

    def cmd_textv(self, params, line_num):
        if not self.canvas:
            return
        var_name = self.unwrap(params.get('var', ''))
        value = self.vars.get(var_name)
        if value is None:
            value = '0'
        x = self._int(params.get('x', 10), 10)
        y = self._int(params.get('y', 10), 10)
        color = self.pv(params.get('color', 'black'))
        size = self._int(params.get('size', 12), 12)
        text_id = self.canvas.create_text(x, y, text=str(value), fill=str(color),
                                          font=('Arial', size), anchor='nw')
        self.textv_bindings.setdefault(var_name, []).append({
            'id': text_id, 'x': x, 'y': y, 'color': color, 'size': size
        })

    def update_textv(self, var_name):
        if var_name not in self.textv_bindings:
            return
        value = self.vars.get(var_name)
        if value is None:
            value = '0'
        for item in self.textv_bindings[var_name]:
            self.canvas.delete(item['id'])
            item['id'] = self.canvas.create_text(
                item['x'], item['y'], text=str(value), fill=item['color'],
                font=('Arial', item['size']), anchor='nw')

    def cmd_shape(self, params, line_num):
        if not self.canvas:
            return
        shape_type = self.unwrap(params.get('type', 'square'))
        x = self._int(params.get('x', 100), 100)
        y = self._int(params.get('y', 100), 100)
        color = self.pv(params.get('color', 'red'))
        size = self._int(params.get('size', 50), 50)
        elem_id = self.unwrap(params.get('id', ''))
        if shape_type == 'circle':
            shape_id = self.canvas.create_oval(x, y, x + size, y + size, fill=str(color), outline='')
        else:
            shape_id = self.canvas.create_rectangle(x, y, x + size, y + size, fill=str(color), outline='')
        if elem_id:
            self.elements[elem_id] = {'id': shape_id, 'x': x, 'y': y, 'size': size}
            print(f"[SPIDER] Shape '{elem_id}' created at ({x}, {y}) [ID: {shape_id}]")

    def cmd_move(self, params, line_num):
        if not self.canvas:
            print("[SPIDER] ERROR: No canvas")
            return
        elem_id = self.unwrap(params.get('id', ''))
        if not elem_id or elem_id not in self.elements:
            print(f"[SPIDER] ERROR: Element '{elem_id}' not found")
            return
        element = self.elements[elem_id]
        shape_id = element['id']
        dx = dy = 0
        for key, value in params.items():
            if key == 'id':
                continue
            val = str(value)
            if key == 'x':
                if val.startswith('+'):
                    dx = int(val[1:]) if len(val) > 1 else 0
                elif val.startswith('-'):
                    dx = -int(val[1:]) if len(val) > 1 else 0
                else:
                    try:
                        dx = int(float(val)) - self.canvas.coords(shape_id)[0]
                    except Exception:
                        pass
            elif key == 'y':
                if val.startswith('+'):
                    dy = int(val[1:]) if len(val) > 1 else 0
                elif val.startswith('-'):
                    dy = -int(val[1:]) if len(val) > 1 else 0
                else:
                    try:
                        dy = int(float(val)) - self.canvas.coords(shape_id)[1]
                    except Exception:
                        pass
        if dx != 0 or dy != 0:
            self.canvas.move(shape_id, dx, dy)
            self.canvas.update()
            coords = self.canvas.coords(shape_id)
            element['x'], element['y'] = coords[0], coords[1]
            print(f"[SPIDER] Moved '{elem_id}' to ({coords[0]}, {coords[1]})")

    def cmd_clear(self, params, line_num):
        if self.canvas:
            self.canvas.delete('all')
            self.elements.clear()
            self.textv_bindings.clear()
            print("[SPIDER] Canvas cleared")

    def cmd_button(self, params, line_num):
        if not self.root:
            return
        text = self.pv(params.get('text', 'Button'))
        action = self.unwrap(params.get('action', ''))
        x = self._int(params.get('x', 10), 10)
        y = self._int(params.get('y', 10), 10)
        width = self._int(params.get('width', 100), 100)
        height = self._int(params.get('height', 30), 30)
        bg = self.pv(params.get('bg', '#238636'))
        fg = self.pv(params.get('color', 'white'))
        eid = self.unwrap(params.get('id', '')) or f"__btn_{line_num}"
        btn = tk.Button(self.root, text=str(text), bg=str(bg), fg=str(fg),
                        command=lambda a=action: self.execute_action(a, line_num))
        btn.place(x=x, y=y, width=width, height=height)
        self.elements[eid] = btn
        print(f"[SPIDER] Button '{text}' created")

    def cmd_var(self, params, line_num):
        if 'name' in params and 'value' in params:
            name = self.unwrap(params['name'])
            raw = params['value']
        elif len(params) == 1:
            name = next(iter(params))
            raw = params[name]
        else:
            SpiderError.show('MISSING_PARAM', line_num, 'var', 'var requires name=value')
            return
        if not name:
            SpiderError.show('MISSING_PARAM', line_num, 'var', 'var requires name')
            return
        value = self.pv(raw)
        self.vars.set(name, value)
        self.update_textv(name)
        print(f"[SPIDER] var '{name}' = {self.vars.get(name)}")

    def cmd_print(self, params, line_num):
        text = self.pv(params.get('text', ''))
        print(f"[SPIDER] {text}")

    def cmd_title(self, params, line_num):
        text = self.pv(params.get('text', ''))
        print(f"\n{'=' * 50}\n  {text}\n{'=' * 50}\n")

    def cmd_wait(self, params, line_num):
        try:
            seconds = float(self.pv(params.get('time', 1)))
            if self.root:
                self.root.after(int(seconds * 1000))
            else:
                time.sleep(seconds)
        except Exception:
            pass

    def cmd_check(self, params, line_num):
        cond = self.unwrap(params.get('what', ''))
        yes = self.unwrap(params.get('yes', ''))
        no = self.unwrap(params.get('no', ''))
        if self.check_condition(cond):
            if yes:
                self.execute_action(yes, line_num)
        else:
            if no:
                self.execute_action(no, line_num)

    def cmd_bind(self, params, line_num):
        key = self.unwrap(params.get('key', ''))
        action = self.unwrap(params.get('action', ''))
        if not (self.root and key):
            return
        aliases = {
            'enter': 'Return', 'return': 'Return',
            'esc': 'Escape', 'escape': 'Escape',
            'space': 'space', 'tab': 'Tab',
            'backspace': 'BackSpace', 'delete': 'Delete',
            'insert': 'Insert', 'home': 'Home', 'end': 'End',
            'pageup': 'Prior', 'pagedown': 'Next',
            'up': 'Up', 'down': 'Down', 'left': 'Left', 'right': 'Right',
        }
        k = aliases.get(key.lower(), key)

        def callback(event, act=action):
            self.execute_action(act, line_num)

        self.root.bind(f'<KeyPress-{k}>', callback)
        if len(k) == 1:
            self.root.bind(f'<KeyPress-{k.upper()}>', callback)
        print(f"[SPIDER] Bind '{key}' -> {action}")

    def execute_action(self, action_str, line_num):
        if not action_str:
            return
        action_str = action_str.strip()
        if self.parser.extract_command(action_str):
            self.execute_line(action_str, line_num)
            return
        for act_type, var1, var2 in self.parser.parse_action(action_str):
            if act_type == 'assign':
                val = self.pv(var2)
                self.vars.set(var1, val)
                self.update_textv(var1)
            elif act_type == 'add':
                v1 = self.vars.get(var1)
                if v1 is None:
                    v1 = 0
                self.vars.set(var1, v1 + self.pv(var2))
                self.update_textv(var1)
            elif act_type == 'sub':
                v1 = self.vars.get(var1)
                if v1 is None:
                    v1 = 0
                self.vars.set(var1, v1 - self.pv(var2))
                self.update_textv(var1)

    def parse_value(self, val_str):
        return self.pv(val_str)

    def check_condition(self, cond):
        from .values import evaluate_condition
        return evaluate_condition(cond, self.vars)

    def run_loop(self):
        if self.root:
            self.root.mainloop()