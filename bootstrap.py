"""Start readable source; install dependencies in a local venv when necessary."""
import os
import runpy
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def usable():
    try:
        import httpx
        from PySide6.QtWidgets import QApplication
        return hasattr(httpx, 'Client')
    except ImportError:
        return False


def main():
    os.chdir(ROOT)
    if usable():
        sys.argv = [str(ROOT/'app.py'),*sys.argv[1:]]
        runpy.run_path(str(ROOT/'app.py'),run_name='__main__')
        return
    venv = ROOT/'.venv'
    python = venv/'Scripts'/'python.exe' if os.name == 'nt' else venv/'bin'/'python'
    if not python.exists():
        print('Creating local Python environment...',flush=True)
        subprocess.run([sys.executable,'-m','venv',str(venv)],check=True)
    check = subprocess.run([str(python),'-c','import httpx; from PySide6.QtWidgets import QApplication'],capture_output=True)
    if check.returncode:
        print('Installing PySide6 Essentials and HTTPX in .venv (first run only)...',flush=True)
        subprocess.run([str(python),'-m','pip','install','-r',str(ROOT/'requirements.txt')],check=True)
    raise SystemExit(subprocess.call([str(python),str(ROOT/'app.py'),*sys.argv[1:]]))


if __name__ == '__main__':
    main()

