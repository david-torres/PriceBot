Requirements
============

Python, pip, mysql


Installation
============

    $ pip install -r requirements.txt

Installed via pip
==================

Needed by the scrolls client to authenticate

	requests==2.0.1

Used to read the config file

	PyYAML==3.10

Used to create an easy to start/stop daemon process

	zdaemon==4.0.0


Used to do fuzzy matching to catch misspelled/abbreviated scroll names

	fuzzywuzzy==0.2

Used to connect to a db and insert some data using MySql

	sqlsoup==0.9.0
	MySQL-python==1.2.4



Usage
======

Copy config.yaml.sample to config.yaml. Fill in relevant values.

    $ cp config.yaml.sample config.yaml

Make sure the bash start/stop scripts are executable.

    $ chmod +x *.sh

Start the bot
==============

    $ ./start.sh

Stop the bot
=============

    $ ./stop.sh
