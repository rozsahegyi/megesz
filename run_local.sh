
# all servers listen on the same udp port currently
# thus sleep is necessary because if all servers broadcast at once on startup,
# udp packages seem to get lost or ignored

./manage.py runsilent 0.0.0.0:8000 --settings=lab.settings_local &
sleep 1
./manage.py runsilent 0.0.0.0:8001 --settings=lab.settings_local_client &
sleep 1
./manage.py runsilent 0.0.0.0:8002 --settings=lab.settings_local_client &
sleep 1
./manage.py runsilent 0.0.0.0:8003 --settings=lab.settings_local_client &
