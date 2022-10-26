#!/usr/bin/env bash


SCRIPT_DIR=$(dirname "${BASH_SOURCE[0]}")

pushd $SCRIPT_DIR

python -m pylint \
    --output-format=colorized \
    generic_map_api
