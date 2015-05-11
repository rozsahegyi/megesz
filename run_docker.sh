
echo 'Removing running containers...'
docker rm -f mserver mclient1 mclient2 mclient3

echo 'Starting containers...'
docker run -h mserver  --name mserver  -p 8000:8000 -v /work/megesz:/home/megesz -d megesz --settings=lab.settings_docker
docker run -h mclient1 --name mclient1 -p 8001:8000 -v /work/megesz:/home/megesz -d megesz
docker run -h mclient2 --name mclient2 -p 8002:8000 -v /work/megesz:/home/megesz -d megesz
docker run -h mclient3 --name mclient3 -p 8003:8000 -v /work/megesz:/home/megesz -d megesz

docker ps -a
