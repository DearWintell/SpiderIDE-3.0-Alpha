import re

_NUM_RE = re.compile(r'^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$')

_SAFE_BUILTINS = {
    'len': len, 'abs': abs, 'round': round, 'min': min, 'max': max,
    'sum': sum, 'str': str, 'int': int, 'float': float, 'bool': bool,
    'list': list, 'tuple': tuple, 'set': set, 'sorted': sorted,
    'reversed': reversed, 'enumerate': enumerate, 'range': range,
    'upper': lambda s: str(s).upper(),
    'lower': lambda s: str(s).lower(),
    'strip': lambda s: str(s).strip(),
    'replace': lambda s, a, b: str(s).replace(a, b),
    'split': lambda s, sep=None: str(s).split(sep),
    'join': lambda sep, seq: str(sep).join(str(x) for x in seq),
    'find': lambda s, sub: str(s).find(sub),
    'count': lambda s, sub: str(s).count(sub),
}

_BOOL_LITERALS = {
    'true': True, 'yes': True, 'false': False, 'no': False,
    'none': None, 'nil': None, 'null': None,
}


def _unquote(s):
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        inner = s[1:-1]
        out, i = [], 0
        while i < len(inner):
            c = inner[i]
            if c == '\\' and i + 1 < len(inner):
                nxt = inner[i + 1]
                out.append({'n': '\n', 't': '\t', '\\': '\\', '"': '"', "'": "'"}.get(nxt, nxt))
                i += 2
                continue
            out.append(c)
            i += 1
        return ''.join(out)
    return s


def _is_single_string_literal(s):
    if len(s) < 2 or s[0] not in ('"', "'"):
        return False
    if s[-1] != s[0]:
        return False
    quote = s[0]
    i = 1
    while i < len(s):
        ch = s[i]
        if ch == '\\' and i + 1 < len(s):
            i += 2
            continue
        if ch == quote:
            return i == len(s) - 1
        i += 1
    return False


def _is_number(s):
    return bool(_NUM_RE.match(s))


def _to_number(s):
    s = s.strip()
    low = s.lower()
    if '.' in s or 'e' in low:
        return float(s)
    return int(s)


def _split_top_level(s, sep=','):
    parts, buf, depth = [], [], 0
    in_str = False
    quote = ''
    i = 0
    while i < len(s):
        ch = s[i]
        if in_str:
            buf.append(ch)
            if ch == '\\' and i + 1 < len(s):
                buf.append(s[i + 1]); i += 2; continue
            if ch == quote:
                in_str = False
        else:
            if ch in ('"', "'"):
                in_str = True; quote = ch; buf.append(ch)
            elif ch in '([{':
                depth += 1; buf.append(ch)
            elif ch in ')]}':
                depth -= 1; buf.append(ch)
            elif ch == sep and depth == 0:
                parts.append(''.join(buf)); buf = []
            else:
                buf.append(ch)
        i += 1
    if buf:
        parts.append(''.join(buf))
    return [p.strip() for p in parts]


def _parse_list_literal(s, vars_obj):
    inner = s[1:-1].strip()
    if not inner:
        return []
    return [evaluate(p, vars_obj) for p in _split_top_level(inner, ',')]


def _build_namespace(vars_obj):
    ns = dict(_BOOL_LITERALS)
    if vars_obj is not None:
        try:
            ns.update(dict(vars_obj.vars))
        except Exception:
            pass
    return ns


def unwrap_literal(s):
    if s is None:
        return ''
    s = str(s).strip()
    if _is_single_string_literal(s):
        return _unquote(s)
    return s


def evaluate(expr, vars_obj=None):
    if expr is None:
        return None
    if isinstance(expr, (bool, int, float, list, dict, tuple, set)):
        return expr
    s = str(expr).strip()
    if s == '':
        return ''

    low = s.lower()
    if low in _BOOL_LITERALS:
        return _BOOL_LITERALS[low]

    if _is_single_string_literal(s):
        return _unquote(s)

    if _is_number(s):
        return _to_number(s)

    if s[0] == '[' and s[-1] == ']':
        return _parse_list_literal(s, vars_obj)

    if '__' in s:
        return s

    ns = _build_namespace(vars_obj)
    globals_box = {'__builtins__': _SAFE_BUILTINS}
    try:
        return eval(s, globals_box, ns)
    except NameError:
        return s
    except Exception:
        return s


def evaluate_condition(cond, vars_obj=None):
    return bool(evaluate(cond, vars_obj))