#!/bin/bash

case "$1" in
    help)
        echo $"Usage: $0 {recreate|help}"
        exit 0
    ;;
    jira)
        docker volume rm azufre-jira
        docker volume create --driver local \
            --opt type=nfs \
            --opt o=addr=azufre.int.stratio.com,rw \
            --opt device=:/sistemas/backup-Jira_Confluence/jira \
            azufre-jira

        # JIRA
        if [[ $(docker ps -a | grep backup-jira) ]]
        then
        echo "Delete Docker Container"
        docker rm --force backup-jira > /dev/null 2>&1
        else
        echo "Docker Container doesn't exists"
        fi

        docker run \
        --name backup-jira \
        -d \
        -v azufre-jira:/tmp/backup \
        -e "DOWNLOAD_FOLDER=/tmp/backup" \
        -e "EMAIL=sysinternal@stratio.com" \
        -e "API_TOKEN=07j5OacJLow8ennOIFeF6CBF" \
        -e "HOSTNAME=stratio.atlassian.net" \
        sistemasstratio/cloud-backup:0.2

        exit 0
    ;;
    confluence)
        docker volume rm azufre-confluence
        docker volume create --driver local \
            --opt type=nfs \
            --opt o=addr=azufre.int.stratio.com,rw \
            --opt device=:/sistemas/backup-Jira_Confluence/confluence \
            azufre-confluence

        ## CONFLUENCE
        if [[ $(docker ps -a | grep backup-confluence) ]]
        then
        echo "Delete Docker Container"
        docker rm --force backup-confluence > /dev/null 2>&1
        else
        echo "Docker Container doesn't exists"
        fi

        docker run \
        --name backup-confluence \
        -d \
        -v azufre-confluence:/tmp/backup \
        -e "DOWNLOAD_FOLDER=/tmp/backup" \
        -e "EMAIL=sysinternal@stratio.com" \
        -e "API_TOKEN=07j5OacJLow8ennOIFeF6CBF" \
        -e "HOSTNAME=stratio.atlassian.net/wiki" \
        sistemasstratio/cloud-backup:0.2

    ;;
    clean)
        # Delete old backups 1 month
        mkdir -p /tmp/backup-jira_confluence/
        mount.nfs azufre.int.stratio.com:/sistemas/backup-Jira_Confluence/ /tmp/backup-jira_confluence
        find /tmp/backup-jira_confluence/confluence -type f -name '*.zip' -mtime +15 -exec rm {} \;
        find /tmp/backup-jira_confluence/jira -type f -name '*.zip' -mtime +15 -exec rm {} \;
        umount /tmp/backup-jira_confluence

        exit 0
    ;;
    *)
        echo $"Usage: $0 {jira|confluence|clean|help}"
        exit 0
    ;;

esac


exit 0

## Crontab
# 0 0 * * 6 root bash /docker_configs/backup-jira_confluence.sh jira
# 0 0 * * 0 root bash /docker_configs/backup-jira_confluence.sh confluence
# 0 0 * * 12 root bash /docker_configs/backup-jira_confluence.sh clean
