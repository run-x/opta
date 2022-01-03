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
# himps = [
# "modules.aws_k8s_service.aws_k8s_service",
# "modules.aws_k8s_base.aws_k8s_base",
# "modules.datadog.datadog",
# "modules.gcp_k8s_base.gcp_k8s_base",
# "modules.gcp_k8s_service.gcp_k8s_service",
# "modules.gcp_gke.gcp_gke",
# "modules.aws_dns.aws_dns",
# "modules.aws_documentdb.aws_documentdb",
# "modules.runx.runx",
# "modules.helm_chart.helm_chart",
# "modules.aws_iam_role.aws_iam_role",
# "modules.aws_iam_user.aws_iam_user",
# "modules.aws_eks.aws_eks",
# "modules.aws_ses.aws_ses",
# "modules.aws_sqs.aws_sqs",
# "modules.aws_sns.aws_sns",
# "modules.azure_base.azure_base",
# "modules.azure_k8s_base.azure_k8s_base",
# "modules.azure_k8s_service.azure_k8s_service",
# "modules.local_k8s_service.local_k8s_service",
# "modules.external_ssl_cert.external_ssl_cert",
# "modules.aws_s3.aws_s3",
# "modules.gcp_dns.gcp_dns",
# "modules.gcp_service_account.gcp_service_account",
# "modules.custom_terraform.custom_terraform",
# "modules.aws_dynamodb.aws_dynamodb",
# "modules.mongodb_atlas.mongodb_atlas",
# "modules.cloudfront_distribution.cloudfront_distribution",
# "modules.lambda_function.lambda_function"
# ]
print(himps)

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
