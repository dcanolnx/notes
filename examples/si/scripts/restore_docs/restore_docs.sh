#!/usr/bin/bash
################################################################################
# Vars                                                                         #
################################################################################
MYSQL_USER=documentation
MYSQL_PASSWORD=
MYSQL_ROOT_USER=root
MYSQL_ROOT_PASSWORD=
IP_PRODSERVER=10.121.0.116
################################################################################
# Functions                                                                    #
################################################################################
Help() {
   echo "This script downloads documentroot and SQL from *.docs.stratio.com and import it to this local machine"
   echo
   echo "Syntax: scriptTemplate [h|f|n]"
   echo "options:"
   echo "-h     Print this Help."
   echo "-l     Get date of last documentroot downloaded if exists"
   echo "-f     Fast mode, using last documentroot downloaded if exists"
   echo "-n     Normal mode, download sql and documentroot to get latest copy"
   echo
}


Fast_mode() {
   echo "-- Script running on Fast Mode --"

   echo "Generate documentroot"
   rm -rf /var/www/html/documentation
   tar -xf /var/www/html/documentation.tar.gz -C /
   cp /opt/restore/data/wp-config.php /var/www/html/documentation/
   chown apache:apache /var/www/html/documentation/wp-config.php
   chmod 774 /var/www/html/documentation/wp-config.php

   echo "Delete local database documentation"
   mysql -u $MYSQL_ROOT_USER -p$MYSQL_ROOT_PASSWORD -e "drop database documentation;"
   echo "Create local database documentation"
   mysql -u $MYSQL_ROOT_USER -p$MYSQL_ROOT_PASSWORD -e "create database documentation;"
   sed -i 's/utf8mb4_unicode_520_ci/utf8_general_ci/g' /opt/restore/data/documentation_backup.sql
   sed -i 's/utf8mb4/utf8/g' /opt/restore/data/documentation_backup.sql
   echo "Import sql file to local database"
   mysql -u $MYSQL_USER -p$MYSQL_PASSWORD documentation < /opt/restore/data/documentation_backup.sql
}

Normal_mode() {
   echo "-- Script running on Normal Mode --"
   echo "rm tar.gz on production server"
   ssh $IP_PRODSERVER rm /var/www/html/documentation.tar.gz
   echo "tar document root"
   ssh $IP_PRODSERVER tar -zcf /var/www/html/documentation.tar.gz /var/www/html/documentation
   [ -e /var/www/html/documentation.tar.gz ] && rm /var/www/html/documentation.tar.gz
   echo "Download documentroot from prod"
   scp $IP_PRODSERVER:/var/www/html/documentation.tar.gz /var/www/html/
   echo "Download sql file from prod"
   scp $IP_PRODSERVER:/var/www/backup/documentation_backup.sql /opt/restore/data/
   Fast_mode
}

Last_documentrootdownload() {
   if [ -e /var/www/html/documentation.tar.gz ] 
   then
      date -r /var/www/html/documentation.tar.gz
   else
      echo "There is not documentroot downloaded"
   fi

}

################################################################################
# Main                                                                         #
################################################################################
# Get the options
while getopts ":hfnl" option; do
   case $option in
      h) # display Help
         Help
         exit;;
      f) # Fast mode
         Fast_mode
         exit;;
      n) # Normal mode
         Normal_mode
         exit;;
      l) # Last document root downloaded
         Last_documentrootdownload
         exit;;
     \?) # incorrect option
         echo "Error: Invalid option"
         exit;;
   esac
done

