#!/bin/bash
BACKUP_DATA_DIRECTORY="/backup_ldap/data"
find $BACKUP_DATA_DIRECTORY  -mtime +5 -name "*.ldif" -type f -delete
/sbin/slapcat -v -l  $BACKUP_DATA_DIRECTORY/backup_ldap.$(date +%F).ldif
/sbin/slapcat -n 0 -l  $BACKUP_DATA_DIRECTORY/backup_ldap_config.$(date +%F).ldif