# docker build . -t maven-cleaner:1.0
FROM ubuntu:20.04
COPY docker-images/mvn-cleaner/entrypoint.sh /root/entrypoint.sh
RUN chmod +x /root/entrypoint.sh
ENV BEFORE="7"
ENTRYPOINT ["/bin/bash","/root/entrypoint.sh"]