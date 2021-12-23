# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

himps = [
"mypy",
"mypy-boto3-acm",
"mypy-boto3-autoscaling",
"mypy-boto3-cloudformation",
"mypy-boto3-dynamodb",
"mypy-boto3-ec2",
"mypy-boto3-elbv2",
"mypy-boto3-lambda",
"mypy-boto3-logs",
"mypy-boto3-rds",
"mypy-boto3-route53",
"mypy-boto3-s3",
"mypy-boto3-sesv2",
"mypy-boto3-sqs",
"mypy-boto3-ssm",
"mypy-extensions",
]
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
