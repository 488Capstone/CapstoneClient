#!/bin/bash

export SIOclientDir=`pwd` #you should run this script from the directory where it's stored (the git repo top level)
#file='./capstoneclient/capstoneclient.py'
file='./capstoneclient.py'
echo "Running main capstone client script: $file"

. env/bin/activate
python3 $file

# adding so terminal window not closed to see errors
$SHELL
