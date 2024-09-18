# Use the Script compileAndPush.sh to do all the work
Change the variable dirst
```
./compileAndPush.sh
```

# Or run next commands to update ovirt-exporter docker image
```
docker build -t sistemasstratio/ovirt-exporter:<version> .
docker tag sistemasstratio/ovirt-exporter:<version> sistemasstratio/ovirt-exporter:latest

docker push sistemasstratio/ovirt-exporter:<version> && docker push sistemasstratio/ovirt-exporter:latest
```