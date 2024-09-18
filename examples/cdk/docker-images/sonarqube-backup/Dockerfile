# This container is used to grate and recover sonar backup
FROM alpine:latest

RUN apk update && apk add bash && apk add coreutils && apk add jq && apk add openssh && apk add sshpass
RUN apk --no-cache add curl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
RUN install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

COPY docker-images/sonarqube-backup/entrypoint.sh /opt
RUN chmod +x /opt/entrypoint.sh
ENTRYPOINT [ "/bin/bash","/opt/entrypoint.sh" ]