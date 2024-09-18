#!/bin/bash
# This script contains some utils to be executed on; https://github.com/Stratio/docker-registry.helm

#VARS
DOCKERREGISTRY="http://docker-registry:5000/v2/"
ACTION=$1
NAMESPACE=$2
IMAGE=$3
TAG=$4

print_help () {
	echo "Usage: 
	DockerRegistry_Utils.sh <get|delete> <namespace> <image> <tag> 

Examples: 
	DockerRegistry_Utils.sh get keos-ci stratio/keos-installer
	DockerRegistry_Utils.sh delete keos-ci stratio/keos-installer 0.5.0-PR895-SNAPSHOT
Info:
	This script contains some utils to be executed on; https://github.com/Stratio/docker-registry.helm"
}

get_tags() {
	tags=$(/usr/local/bin/kubectl exec --container dockerregistry-cleaner -it $pod_name -n $NAMESPACE -- curl $DOCKERREGISTRY$IMAGE/tags/list)
	echo "$tags"
}

delete_image() {
	dockercontentid=$(/usr/local/bin/kubectl exec --container dockerregistry-cleaner -i $pod_name -n $NAMESPACE -- curl -s -I -H 'Accept: application/vnd.oci.image.index.v1+json' $DOCKERREGISTRY$IMAGE/manifests/$TAG | grep Docker-Content-Digest | cut -d ' ' -f2 | tr -d '\r')
	command="curl -X DELETE -H 'Accept: application/vnd.oci.image.index.v1+json' $DOCKERREGISTRY$IMAGE/manifests/$dockercontentid"
	del=$(/usr/local/bin/kubectl exec --container dockerregistry-cleaner -it $pod_name -n $NAMESPACE -- $command )
}

#Check number arguments are correct
if [[ "$#" -eq 4 && "$1" = "delete" ]] || [[ "$#" -eq 3 && "$1" = "get" ]] ; then
	# Check namespace is available
	namespaces=$(/usr/local/bin/kubectl get ns | cut -d " " -f1)
	if [[ -z $(echo $namespaces | grep " $2 ")  ]] ;then
		echo "Error - namespace $2 is not available"
	else
		# Get docker-registry pod name
		pod_name="$(/usr/local/bin/kubectl get pods -n $2 | grep docker-registry | cut -d ' ' -f1)"
		if [[ -z $pod_name ]] ;then
			echo "Error - Pod docker-registry is not running"
		else
			# Check if container dockerregistry-cleaner is running in Pod  docker-registry
			if [[ -z $(/usr/local/bin/kubectl get pod $pod_name -n keos-ci -o jsonpath='{.spec.containers[*].name}' | grep 'dockerregistry-cleaner') ]]; then
				echo "Error - Container dockerregistry-cleaner is not running in $pod_name "
			else
				if [[ "$1" = "get" ]]; then
					get_tags
				fi
				if [[ "$1" = "delete" ]]; then
					delete_image
				fi
			fi
		fi
	fi
else
	echo "Error - Bad arguments"
	print_help
	exit 1
fi 
