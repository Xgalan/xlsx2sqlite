#!/bin/bash
# build command for docker image
docker build -t xlsx2sqlite:compile-py3.7 \
    --build-arg USER_ID=$(id -u) \
    --build-arg GROUP_ID=$(id -g) .