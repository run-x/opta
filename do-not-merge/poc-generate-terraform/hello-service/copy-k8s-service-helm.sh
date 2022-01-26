#!/bin/bash

# ex: aws_base
module_name=$1

OPTA_MODULE_DIR=$HOME/github/opta/modules

SOURCE_DIR="$OPTA_MODULE_DIR/opta-k8s-service-helm"
TARGET_DIR="./modules/$module_name/tf_module/opta-k8s-service-helm"
echo "Copying $SOURCE_DIR to $TARGET_DIR"

cp -r $SOURCE_DIR $TARGET_DIR

ls -R -l $TARGET_DIR
echo "Done"
