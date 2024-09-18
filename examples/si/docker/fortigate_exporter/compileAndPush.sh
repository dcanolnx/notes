#! /bin/sh

version="beta-20210104-ipv6-policy"

docker build -t sistemasstratio/fortigate-exporter:${version} .
docker tag sistemasstratio/fortigate-exporter:${version} sistemasstratio/fortigate-exporter:latest

docker push sistemasstratio/fortigate-exporter:${version} 
docker push sistemasstratio/fortigate-exporter:latest
