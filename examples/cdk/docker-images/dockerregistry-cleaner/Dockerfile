FROM ubuntu:18.04

USER root

## DEPENDENCIES
RUN apt update && apt -y install python3 python3-pip wget curl

## YACRON
# https://github.com/gjcarneiro/yacron
RUN wget http://qa.int.stratio.com/repository/new-thirdparty-binaries/org/yacron/yacron -O /usr/local/bin/yacron && chmod +x /usr/local/bin/yacron
COPY docker-images/dockerregistry-cleaner/yacronjob.cfg /opt/

## DOCKERREGISTRYCLEANER
COPY docker-images/dockerregistry-cleaner/dockerregistry_cleaner.py /usr/local/bin/
RUN chmod +x /usr/local/bin/dockerregistry_cleaner.py
COPY docker-images/dockerregistry-cleaner/requeriments.txt /root/requeriments.txt
RUN pip3 install -r /root/requeriments.txt
RUN touch /var/log/dockerregistry-cleaner.log && chmod -R 766 /var/log/*.log

RUN adduser -u 1001 stratio --disabled-password
USER stratio

CMD [ "/usr/local/bin/yacron","-c","/opt/yacronjob.cfg","-l","WARNING" ]