# Use the Script compileAndPush.sh to do all the work
Change the variable dirst
```
./compileAndPush.sh
```

# Or run next commands to update fortigate-exporter docker image
```
docker build -t sistemasstratio/fortigate-exporter:<version> .
docker tag sistemasstratio/fortigate-exporter:<version> sistemasstratio/fortigate-exporter:latest

docker push sistemasstratio/fortigate-exporter:<version> && docker push sistemasstratio/fortigate-exporter:latest
```