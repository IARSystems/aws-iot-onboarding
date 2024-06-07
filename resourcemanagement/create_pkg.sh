#!/bin/bash

poetry export --format requirements.txt --output requirements.txt

pip install --target=./dependencies -r ./requirements.txt

pip install --platform manylinux2014_x86_64 --target=./dependencies --implementation cp --python-version 3.10 --only-binary=:all: --upgrade jwcrypto

cp ../runtimescript/runtimescript.py ./dependencies

cd ./dependencies

zip -r ../deployment_package.zip .

cd ..
