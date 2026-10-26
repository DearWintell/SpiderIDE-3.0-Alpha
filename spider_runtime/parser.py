import re


class SpiderParser:
    @staticmethod
    def _top_mask(s):
        n = len(s)
        mask = [False] * n
        depth = 0
        in_str = False
        quote = ''
        i = 0
        while i < n:
            ch = s[i]
            if in_str:
                if ch == '\\' and i + 1 < n:
                    i += 2
                    continue
                if ch == quote:
                    in_str = False
                i += 1
                continue
            if ch in ('"', "'"):
                in_str = True
                quote = ch
                i += 1
                continue
            if ch in '([{':
                depth += 1
                i += 1
                continue
            if ch in ')]}':
                depth -= 1
                i += 1
                continue
            if depth == 0:
                mask[i] = True
            i += 1
        return mask

    @staticmethod
    def _first_top(s, mask, ch):
        for i in range(len(s)):
            if mask[i] and s[i] == ch:
                return i
        return -1

    @staticmethod
    def _split_top(s, sep=';'):
        mask = SpiderParser._top_mask(s)
        parts, buf = [], []
        for i, c in enumerate(s):
            if mask[i] and c == sep:
                parts.append(''.join(buf)); buf = []
            else:
                buf.append(c)
        parts.append(''.join(buf))
        return [p.strip() for p in parts if p.strip()]

    @staticmethod
    def parse_params(param_str, cmd=None):
        params = {}
        if not param_str:
            return params
        s = param_str.strip()
        if not s:
            return params

        mask = SpiderParser._top_mask(s)
        n = len(s)

        key_pos = []
        i = 0
        while i < n:
            if mask[i] and s[i] == '=':
                k = i - 1
                while k >= 0 and s[k] in ' \t':
                    k -= 1
                if k >= 0 and (s[k].isalnum() or s[k] == '_'):
                    start = k
                    while start >= 0 and (s[start].isalnum() or s[start] == '_'):
                        start -= 1
                    ident_start = start + 1
                    ident = s[ident_start:k + 1]
                    before_ok = (ident_start == 0) or (s[ident_start - 1] in ' ,\t')
                    after_eq = (i + 1 < n and s[i + 1] == '=')
                    if before_ok and not after_eq:
                        key_pos.append((i, ident, ident_start))
            i += 1

        if not key_pos:
            bare = s.rstrip(', \t')
            auto_key = {'print': 'text', 'title': 'text',
                        'textv': 'var', 'Spider': 'phase'}.get(cmd, 'value')
            params[auto_key] = bare
            return params

        for idx, (eq, ident, _istart) in enumerate(key_pos):
            val_start = eq + 1
            val_end = key_pos[idx + 1][2] if idx + 1 < len(key_pos) else n
            raw = s[val_start:val_end].strip().rstrip(', \t')
            params[ident] = raw
        return params

    @staticmethod
    def parse_action(action_str):
        actions = []
        if not action_str:
            return actions
        for act in SpiderParser._split_top(action_str, ';'):
            mask = SpiderParser._top_mask(act)
            eq = SpiderParser._first_top(act, mask, '=')
            if eq != -1:
                actions.append(('assign', act[:eq].strip(), act[eq + 1:].strip()))
                continue
            plus = SpiderParser._first_top(act, mask, '+')
            minus = SpiderParser._first_top(act, mask, '-')
            if plus != -1 and (minus == -1 or plus < minus):
                actions.append(('add', act[:plus].strip(), act[plus + 1:].strip()))
            elif minus != -1:
                actions.append(('sub', act[:minus].strip(), act[minus + 1:].strip()))
        return actions

    @staticmethod
    def is_comment(line):
        line = line.strip()
        return line.startswith('/') or line.startswith('#')

    @staticmethod
    def extract_command(line):
        line = line.strip()
        if '(' in line:
            return line[:line.index('(')].strip()
        return None

    @staticmethod
    def extract_params_string(line):
        line = line.strip()
        start = line.find('(')
        end = line.rfind(')')
        if start != -1 and end != -1 and end > start:
            return line[start + 1:end]
        return ''