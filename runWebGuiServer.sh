#!/bin/bash

#SIO == Solar Irrigation Online
#################################################################################
#	Config Vars
#################################################################################
#DW 2021-10-01-21:15 I set up these if statements so that if you want to run 
# with different values of these config vars but don't want to edit this file,
# you can. Just do something like: export <varName>=1    in the terminal window.
if [[ "$SIO_DEV_MODE" == "" ]]; then
	SIO_DEV_MODE=0 #turn on for flask dev mode (website auto-updates when files changed)
fi
if [[ "$SIO_LAN_SITE" == "" ]]; then
	SIO_LAN_SITE=1 #turn on when wanting to test accessing the site from another machine on the WIFI network
fi
#export SIOclientDir=/home/pi/capstoneProj/fromGit/CapstoneClient
export SIOclientDir=`pwd` #you should run this script from the directory where it's stored (the git repo top level)

#export FLASK_APP=webgui_main
#rename this if we call our webgui app a new name, this is the tutorial name
export FLASK_APP=clientgui

#################################################################################
#################################################################################

#activate the python virtual env
. env/bin/activate

echo "User Config set to:"
echo "SIO_DEV_MODE = $SIO_DEV_MODE"
echo "SIO_LAN_SITE = $SIO_LAN_SITE"
echo "SIOclientDir = $SIOclientDir"
echo "FLASK_APP    = $FLASK_APP"

cd ${SIOclientDir}/webgui

# uncomment below line if we want auto-reloaded pages during dev
if [[ ${SIO_DEV_MODE} > 0 ]] ; then
	export FLASK_ENV=development
fi


# This is handled in the db_manager now I think
## if the database doesn't exist yet, initialize it
#dbFile="${SIOclientDir}/webgui/instance/${FLASK_APP}.sqlite"
#if [[ ! -e ${dbFile} ]] ; then
#	echo "Database file not found, initializing at location: $dbFile"
#	flask init-db
#fi

if [[ ${SIO_LAN_SITE} > 0 ]] ; then
	echo "Website available on WIFI network"
	# if you want to run with a LAN accessible page use below line:
	flask run --host `hostname -I | sed 's/ //g'`
else
	echo "Website local to this machine"
	#run from local host
	flask run
fi




