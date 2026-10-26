class SpiderVars:
    def __init__(self):
        self.vars = {}
        self.vars['true'] = True
        self.vars['false'] = False
        self.vars['yes'] = True
        self.vars['no'] = False

    def set(self, name, value):
        if isinstance(value, (bool, int, float, list, dict, tuple, set)) or value is None:
            self.vars[name] = value
            return
        s = str(value)
        low = s.strip().lower()
        if low in ('true', 'yes'):
            self.vars[name] = True; return
        if low in ('false', 'no'):
            self.vars[name] = False; return
        if low in ('none', 'nil', 'null'):
            self.vars[name] = None; return
        try:
            if '.' in s or 'e' in low:
                self.vars[name] = float(s)
            else:
                self.vars[name] = int(s)
        except Exception:
            self.vars[name] = s.strip("'\"")

    def get(self, name):
        return self.vars.get(name)

    def exists(self, name):
        return name in self.vars