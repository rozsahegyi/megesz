
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

Demo with secure messaging
--------------------------
 - install this into a virtualenv, pip install -r requirements.txt
 - ./run_local.sh
 - after started, open localhost:8000
 - a demo page should open with some explanation and details
