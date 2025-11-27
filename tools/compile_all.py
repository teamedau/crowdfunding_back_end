import py_compile
from pathlib import Path
import sys

errors = 0
for p in Path('.').rglob('*.py'):
    if 'venv' in p.parts or '.venv' in p.parts or 'site-packages' in p.parts:
        continue
    try:
        py_compile.compile(str(p), doraise=True)
    except Exception as e:
        print(f"{p}: {e}")
        errors += 1
sys.exit(errors)
