# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

root = Path(SPECPATH)
a = Analysis(
    [str(root / 'app.py')], pathex=[str(root)], binaries=[], datas=[(str(root / 'assets'), 'assets')],
    hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['numpy', 'PIL', 'pygments', 'pytest'], noarchive=False, optimize=0,
)
# Qt 6.11 uses the unversioned Windows ICU API. An unrelated ICU DLL found
# in the build runtime may export only version-suffixed names and break Qt.
# Use the OS-provided ICU on supported Windows versions, as unfrozen Qt does.
a.binaries = [entry for entry in a.binaries
              if Path(entry[0]).name.lower() not in ('icuuc.dll', 'icudt78.dll')]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='OsuBatch',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='OsuBatch')

