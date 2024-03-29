#!/bin/bash

#FYI- In order to push edits to origin, you should've used the below cmd with git SSH address to create this git repository.
# Talk to Doug if you're not sure what this means!
#git clone git@github.com:488Capstone/CapstoneClient.git

#You should run this script from the */CapstoneClient/ directory

#DW 2021-09-21-20:22 It turns out git preserves the permission settings of files so no need to do this.
#printf "***set all the files to be executable that need to be run\n"
#chmod 755 -v ./runCLI.sh
#chmod 755 -v ./runWebGuiServer.sh
#chmod 755 -v ./dailyactions.py
#chmod 755 -v ./zone_control_devmode.py
#chmod 755 -v ./zone_control.py

if [[ -e ./env ]]; then
	printf "Removing ./env directory. These should not be stored in git origin but instead created for each user\n"
	printf "DW: it appears safe to delete and re-install venv's multiple times (I've done it testing this script)\n"
	printf "DW: just incase, confirm you wish to call: rm -r ./env (y/n)\n"
	rm -rI ./env
fi

python3 -m venv env
. ./env/bin/activate

#DW install all modules in requirements.txt. 

printf "DW: The Raspberry Pi has some modules which throw errors on the Desktop\n"
printf "DW: so we will load the raspi specific modules only if we're on the Raspi\n"
if [[ -e "/sys/firmware/devicetree/base/model" ]]; then
	printf "DW: I suspect you're on the pi! Will run raspiRequirements!\n"
	printf "DW: If this is wrong, let me know!\n"
	python3 -m pip install -r raspiRequirements.txt
	#DW 2021-09-23-16:16 for some reason smbus is a pain in my a$$
	python3 -m pip install smbus --upgrade
else
	printf "DW: I suspect you're NOT on the pi!\n"
	printf "DW: If this is wrong, let me know!\n"
fi

#read -p "**Is this running on the Raspberry Pi? (Y/N): " confirm  
#if [[ "$confirm" == [yY] || "$confirm" == [yY][eE][sS] ]]; then
#	python3 -m pip install -r raspiRequirements.txt
#fi

python3 -m pip install -r desktopRequirements.txt


printf "\nDW: Installing our CapstoneClient module (allows the webgui to use the sql database)\n"
printf "DW: Ask me about it if you're thinking, 'wtf why?' Maybe there's a better solution!\n"
pip install -e .

#below script shoot start up the webgui, set the crontab, and set the starting state of GPIO's
./runStartUp.sh

#printf "\n***Install Python Flask\n"
#python3 -m pip install Flask==2.0.1
#
#printf "\n***Install Python CronTab\n"
#python3 -m pip install python-CronTab==2.5.1
#
#printf "\n***Install Python cron-descriptor\n"
#python3 -m pip install cron-descriptor==1.2.24
#
#printf "\n***Install Python sqlalchemy\n"
#python3 -m pip install sqlalchemy==1.4.23

# adding so terminal window doesn't close on completion:
$SHELL
