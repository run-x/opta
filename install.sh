#! /usr/bin/env bash

set -u

# Check if script is run non-interactively (e.g. CI)
# If it is run non-interactively we should not prompt for passwords.
if [[ ! -t 0 || -n ${CI-} ]]; then
  NONINTERACTIVE=1
fi

TEMP_LOCAL="/tmp/opta_local"

abort() {
  printf "%s\n" "$1"
  exit 1
}

# Compares two version numbers.
# Returns 0 if the versions are equal, 1 if the first version is higher, and 2 if the second version is higher.
# Source Code: https://stackoverflow.com/questions/4023830/how-to-compare-two-strings-in-dot-separated-version-format-in-bash
# You can run the test cases by using the below command:
# /bin/bash -c "$(curl -fsSL  https://gist.githubusercontent.com/nsarupr/28a5af20ef5462cdd1f4c95739203246/raw/2cc50b6bd2e973bee8c6ef6269f731a78862bb37/compare_version.sh)"
compare_version() {
  if [[ $1 == "$2" ]]; then
    return 0
  fi
  local IFS=.
  local i ver1=($1) ver2=($2)
  # fill empty fields in ver1 with zeros
  for ((i = ${#ver1[@]}; i < ${#ver2[@]}; i++)); do
    ver1[i]=0
  done
  for ((i = 0; i < ${#ver1[@]}; i++)); do
    if [[ -z ${ver2[i]} ]]; then
      # fill empty fields in ver2 with zeros
      ver2[i]=0
    fi
    if ((10#${ver1[i]} > 10#${ver2[i]})); then
      echo 1
      return
    fi
    if ((10#${ver1[i]} < 10#${ver2[i]})); then
      echo 2
      return
    fi
  done
  echo 0
  return
}

trim_version() {
  VERSION="$1"
  firstChar=${VERSION:0:1}
  if [[ ${firstChar} == "v" || ${firstChar} == "V" ]]; then
    VERSION=${VERSION:1}
  fi
  echo "${VERSION}"
}

check_prerequisites() {
  echo "Checking Prerequisites..."
  # declare -a prereq   # Throws "unbound variable" error on Ubuntu 20.04 LTS Focal Fossa on Line #38
  hard_prereq=()
  soft_prereq=()
  if ! unzip_loc="$(type -p unzip)" || [[ -z $unzip_loc ]]; then
    hard_prereq+=(unzip)
  fi

  if ! curl_loc="$(type -p curl)" || [[ -z $curl_loc ]]; then
    hard_prereq+=(curl)
  fi

  if ! terraform_loc="$(type -p terraform)" || [[ -z $terraform_loc ]]; then
    soft_prereq+=(terraform)
  fi

  if ! docker_loc="$(type -p docker)" || [[ -z $docker_loc ]]; then
    soft_prereq+=(docker)
  fi

  if [[ ${#hard_prereq[@]} -gt 0 ]]; then
    abort "Please install the following prerequisites: (${hard_prereq[*]})"
  fi

  if [[ ${#soft_prereq[@]} -gt 0 ]]; then
    echo "Opta would require (${soft_prereq[*]}) to run properly. Please install these."
  fi
}

# Check OS
OS="$(uname)"

echo "Welcome to the opta installer."

check_prerequisites

# Set VERSION
VERSION="${VERSION:-}"

if [[ -z ${VERSION} ]]; then
  # Determine latest VERSION
  echo "Determining latest version"
  VERSION="$(curl -s https://api.github.com/repos/unionai/opta/releases/latest | grep 'tag_name' | grep -oP '[0-9.]+')"
else
  VERSION=$(trim_version "${VERSION}")
fi

echo "Going to install opta v${VERSION}"

if [[ ${OS} == "Linux" ]]; then
  SPECIFIC_OS_ID=$(grep "ID=" /etc/os-release | awk -F"=" '{print $2;exit}' | tr -d '"')
  if [[ ${SPECIFIC_OS_ID} == "amzn" ]] || [[ ${SPECIFIC_OS_ID} == "centos" ]]; then
    PACKAGE=https://github.com/unionai/opta/releases/download/v$VERSION/opta_centos.zip
  else
    PACKAGE=https://github.com/unionai/opta/releases/download/v$VERSION/opta_linux.zip
  fi
elif [[ ${OS} == "Darwin" ]]; then
  PACKAGE=https://github.com/unionai/opta/releases/download/v$VERSION/opta_mac.zip
else
  abort "Opta is only supported on macOS and Linux."
fi

echo "Downloading installation package..."
curl -s -L "${PACKAGE}" -o /tmp/opta.zip --fail
if [[ $? != 0 ]]; then
  echo "Version ${VERSION} not found."
  echo "Please check the available versions at https://github.com/unionai/opta/releases."
  exit 1
fi
echo "Downloaded"

rm -rf $TEMP_LOCAL
mkdir $TEMP_LOCAL

if [[ -d ~/.opta ]]; then
  if [[ -n ${NONINTERACTIVE-} ]]; then
    echo "Opta already installed. Overwriting..."
    if [[ -d ~/.opta/local ]]; then
      mv ~/.opta/local $TEMP_LOCAL
    fi
    rm -rf ~/.opta
  else
    read -p "Opta already installed. Overwrite? " -n 1 -r
    echo
    if [[ ${REPLY} =~ ^[Yy]$ ]]; then
      if [[ -d ~/.opta/local ]]; then
        mv ~/.opta/local $TEMP_LOCAL
      fi
      rm -rf ~/.opta
    else
      rm -rf /tmp/opta.zip
      exit 0
    fi
  fi
fi

echo "Sleeping..."
sleep 15
echo "Installing..."
unzip -q /tmp/opta.zip -d ~/.opta
rm -rf /tmp/opta.zip
if [[ -d $TEMP_LOCAL/local ]]; then
  mv $TEMP_LOCAL/local ~/.opta/
fi
rm -rf $TEMP_LOCAL
chmod u+x ~/.opta/opta

RUNPATH=~/.opta
# Add symlink if possible, or tell the user to use sudo for symlinking
if ln -fs ~/.opta/opta /usr/local/bin/opta 2>/dev/null; then
  echo "Opta symlinked to /usr/local/bin/opta; You can now type 'opta' in the terminal to run it."
else
  echo "Please symlink the opta binary to one of your path directories; for example using 'sudo ln -fs $RUNPATH/opta /usr/local/bin/opta'"
  echo "Alternatively, you could add the .opta installation directory to your path like so"
  echo "export PATH=\$PATH:${RUNPATH}"
  echo "to your terminal profile."
fi
