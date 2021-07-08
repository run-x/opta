# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None


a = Analysis(['opta/cli.py'],
             pathex=[],
             binaries=[],
             datas=[
               ('./config', 'config'),
               ('roots.pem', 'grpc/_cython/_credentials/'),
               ('opta/commands/init_templates/environment/aws/opta.yml', 'opta/commands/init_templates/environment/aws'),
               ('opta/commands/init_templates/environment/gcp/opta.yml', 'opta/commands/init_templates/environment/gcp'),
               ('opta/commands/init_templates/environment/azure/opta.yml', 'opta/commands/init_templates/environment/azure'),
             ] + collect_data_files('hcl2'),
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
