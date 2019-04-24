
echo 'Removing all containers...'
docker rm -f `docker ps -aq -f label=megesz`

echo 'Starting containers...'
docker run -h mserver  --name mserver  -l megesz -p 8000:8000 -v /vagrant/megesz:/home/megesz -d megesz --settings=lab.settings_docker
docker run -h mclient1 --name mclient1 -l megesz -p 8001:8000 -v /vagrant/megesz:/home/megesz -d megesz
# docker run -h mclient2 --name mclient2 -l megesz -p 8002:8000 -v /vagrant/megesz:/home/megesz -d megesz
# docker run -h mclient3 --name mclient3 -l megesz -p 8003:8000 -v /vagrant/megesz:/home/megesz -d megesz
# docker run -h mclient4 --name mclient4 -l megesz -p 8003:8000 -v /vagrant/megesz:/home/megesz -d megesz
# docker run -h mclient5 --name mclient5 -l megesz -p 8003:8000 -v /vagrant/megesz:/home/megesz -d megesz

docker ps -a -f label=megesz
