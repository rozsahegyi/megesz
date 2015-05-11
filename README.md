
Megesz -- a Django demo
=======================

Concept
-------
 - this is a demo/exercise for secure communication on a network over http
 - machines on a network would each run this django project
 - one of them has a server key, the others act as clients (with random keys)
 - servers and clients broadcast/exchange keys
 - secure requests (and responses) are encrypted:
   - (browser) -> (local django) -[encrypted request]-> (remote machine)

Demo on one host
----------------
 - install this into a virtualenv, pip install -r requirements.txt
 - ./run_local.sh
 - wait for django instances to start, then open http://localhost:8000
 - a demo page should open with some explanation and details
 - the demo runs 4 django instances, and can take some cpu time
 - ./reset.sh to stop (will stop python processes)

Demo with Docker
----------------
 - have or install Docker
 - ./build.sh will build two images (a base and one set up for the project)
 - set the hostname (or ip) of your docker machine in lab/settings_docker.py
   - LAB.docker = {'host': 'your_host'}
   - your browser should be able to access your_host:8000-8003
 - ./run_docker.sh - this will run 4 containers, each with a django instance
 - open http://localhost:8000 
