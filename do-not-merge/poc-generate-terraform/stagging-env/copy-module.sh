#!/bin/bash

# ex: aws_base
module_name=$1

OPTA_MODULE_DIR=$HOME/github/opta/modules
SOURCE_DIR="$OPTA_MODULE_DIR/$module_name/tf_module"
TARGET_DIR="./modules/$module_name/tf_module"
echo "Copying $module_name from $SOURCE_DIR to $TARGET_DIR"

mkdir -p "./modules/$module_name"

# copy everything, should be mostly .tf, with some .sh (ex: eks/openid.tf runs a script)
cp -r $SOURCE_DIR $TARGET_DIR

ls -R -l $TARGET_DIR
echo "Done"
