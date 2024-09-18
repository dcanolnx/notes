# Run next commands to update rundeck-exporter docker image
```
docker build -t sistemasstratio/rundeck-exporter:<version> .
docker tag sistemasstratio/rundeck-exporter:<version> sistemasstratio/rundeck-exporter:latest

docker push sistemasstratio/rundeck-exporter:<version> && docker push sistemasstratio/rundeck-exporter:latest
```