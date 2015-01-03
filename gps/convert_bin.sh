#!/bin/sh

usage="Usage: $0 [input file] [output file]"
ifile=${1?$usage}
ofile=${2?$usage}

# generate new line every 512 bits
#xxd -b -g0 $ifile | cut -f2 -d' ' | tr -d '\n' | grep -oE '.{1,512}' > $ofile

# generate one big string with 0 and 1s seperated by spaces for octave/matlab
xxd -b -g0 $ifile | cut -f2 -d' ' | tr -d '\n' | sed 's|\(.\)|\1 |g' > $ofile
