# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
import pymunk

a = Analysis(['main.py'],
             pathex=['C:\\Users\\Mark\\Documents\\Python Scripts\\gamejam_2020_moonshot'],
             binaries=[ (pymunk.chipmunk_path, '.')],
             datas=[('sounds/*.wav','sounds'),('images/*.png','images')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='main',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
