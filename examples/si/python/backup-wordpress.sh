#!/bin/bash
#######
# VARS
#######
DIR="/var/www/html/documentation/"
DESTINATION_SFTP_SERVER_USER="backup-bigthings"
DESTINATION_SFTP_SERVER_SERVER="litio.int.stratio.com"
DESTINATION_SFTP_SERVER_DIRECTORY="/home/backup-bigthings/"

#######
# MAIN
#######
if [ -d "$DIR" ]; then
  config_file=$(find $DIR -maxdepth 3 -name "wp-config.php")
  result_find=$(find $DIR -maxdepth 3 -name "wp-config.php" | wc -l)
  if [ $result_find -eq 1 ]; then
  	# We get all neccesary params to connect to database
  	database_name=$(cat $config_file | grep -v "//" | grep 'DB_NAME' | awk -F["'"] '{print $4}')
  	echo $database_name
  	database_user=$(cat $config_file | grep -v "//" | grep 'DB_USER' | awk -F["'"] '{print $4}')
  	echo $database_user
   	database_password=$(cat $config_file | grep -v "//" | grep 'DB_PASSWORD' | awk -F["'"] '{print $4}')
  	echo $database_password
  	database_host=$(cat $config_file | grep -v "//" | grep 'DB_HOST' | awk -F["'"] '{print $4}' | cut -d ":" -f1)
  	echo $database_host
  	# We create directory to save backup
  	mkdir /backup
#  	# Backup of database
  	echo "mysqldump -u $database_user -h $database_host -p$database_password $database_name > /backup/wordpress_database.$(date +%F).sql"
#  	mysqldump -u $database_user -h $database_host -p$database_password $database_name > /backup/wordpress_database.$(date +%F).sql
#  	# Backup of documentroot
#  	tar -zcvf /backup/wordpress_documentroot.$(date +%F).zip /wordpress/
#  	result_find=$(find /backup | wc -l)
#  	if [ $result_find -eq 3 ]; then
#  		# We upload backup via sftp to backup server
#  		cp /key/ssh-privatekey /tmp/ssh-privatekey.key && chmod 700 /tmp/ssh-privatekey.key
#  		scp -o "StrictHostKeyChecking=no"  -i /tmp/ssh-privatekey.key /backup/*  $DESTINATION_SFTP_SERVER_USER@$DESTINATION_SFTP_SERVER_SERVER:$DESTINATION_SFTP_SERVER_DIRECTORY
#  		echo "OK"
#  	else
#  		echo "Error: Backup of mysql or documentroot has not been made correctly"
#  		exit 1
#  	fi
#  else
#  	if [ $result_find -eq 0 ]; then
#  		echo "Error: wp-config.php does not exists in /wordpress directory"
#  		exit 1
#  	else
#  		echo "Error: there are more than one wp-config.php  in /wordpress directory"
#  		exit 1
#  	fi
  fi
else
  echo "Error: ${DIR} not found. It is neccesary to mount wordpress documentroot that you want to do backup in /wordpress"
  exit 1
fi