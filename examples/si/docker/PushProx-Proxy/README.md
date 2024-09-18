# Run next commands to update PushProx-proxy docker image
```
docker build -t sistemasstratio/pushprox-proxy:<version> .
docker tag sistemasstratio/pushprox-proxy:<version> sistemasstratio/pushprox-proxy:latest

docker push sistemasstratio/pushprox-proxy:<version> && docker push sistemasstratio/pushprox-proxy:latest
```