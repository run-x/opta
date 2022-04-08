#!/bin/bash

cd ..
blah=$(grep -rl "import pdb" ./opta)
if [[ -n ${blah} ]]; then
	echo "${blah}"
	exit 1
fi
