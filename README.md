
Megesz -- a Django demo
=======================

- a webapp concept for secure communication on a local network via http
- machines on a network would each run this django project, with one having the server key, the others acting as clients (with random keys)
- servers and clients broadcast/exchange keys via udp
- after that, secure requests (and responses) are encrypted: `browser` -> `local django` -> `[encrypted request]` -> `remote machine`

Run with Docker
---------------
- containers use port 8000-8005, these need to be accessible on the machine running docker (so allow them in your vagrantfile, firewall, etc)
- set the hostname of your docker machine in `lab/settings_docker.py`: `LAB.docker = {'host': 'your_host'}`
- `./build.sh` will build a python base image, and another image for the project
- `./run.sh` will (re)start containers, a server and at least one client (you can allow more)
- open `http://your_host:8000` and you can test encrypted requests between the server and clients
- `reset.sh` will clean up images and containers

TODO
----
- finish adapting fully to latest Django, revise confs, clean up
- setup with docker compose
- revise/update runsilent.py if needed
