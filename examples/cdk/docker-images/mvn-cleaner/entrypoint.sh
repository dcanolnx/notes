#!/bin/bash
#######
# This script needs $BEFORE env to indicate how many days must have passed to delete an item 
#######
if [[ -d "/maven" ]] ; then
	re='^[0-9]+$'
	if [[ $BEFORE =~ $re ]] ; then
		# We get all directories which contains one or more files older than BEFORE
		directories=$(find /maven/ -type f -atime +$BEFORE -printf '%h\n')
	   	if [[ -z $directories ]]; then	   	
	   		echo "There are not directories to delete before "$BEFORE" days"
	   	else
	   		echo "Proccess directories which contains one or more files older than "$BEFORE
			for i in $directories; do 
				if [[ -d $i ]]; then
					# We check if there are files accessed recently
					files=$(find $i -type f -atime -$BEFORE)
					if [[ ! -z $files ]]; then
						echo "Skip delete of directory "$i" there are some files accessed recently days: "$files
					else
						echo "Delete directory "$i
						rm -rf $i
					fi
			    fi
			done
	   	fi
	   	exit 0
	else
		echo "ERROR: env BEFORE must be a number"
		exit 1
	fi
else
	echo "ERROR: dir /maven does not exists"
	exit 1
fi