FROM alpine:3.14

RUN apk add python3 py3-pip curl jq

RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
RUN install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

COPY docker-images/keoscicd-cleaner/keoscicd-cleaner.py /bin/
COPY docker-images/keoscicd-cleaner/create-kubeconfig.sh /bin/

RUN chmod +x /bin/keoscicd-cleaner.py
RUN chmod +x /bin/create-kubeconfig.sh

RUN /bin/create-kubeconfig.sh

ENTRYPOINT ["/usr/bin/python3","/bin/keoscicd-cleaner.py"]