#!/bin/bash

version=$(grep '"version":' manifest.json | cut -d: -f2 | cut -d\" -f2)

rm -rf SHA256SUMS package
rm -rf ._*
mkdir package

cp -r pkg LICENSE manifest.json *.py README.md css images js views package/
find package -type f -name '*.pyc' -delete
find package -type f -name '._*' -delete
find package -type d -empty -delete
sudo rm -rf /home/pi/.mozilla-iot/addons/followers/package/pkg/pycache
#cp -r pkg css images js views package/

cd package
find . -type f \! -name SHA256SUMS -exec sha256sum {} \; >> SHA256SUMS
cd ..

tar czf "followers-${version}.tgz" package
sha256sum "followers-${version}.tgz"
