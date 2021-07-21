#!/bin/bash

echo ===============================================
echo = this script assumes you have already set up  
echo = python 3.6 and the virtualenv
echo ===============================================
cd src
./maze_make_aiml.py 
echo generate maze

./maze_make_aiml.py --dir ./../chat/ --no-moves --look-word "what was that"
echo generate how-to
