
# remove containers and images
docker rm -f `docker ps -aq -f label=megesz`
docker rmi -f megesz megesz-base
