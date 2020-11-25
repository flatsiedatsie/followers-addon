#!/bin/bash -e

version=$(grep '"version"' manifest.json | cut -d: -f2 | cut -d\" -f2)

# Clean up from previous releases
rm -rf *.tgz lib package SHA256SUMS

# Prep new package
mkdir -p dir package

# Pull down Python dependencies
pip3 install -r requirements.txt -t lib --no-binary :all: --prefix ""

# Put package together
cp -r pkg lib LICENSE manifest.json *.py README.md css images js views package/
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
TARFILE="followers-${version}.tgz"
tar czf ${TARFILE} package

shasum --algorithm 256 ${TARFILE} > ${TARFILE}.sha256sum
cat ${TARFILE}.sha256sum

rm -rf SHA256SUMS package