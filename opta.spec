# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files
import os
def generate_module_import_array():
  himps = []
  for root, dirs, files in os.walk("./modules"):
    for filename in files:
      if filename.endswith(".py") and not filename.startswith("test"):
        modname = filename.split(".py")[0]
        himps.append(".".join(["modules", modname, modname]))
  return sorted(himps)



block_cipher = None

himps = generate_module_import_array()

a = Analysis(['opta/cli.py'],
             pathex=[],
             binaries=[],
             datas=[
               ('./config', 'config'),
               ('./modules', 'modules'),
               ('roots.pem', 'grpc/_cython/_credentials/'),
             ] + collect_data_files('hcl2'),
             hiddenimports=himps,
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
          [],
          exclude_binaries=True,
          name='opta',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='opta')
