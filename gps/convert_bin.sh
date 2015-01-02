#!/bin/sh

usage="Usage: $0 [input file] [output file]"
ifile=${1?$usage}
ofile=${2?$usage}

xxd -b -g0 $ifile | cut -f2 -d' ' | tr -d '\n' | sed 's|\(.\)|\1 |g' > $ofile
