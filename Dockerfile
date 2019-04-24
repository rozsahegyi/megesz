
FROM megesz-base

WORKDIR /home/megesz
ADD . /home/megesz

CMD ["--settings=lab.settings_docker_client"]
ENTRYPOINT ["./manage.py", "runserver", "0.0.0.0:8000"]
