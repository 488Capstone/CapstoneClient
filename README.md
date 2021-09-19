This repo contains the code for a portion of a Senior Design Capstone project at Arizona State University.
This code is for the actual controller device.

Project title: Solar-Powered Smart Irrigation Controller

Team Members: Collin T, Doug W, Nolan B, Xavier R, Jeff M

Project Title: Solar-Powered Smart Backyard Irrigation

For a first time install (if you just cloned the git repo) run this file:
./runFirstTimeInstall.sh

runCLI.sh is a script made for running the capstoneclien.py file
runWebGuiServer.sh is a script made for running the web gui interface that can be accessed on the same Wifi network

capstoneclient.py is the main script. This includes set-up and operation, and is currently limited to CLI I/O.

DW: I've made a file called funcIndex.py where I'm collecting the functions used in CapstoneClient with brief snippets of info about them
For ongoing operations, CronTab is used to schedule relevant tasks via dailyactions.py and zonecontrol.py.

dailyactions.py contains functionality to:
	1) take sensor readings,
	2) update weather data / ET calculations.

	the functionality to be executed is controlled by CLI arguments passed from CronTab. Sensor functions and
	weather data functions will be scheduled at regular but different intervals.

