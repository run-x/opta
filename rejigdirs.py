# type: ignore
import os
import shutil

allFilePaths = set([])


def make_valid_files_list(
    ignoreDirs=[".git", "dist", "tests", "__pycache__", ".mypy_cache"]
):
    for root, dirs, files in os.walk(".", topdown=False):
        for name in files:
            addToList = True
            filePath = os.path.join(root, name)
            for ignoreDir in ignoreDirs:
                if ignoreDir + "/" in filePath:
                    addToList = False
                    break
            if addToList:
                allFilePaths.add(filePath)


def get_all_module_names():
    modset = set([])
    for root, dirs, files in os.walk("./config/registry"):
        for name in files:
            if name.endswith("yaml"):
                modset.add(name.split(".yaml")[0])
    return modset


def get_underscore_module_name(module_name):
    rtn_val = module_name
    if "-" in module_name:
        rtn_val = "_".join(module_name.split("-"))
    return rtn_val


def get_all_module_files(module_name):
    moduleFiles = []
    _module_name = module_name
    if "-" in module_name:
        _module_name = get_underscore_module_name(module_name)
    for aFilePath in allFilePaths:
        if module_name in aFilePath or _module_name in aFilePath:
            moduleFiles.append(aFilePath)
    return moduleFiles


def copy_over_files(aModule):
    module_files = get_all_module_files(aModule)
    targetDir = os.path.join("modules", get_underscore_module_name(aModule))
    os.makedirs(targetDir, exist_ok=True)
    for aPath in module_files:
        tgt = targetDir
        if "tf_modules" in aPath:
            tgt = os.path.join(targetDir, "tf_module")
            os.makedirs(tgt, exist_ok=True)

        shutil.copy(aPath, os.path.join(tgt, os.path.basename(aPath)))


# Entrypoint
make_valid_files_list()
for aModule in get_all_module_names():
    copy_over_files(aModule)


# Manual steps needed
# k8s-service tf to aws_k8s_service/ and rename to tf_module
# k8s-base to aws_k8s_base/ and rename to tf_module

# Copy opta-k8s-service-helm to modules/
# manually copy aws_document_db.py into modules/aws_documentdb.py and rename it
# manually copy base.py and custom_terraform.py into modules/
