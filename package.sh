#!/bin/bash 

#-e
set -x # echo commands too

export DEBIAN_FRONTEND=noninteractive

ADDON_ARCH="$1"
#LANGUAGE_NAME="$2"
#PYTHON_VERSION="$3"


echo ""
echo ""

#lsb_release -a
#ldd --version


#pip3 --version

echo ""
echo ""
version=$(grep '"version"' manifest.json | cut -d: -f2 | cut -d\" -f2)






if [ -z "${PYTHON_VERSION}" ]; then
    #echo "YIKES, did NOT get Python version as a parameter."
    # assume the current python3 version is the target one
    PYTHON_VERSION="$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d. -f 1-2)"
    #echo "PYTHON_VERSION from python3: $PYTHON_VERSION"
else
    # python version was explicitly provided
    echo "got Python version as a parameter: ${PYTHON_VERSION}"
fi

echo "whoami         : $(whoami)"
echo "addon version  : $version"
echo "python version : $(python3 --version)"
echo "architecture   : $ADDON_ARCH"
echo "platform       : $(uname -v)"
echo ""

# Setup environment for building inside Dockerized toolchain
[ $(id -u) = 0 ] && umask 0

# Clean up from previous releases
echo "package.sh: removing old files"
rm -rf *.tgz *.sha256sum package SHA256SUMS lib

if [ -z "${ADDON_ARCH}" ]; then
  TARFILE_SUFFIX=
else
  #PYTHON_VERSION="$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d. -f 1-2)"
  #PYTHON_VERSION="3.11"
  TARFILE_SUFFIX="-${ADDON_ARCH}-v${PYTHON_VERSION}"
fi

echo "-----"
echo "TARFILE_SUFFIX : $TARFILE_SUFFIX"
echo "-----"



# Prep new package
echo ""
echo "package.sh: creating package"
mkdir -p lib package

set -e

#if [[ $EUID -ne 0 ]]; then
#      sudo apt install -y python3.11-distutils
#else
#      apt install -y python3.11-distutils
#fi
#curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11
#python3.11 -m pip install --upgrade setuptools==70.0.0 wheel



python3 -m pip install -r requirements.txt -t lib --no-cache-dir --no-binary  :all: --prefix ""


# Put package together
cp -r lib pkg LICENSE manifest.json *.py README.md css images js views  package/
find package -type f -name '*.pyc' -delete
find package -type f -name '._*' -delete
find package -type d -empty -delete
rm -rf package/pkg/pycache

# Generate checksums
echo "generating checksums"
cd package
find . -type f \! -name SHA256SUMS -exec shasum --algorithm 256 {} \; >> SHA256SUMS
cd -

# Make the tarball
echo "creating archive"
TARFILE="followers-${version}${TARFILE_SUFFIX}.tgz"
tar czf ${TARFILE} package

echo "creating shasums"
shasum --algorithm 256 ${TARFILE} > ${TARFILE}.sha256sum
cat ${TARFILE}.sha256sum
#sha256sum ${TARFILE}
#rm -rf SHA256SUMS package

echo ""
echo "DONE! files:"
ls -lh



