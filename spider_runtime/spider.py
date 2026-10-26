import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from spider_runtime.executor import SpiderExecutor
from spider_runtime.errors import SpiderError

def run_spider(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        SpiderError.show('NO_START', 1)

    first = lines[0].strip()
    if first != 'Spider(Start)':
        SpiderError.show('NO_START', 1, first)

    print(f"\nSPIDER SCRIPT")
    print(f"File: {file_path}")
    print("=" * 50 + "\n")

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