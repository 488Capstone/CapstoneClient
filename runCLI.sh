#!/bin/bash

export SIOclientDir=`pwd` #you should run this script from the directory where it's stored (the git repo top level)
file='capstoneclient.py'
echo "Running main capstone client script: $file"

python3 $file
