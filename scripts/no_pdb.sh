cd ..
blah=`grep -rl "import pdb" .`
if [[ -n ${blah} ]]; then
  echo ${blah}
  exit 1
fi