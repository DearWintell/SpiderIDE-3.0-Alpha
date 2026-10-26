import os
import tkinter as tk
from tkinter import ttk

from .errors import SpiderError

_EVENT_MAP = {
    'click': '<Button-1>',
    'dblclick': '<Double-Button-1>',
    'rightclick': '<Button-3>',
    'keypress': '<Key>',
    'keydown': '<KeyPress>',
    'keyup': '<KeyRelease>',
    'hover': '<Enter>',
    'enter': '<Enter>',
    'leave': '<Leave>',
    'motion': '<Motion>',
    'focus_in': '<FocusIn>',
    'focus_out': '<FocusOut>',
    'submit': '<Return>',
}


def _num(v, default=0):
    try:
        return int(float(v))
    except Exception:
        return default


def _txt(v, default=''):
    if v is None:
        return default
    return str(v).strip("'\"")


def _flag(v):
    if v is None:
        return False
    return str(v).strip().lower().strip("'\"") in ('1', 'true', 'yes', 'on')


class WidgetMixin:
    def _parent(self):
        return self.root

    def _ensure_window(self, line_num):
        if not self.window_created:
            SpiderError.show('NO_START', line_num, 'widget')
            return False
        return True

    def _place(self, widget, params):
        widget.place(x=_num(params.get('x'), 0), y=_num(params.get('y'), 0))

    def _register(self, eid, widget):
        if eid:
            self.elements[eid] = widget

    def cmd_input(self, params, line_num):
        if not self._ensure_window(line_num):
            return
        w = tk.Entry(self._parent(), width=_num(params.get('width'), 20))
        ph = _txt(params.get('placeholder'))
        if ph:
            w.insert(0, ph)
            w.bind('<FocusIn>', lambda e: w.delete(0, 'end') if w.get() == ph else None)
            w.bind('<FocusOut>', lambda e: w.insert(0, ph) if not w.get() else None)
        self._place(w, params)
        self._register(_txt(params.get('id')), w)

    def cmd_checkbox(self, params, line_num):
        if not self._ensure_window(line_num):
            return
        var = tk.BooleanVar(value=_flag(params.get('value')))
        w = tk.Checkbutton(self._parent(), text=_txt(params.get('text')), variable=var)
        eid = _txt(params.get('id'))
        if eid:
            self.vars.set(eid, var.get())
            var.trace_add('write', lambda *a, e=eid: self.vars.set(e, var.get()))
        self._place(w, params)
        self._register(eid, w)

    def cmd_slider(self, params, line_num):
        if not self._ensure_window(line_num):
            return
        orient = 'vertical' if _txt(params.get('orient'), 'horizontal').lower().startswith('v') else 'horizontal'
        w = tk.Scale(self._parent(), from_=_num(params.get('from'), 0),
                     to=_num(params.get('to'), 100), orient=orient,
                     resolution=_num(params.get('step'), 1), showvalue=1)
        w.set(_num(params.get('value'), 0))
        eid = _txt(params.get('id'))
        if eid:
            self.vars.set(eid, w.get())
            w.configure(command=lambda v, e=eid: self.vars.set(e, int(float(v))))
        self._place(w, params)
        self._register(eid, w)

    def cmd_dropdown(self, params, line_num):
        if not self._ensure_window(line_num):
            return
        opts = [o.strip() for o in _txt(params.get('options')).split(',') if o.strip()]
        cur = tk.StringVar(value=_txt(params.get('value'), opts[0] if opts else ''))
        w = ttk.Combobox(self._parent(), textvariable=cur, values=opts,
                         width=_num(params.get('width'), 12), state='readonly')
        if opts:
            cur.set(_txt(params.get('value'), opts[0]))
        eid = _txt(params.get('id'))
        if eid:
            self.vars.set(eid, cur.get())
            cur.trace_add('write', lambda *a, e=eid: self.vars.set(e, cur.get()))
        self._place(w, params)
        self._register(eid, w)

    def cmd_image(self, params, line_num):
        if not self._ensure_window(line_num):
            return
        path = _txt(params.get('file') or params.get('src'))
        if not path or not os.path.exists(path):
            SpiderError.show('MISSING_PARAM', line_num, 'image', 'file not found: %s' % path)
            return
        try:
            img = tk.PhotoImage(file=path)
        except Exception as ex:
            SpiderError.show('WRONG_VALUE', line_num, 'image', str(ex))
            return
        w = tk.Label(self._parent(), image=img)
        w._img = img
        self._place(w, params)
        self._register(_txt(params.get('id')), w)

    def cmd_on(self, params, line_num):
        eid = _txt(params.get('id'))
        event = _txt(params.get('event')).lower()
        action = _txt(params.get('action'))
        widget = self.elements.get(eid)
        if widget is None:
            SpiderError.show('VAR_NOT_FOUND', line_num, 'on', 'unknown id: %s' % eid)
            return
        self._bind_one(widget, event, action, line_num)

    def _bind_one(self, widget, event, action, line_num):
        cb = lambda *a, act=action, ln=line_num: self.execute_line(act, ln)
        if event == 'change':
            if isinstance(widget, (tk.Scale, tk.Checkbutton)):
                try:
                    widget.configure(command=cb)
                    return
                except Exception:
                    pass
            widget.bind('<KeyRelease>', cb)
            widget.bind('<ButtonRelease-1>', cb)
            return
        tk_event = _EVENT_MAP.get(event)
        if tk_event is None:
            SpiderError.show('UNKNOWN_CMD', line_num, 'on', 'event: %s' % event)
            return
        widget.bind(tk_event, cb)
        if event == 'hover':
            widget.bind('<Leave>', cb)