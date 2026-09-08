"""Build a Windows onedir distribution with replaceable Qt libraries."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
if __name__ == "__main__":
    subprocess.run([
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
        "--distpath", str(ROOT / "dist"), "--workpath", str(ROOT / "build"),
        str(ROOT / "OsuBatch.spec"),
    ], check=True, cwd=ROOT)

