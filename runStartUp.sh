#!/bin/bash

#you should run this script from the directory where it's stored (the git repo top level)
#TODO finish the DEMO mode setup
#SIO == Solar Irrigation Online
#################################################################################
#	Config Vars
#################################################################################
#DW 2021-10-01-21:15 I set up these if statements so that if you want to run 
# with different values of these config vars but don't want to edit this file,
# you can. Just do something like: export <varName>=1    in the terminal window.
if [[ "$SIO_GUI" == "" ]]; then
	SIO_GUI=1 #run the website at boot up
fi
if [[ "$SIO_PYSTART" == "" ]]; then
	SIO_PYSTART=1 # ran the python STARTUP script which will do stuff like init the GPIO's, and reset the static sys cron's
fi
if [[ "$SIO_DEMO" == "" ]]; then
	export SIO_DEMO=1 # This will eventually tell all of our scripts that we are in a demo mode.
fi
#export SIOclientDir=/home/pi/capstoneProj/fromGit/CapstoneClient
if [[ "$SIOclientDir" == "" ]]; then
	export SIOclientDir=`pwd` #you should run this script from the directory where it's stored (the git repo top level)
fi

#activate the python virtual env
. env/bin/activate

echo "User Config set to:"
echo "SIO_GUI = $SIO_GUI"
echo "SIO_PYSTART = $SIO_PYSTART"
echo "SIO_DEMO = $SIO_DEMO"

if [[ $SIO_PYSTART > 0 ]]; then
	#set gpio's and crontab
	./runPy.sh ./dailyactions.py STARTUP
fi

webgui_runfile="${SIOclientDir}/runWebGuiServer.sh"
webgui_logfile="${SIOclientDir}/webgui.log"

if [[ $SIO_GUI > 0 && -e "$webgui_runfile" ]]; then
	# need to sleep for 10 seconds to allow dhclient to run before the website so we have an IP!
	sleep 10
	$webgui_runfile >> $webgui_logfile 2>&1 
fi

