# uptime_monitor
A (very) simple uptime monitor for sites built in python using flask.

This iteration keeps all the needed files (namely chart.js) available offline in the event of a total failure of the external internet connection. 

**bugs likely**
Use or don't - offered for convenience and for easy reference.

## installation
1. clone repository
2. install requirements with pip `pip install -r requirements.txt`

## running the site
on windows: `py main.py`  
on unix / macOS: `python3 main.py`

site will start on: `http://localhost:5000/`