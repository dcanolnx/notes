# docker run --rm --name vnotifier -v $PWD/vnotifier.conf:/etc/stratio/vnotifier.conf -v $PWD/vnotifier:/var/lib/vnotifier vnotifier
FROM alpine:3.14.1 
ENV CREATED 2018-10-09
LABEL maintainer="Informatica Interna <sysinternal@stratio.com>"
LABEL name="vnotifier" \
        version="0.9" \
        description="VMs accounting" \
        vendor="Stratio" \
        license="Stratio license"

# Install requisites
RUN apk update
RUN apk add shadow python3 py3-netifaces py3-pip python3-dev curl-dev libressl-dev libxml2-dev gcc musl-dev
RUN pip3 install pyvmomi keystoneauth1 python-keystoneclient python-novaclient python-cinderclient ovirt-engine-sdk-python

# Create user
RUN useradd -m vnotifier 

# We add the script
ADD vnotifier.py /opt/vnotifier/vnotifier.py
ADD vnotifier.conf /opt/vnotifier/vnotifier.conf


USER vnotifier
WORKDIR /opt/vnotifier

ENTRYPOINT ["python3", "/opt/vnotifier/vnotifier.py", "/etc/stratio/vnotifier.conf"]
