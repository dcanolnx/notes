# DOCKER_BUILDKIT=1 docker build . -t dockerregistry-api:1.0
# Based on https://github.com/docker/distribution-library-image/blob/master/amd64/Dockerfile

FROM alpine:3.14

RUN apk add python3 py3-pip
RUN pip3 install flask
RUN touch /var/log/garbage-collect && chmod -R 766 /var/log/garbage-collect

COPY --chmod=755 docker-images/dockerregistry-api/registry /bin/registry
COPY docker-images/dockerregistry-api/config-example.yml /etc/docker/registry/config.yml
COPY --chmod=755 docker-images/dockerregistry-api/registry-api.py /bin/

VOLUME ["/var/lib/registry"]

ENTRYPOINT ["/usr/bin/python3","/bin/registry-api.py"]