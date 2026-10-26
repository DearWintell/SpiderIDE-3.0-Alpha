class SpiderError:
    CODES = {
        'NO_START': 'Script must start with Spider(Start)',
        'UNKNOWN_CMD': 'Unknown command',
        'MISSING_PARAM': 'Missing required parameter',
        'WRONG_VALUE': 'Wrong value type',
        'VAR_NOT_FOUND': 'Variable not found',
        'SYNTAX_ERROR': 'Syntax error',
        'DIV_BY_ZERO': 'Division by zero',
    }

    @staticmethod
    def show(code, line_num, command='', extra=''):
        message = SpiderError.CODES.get(code, 'Unknown error')
        print(f"\n[ERROR] Line {line_num}")
        if command:
            print(f"   Command: {command}")
        print(f"   Reason: {message}")
        if extra:
            print(f"   {extra}")
        exit(1)