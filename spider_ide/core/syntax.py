from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression


class SpiderSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        
        self.formats = {}
        self.errors = []
        self.warnings = []
        
        self._init_formats({
            'keyword': '#7dd3fc',
            'command': '#4ade80',
            'string': '#fbbf24',
            'number': '#c084fc',
            'comment': '#52525b',
            'param': '#e0e0e0',
            'special': '#f472b6',
            'function': '#7dd3fc',
            'operator': '#94a3b8',
            'error': '#ef4444',
            'warning': '#f59e0b',
        })
        
        self.rules = [
            (QRegularExpression(r'#.*$'), 'comment'),
            (QRegularExpression(r'//.*$'), 'comment'),
            (QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), 'string'),
            (QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), 'string'),
            (QRegularExpression(r'\b\d+\.?\d*\b'), 'number'),
            (QRegularExpression(r'\bSpider\s*\(\s*Start\s*\)'), 'special'),
            (QRegularExpression(r'\bSpider\s*\(\s*End\s*\)'), 'special'),
            (QRegularExpression(
                r'\b(print|var|window|text|button|title|shape|move|bind|check|clear|wait|action|loop|func|return|param|if|else|elif)\s*\('
            ), 'command'),
            (QRegularExpression(r'\b([a-zA-Z_]\w*)\s*='), 'param'),
            (QRegularExpression(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*(?=\()'), 'function'),
        ]
        
        self.keywords = [
            'Spider', 'Start', 'End',
            'if', 'else', 'elif',
            'loop', 'while', 'for',
            'func', 'return', 'param', 'action',
            'var', 'print', 'check', 'clear', 'wait',
            'window', 'text', 'button', 'shape', 'move', 'bind',
            'title', 'color', 'size', 'x', 'y', 'width', 'height', 'bg', 'fg',
            'true', 'false', 'None', 'break', 'continue',
            'import', 'export',
        ]
    
    def _init_formats(self, colors):
        keyword_fmt = QTextCharFormat()
        keyword_fmt.setForeground(QColor(colors.get('keyword', '#7dd3fc')))
        keyword_fmt.setFontWeight(QFont.Weight.Bold)
        self.formats['keyword'] = keyword_fmt
        
        command_fmt = QTextCharFormat()
        command_fmt.setForeground(QColor(colors.get('command', '#4ade80')))
        command_fmt.setFontWeight(QFont.Weight.Bold)
        self.formats['command'] = command_fmt
        
        string_fmt = QTextCharFormat()
        string_fmt.setForeground(QColor(colors.get('string', '#fbbf24')))
        self.formats['string'] = string_fmt
        
        number_fmt = QTextCharFormat()
        number_fmt.setForeground(QColor(colors.get('number', '#c084fc')))
        self.formats['number'] = number_fmt
        
        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor(colors.get('comment', '#52525b')))
        comment_fmt.setFontItalic(True)
        self.formats['comment'] = comment_fmt
        
        param_fmt = QTextCharFormat()
        param_fmt.setForeground(QColor(colors.get('param', '#e0e0e0')))
        self.formats['param'] = param_fmt
        
        special_fmt = QTextCharFormat()
        special_fmt.setForeground(QColor(colors.get('special', '#f472b6')))
        special_fmt.setFontWeight(QFont.Weight.Bold)
        self.formats['special'] = special_fmt
        
        function_fmt = QTextCharFormat()
        function_fmt.setForeground(QColor(colors.get('function', '#7dd3fc')))
        self.formats['function'] = function_fmt
        
        operator_fmt = QTextCharFormat()
        operator_fmt.setForeground(QColor(colors.get('operator', '#94a3b8')))
        self.formats['operator'] = operator_fmt
        
        self.error_format = QTextCharFormat()
        self.error_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
        self.error_format.setUnderlineColor(QColor(colors.get('error', '#ef4444')))
        self.error_format.setToolTip("Syntax Error")
        
        self.warning_format = QTextCharFormat()
        self.warning_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
        self.warning_format.setUnderlineColor(QColor(colors.get('warning', '#f59e0b')))
        self.warning_format.setToolTip("Warning")
    
    def apply_theme(self, theme):
        self._init_formats({
            'keyword': theme.get('keyword', '#7dd3fc'),
            'command': theme.get('command', '#4ade80'),
            'string': theme.get('string', '#fbbf24'),
            'number': theme.get('number', '#c084fc'),
            'comment': theme.get('comment', '#52525b'),
            'param': theme.get('param', '#e0e0e0'),
            'special': theme.get('special', '#f472b6'),
            'function': theme.get('function', '#7dd3fc'),
            'operator': theme.get('operator', '#94a3b8'),
            'error': theme.get('error', '#ef4444'),
            'warning': theme.get('warning', '#f59e0b'),
        })
        self.rehighlight()
    
    def set_errors(self, errors):
        self.errors = errors
        self.rehighlight()
    
    def set_warnings(self, warnings):
        self.warnings = warnings
        self.rehighlight()
    
    def highlightBlock(self, text):
        current_block_number = self.currentBlock().blockNumber() + 1
        
        for pattern, format_key in self.rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, self.formats[format_key])
        
        for keyword in self.keywords:
            pattern = QRegularExpression(r'\b' + keyword + r'\b')
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                start = match.capturedStart()
                length = match.capturedLength()
                
                current_fmt = self.format(start)
                if current_fmt.foreground() == self.formats['command'].foreground():
                    continue
                
                self.setFormat(start, length, self.formats['keyword'])
        
        for line_num, message in self.errors:
            if line_num == current_block_number:
                self.setFormat(0, len(text), self.error_format)
                fmt = self.format(0)
                fmt.setToolTip(f"Error: {message}")
                self.setFormat(0, len(text), fmt)
                break
        
        for line_num, message in self.warnings:
            if line_num == current_block_number:
                self.setFormat(0, len(text), self.warning_format)
                fmt = self.format(0)
                fmt.setToolTip(f"Warning: {message}")
                self.setFormat(0, len(text), fmt)
                break 