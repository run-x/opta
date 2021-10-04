cd ..
blah=`grep -rl "import pdb" .`
if [[ -n ${blah} ]]; then
  exit 1
fi