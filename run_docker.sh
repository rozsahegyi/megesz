
docker rm -f mserver mclient1 mclient2 mclient3

# interactive:
# docker run -h mserver --name mserver -w /home/megesz -p 8000:8000 -v /work/megesz:/home/megesz -it megesz /bin/bash
# run without ENTRYPOINT:
# docker run -h mserver --name mserver -w /home/megesz -p 8000:8000 -v /work/megesz:/home/megesz -d megesz /home/megesz/manage.py runsilent 0.0.0.0:8000

# docker run -h mserver  --name mserver  -p 8000:8000 -v /work/megesz:/home/megesz -d megesz ./manage.py runsilent 0.0.0.0:8000 --settings=lab.settings_docker

docker run -h mserver  --name mserver  -p 8000:8000 -v /work/megesz:/home/megesz -d megesz --settings=lab.settings_docker
docker run -h mclient1 --name mclient1 -p 8001:8000 -v /work/megesz:/home/megesz -d megesz
docker run -h mclient2 --name mclient2 -p 8002:8000 -v /work/megesz:/home/megesz -d megesz
docker run -h mclient3 --name mclient3 -p 8003:8000 -v /work/megesz:/home/megesz -d megesz

docker ps -a
