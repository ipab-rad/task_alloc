#!/bin/bash


if [[ $OSTYPE == 'darwin15' ]]; then
    export PATH=$PATH:../../MiniZincIDE.app/Contents/Resources/
    CMD="../../MiniZincIDE.app/Contents/Resources/mzn-gecode $@"
else
    export PATH=$PATH:../../MiniZincIDE-2.0.11-bundle-linux-x86_64/
    CMD="../../MiniZincIDE-2.0.11-bundle-linux-x86_64/mzn-gecode $@"
fi

echo $CMD
$CMD
