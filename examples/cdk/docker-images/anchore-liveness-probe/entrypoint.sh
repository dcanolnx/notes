#!/bin/bash

#########################
## Generate Kubeconfig ##
######################### 
server="https://10.120.14.102:6443"
# name="default-token" 
ca=$(cat /run/secrets/kubernetes.io/serviceaccount/ca.crt | base64 | tr -d '\n')
token=$(cat /run/secrets/kubernetes.io/serviceaccount/token)
namespace=$(cat /run/secrets/kubernetes.io/serviceaccount/namespace)


echo "
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: ${ca}
    server:     ${server}
  name: stratiocicd
contexts:
- context:
    cluster: stratiocicd
    user: anchore
    namespace: ${namespace}
  name: anchore@stratiocicd
current-context: anchore@stratiocicd
kind: Config
preferences: {}
users:
- name: anchore
  user:
    token: ${token} 
" > /.kube/config



#########################
### Anchore Analyzers ###
#########################
date
echo "Deleting pods idle for more than ${TIME}"

pods=$(kubectl -n keos-ci get --no-headers -o custom-columns=":metadata.name" pods | grep keos-anchore-anchore-engine-analyzer-)

for pod in ${pods}
do
    # echo $pod
    log=$(kubectl -n keos-ci logs $pod --since=${TIME} | grep -v health | grep -v metrics)

    if [ -z "$log" ]
    then
      # echo "Removing POD $pod"
	    kubectl -n keos-ci delete pod $pod
    else
        echo "Don't remove POD $pod"
    fi

done


exit 0
