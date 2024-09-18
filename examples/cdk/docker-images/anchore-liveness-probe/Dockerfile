# docker build . -t anchore-liveness-probe:0.1.0-SNAPSHOT

FROM bitnami/kubectl:1.21.10

COPY docker-images/anchore-liveness-probe/entrypoint.sh /entrypoint.sh
# RUN chmod +x entrypoint.sh

ENV TIME="1h"

ENTRYPOINT ["/bin/bash","/entrypoint.sh"]
