#!/bin/bash

#This file is a wrapper file, so we can store the envVar and the Python Virtual Env before running the python file
export SIOclientDir=`pwd` #you should run this script from the directory where it's stored (the git repo top level)
#file='./capstoneclient/capstoneclient.py'
file=$1
shift
rest_of_args=$@

echo -n `date +"%Y-%m-%d %H:%M:%S.xxxxxx---"` >> ./client_dev.log 2>&1
echo "Run Py script: ${file} $rest_of_args" >> ./client_dev.log 2>&1
. env/bin/activate
#DW added -u for 'unbuffered' mode, which hopefully means I don't have to put flush=True on all prints
./env/bin/python3 -u $file $rest_of_args >> ./client_dev.log 2>&1 
