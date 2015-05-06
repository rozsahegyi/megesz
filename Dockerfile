
FROM base
MAINTAINER laszlo@rozsahegyi.info

WORKDIR /home/megesz
ADD requirements.txt /home/requirements.txt
RUN pip install -r /home/requirements.txt

CMD ["--settings=lab.settings_docker_client"]
ENTRYPOINT ["./manage.py", "runsilent", "0.0.0.0:8000"]
