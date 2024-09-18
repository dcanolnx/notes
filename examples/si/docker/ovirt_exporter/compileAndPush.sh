#! /bin/sh

version="0.9.1"

docker build -t sistemasstratio/ovirt-exporter:${version} .
docker tag sistemasstratio/ovirt-exporter:${version} sistemasstratio/ovirt-exporter:latest

docker push sistemasstratio/ovirt-exporter:${version} 
docker push sistemasstratio/ovirt-exporter:latest
