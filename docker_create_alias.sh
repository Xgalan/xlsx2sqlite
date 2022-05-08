#!/bin/bash
shopt -s expand_aliases
alias xlsx2sqlite='docker run -it --rm --mount type=bind,src=`pwd`,dst=/tmp --workdir /tmp xlsx2sqlite:compile-py3.7'