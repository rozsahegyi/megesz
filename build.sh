
echo 'Removing images and containers...'
docker rm -f `docker ps -aq -f label=megesz`

docker build -t megesz-base -f Dockerfile.python-slim .
# docker build -t megesz-base -f Dockerfile.python-alpine .
docker build -qt megesz .
