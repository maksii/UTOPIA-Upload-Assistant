# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

a = Analysis(
    ['upload.py'],
    pathex=[],
    binaries=[],
    datas=collect_data_files('babelfish', include_py_files=False, subdir='data') + \
        collect_data_files('guessit', include_py_files=False, subdir='config') + \
        collect_data_files('guessit', include_py_files=False, subdir='data'),
    hiddenimports=[
        'babelfish',
        'babelfish.converters',
        'babelfish.converters.name',
        'babelfish.converters.alpha2',
        'babelfish.converters.alpha3b',
        'babelfish.converters.alpha3t',
        'babelfish.converters.opensubtitles',
        'babelfish.converters.thetvdb',
        'babelfish.country',
        'babelfish.exceptions',
        'babelfish.language',
        'babelfish.script',
        'babelfish.utils',
        'babelfish.converters.countryname',
        'guessit.data',
        'multiprocessing'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='upload',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)